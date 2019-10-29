# -*- coding: utf-8 -*-
import hashlib
import re

import ujson

from .AppConfig import Forward
from .Exceptions import (
    ActionNotFound,
    ContainerSpecNotRegisteredError,
    EnvironmentVariableNotFound,
    K8sError,
)
from .Kubernetes import Kubernetes
from .Types import StreamingService
from .constants.LineConstants import LineConstants
from .constants.ServiceConstants import ServiceConstants
from .db.Database import Database
from .entities.ContainerConfig import ContainerConfig
from .entities.Volume import Volume
from .utils import Dict


class Containers:
    @classmethod
    async def remove_volume(cls, app, name):
        await Kubernetes.remove_volume(app, name)

    @classmethod
    async def prepare_for_deployment(cls, story):
        await Kubernetes.clean_namespace(story.app)

    @classmethod
    async def create_and_start(cls, app, line, service_name, container_name):
        """
        Creates and starts a container using the cloud provider (Kubernetes).
        :param app: The app instance
        :param line: Can be null, handled down the chain
        :param service_name: The name of the service
        :param container_name: The name of the container
        :return: null
        """
        # Note: 'uuid' and 'image' are inserted by asyncy.Apps,
        # and are not a part of the OMG spec.
        omg = app.services[service_name][ServiceConstants.config]
        image = omg.get("image", service_name)
        service_uuid = omg["uuid"]

        action = None
        if line is not None:
            action = line[LineConstants.command]

        command_conf = None
        if action is not None:
            command_conf = Dict.find(omg, f"actions.{action}")

            if command_conf is None:
                raise ActionNotFound(service=service_name, action=action)

        shutdown_command = Dict.find(omg, f"lifecycle.shutdown.command")

        if command_conf is not None and command_conf.get("run"):
            start_command = Dict.find(command_conf, "run.command")
        else:
            start_command = Dict.find(omg, f"lifecycle.startup.command")

        if start_command is None:
            start_command = ["tail", "-f", "/dev/null"]

        volumes = []
        if omg.get("volumes"):
            for name, data in omg["volumes"].items():
                vol_name = cls.hash_volume_name(app, line, service_name, name)
                persist = data.get("persist", False)
                target = data.get("target", False)

                volumes.append(
                    Volume(persist=persist, name=vol_name, mount_path=target)
                )

        registry_url = cls.get_registry_url(image)
        container_configs = list(
            map(
                lambda config: ContainerConfig(
                    name=cls.get_containerconfig_name(app, config.name),
                    data=config.data,
                ),
                await Database.get_container_configs(app, registry_url),
            )
        )

        env = {}
        for key, omg_config in omg.get("environment", {}).items():
            actual_val = app.environment.get(service_name, {}).get(key)
            if actual_val is None:
                actual_val = omg_config.get("default")
            if omg_config.get("required", False) and actual_val is None:
                raise EnvironmentVariableNotFound(
                    service=service_name, variable=key
                )

            if actual_val is not None:
                env[key] = actual_val

        await Kubernetes.create_pod(
            app=app,
            service_name=service_name,
            service_uuid=service_uuid,
            image=image,
            container_name=container_name,
            start_command=start_command,
            shutdown_command=shutdown_command,
            env=env,
            volumes=volumes,
            container_configs=container_configs,
        )

    @classmethod
    async def clean_app(cls, app):
        await Kubernetes.clean_namespace(app)

    @classmethod
    async def init(cls, app):
        await Kubernetes.create_namespace(app)

    @classmethod
    def get_hostname(cls, story, line, service_alias):
        container = cls.get_container_name(
            story.app, story.name, line, service_alias
        )
        return Kubernetes.get_hostname(story.app, container)

    @classmethod
    def get_registry_url(cls, image):
        official = ["docker.io", "index.docker.io"]
        i = image.find("/")
        if (
            i == -1
            or (
                not any(c in image[:i] for c in ".:")
                and image[:i] != "localhost"
            )
            or image[:i] in official
        ):
            return "https://index.docker.io/v1/"
        else:
            return image[:i]

    @classmethod
    async def expose_service(cls, app, expose: Forward):
        container_name = cls.get_container_name(
            app, None, None, expose.service
        )
        await cls.create_and_start(app, None, expose.service, container_name)
        ingress_name = cls.hash_ingress_name(expose)
        hostname = f"{app.app_dns}--{cls.get_simple_name(expose.service)}"
        await Kubernetes.create_ingress(
            ingress_name, app, expose, container_name, hostname=hostname
        )

        app.logger.info(
            f"Exposed service {expose.service} as "
            f"https://{hostname}.{app.config.APP_DOMAIN}"
            f"{expose.http_path}"
        )

    @classmethod
    def get(cls, story, line) -> StreamingService:
        service = line[LineConstants.service]
        hostname = cls.get_hostname(story, line, service)
        container_name = cls.get_container_name(
            story.app, story.name, line, service
        )

        return StreamingService(
            name=service,
            command=line["command"],
            container_name=container_name,
            hostname=hostname,
        )

    @classmethod
    async def start(cls, story, line):
        """
        Creates and starts a container as declared by line['service'].

        If a container already exists, then it will be reused.
        """
        service = line[LineConstants.service]
        story.logger.debug(f"Starting container {service}")
        container_name = cls.get_container_name(
            story.app, story.name, line, service
        )
        await cls.create_and_start(story.app, line, service, container_name)

        ss = cls.get(story, line)

        story.logger.debug(f"Started container {container_name}")
        return ss

    @classmethod
    def format_command(cls, story, line, container_name, command):
        services = story.app.services or {}
        spec = services.get(container_name)

        if spec is None:
            raise ContainerSpecNotRegisteredError(
                container_name=container_name, story=story, line=line
            )

        args = spec[ServiceConstants.config]["actions"][command].get(
            "arguments"
        )

        if args is None:
            return [command]

        command_format = spec[ServiceConstants.config]["actions"][command].get(
            "format"
        )
        if command_format is None:
            # Construct a dictionary of all arguments required and send them
            # as a JSON string to the command.
            all_args = {}
            for k in args:
                all_args[k] = story.argument_by_name(line, k)

            return [command, ujson.dumps(all_args)]

        command_parts = command_format.split(" ")

        for k in args:
            actual = story.argument_by_name(line, k)
            for i in range(0, len(command_parts)):
                command_parts[i] = command_parts[i].replace(
                    "{" + k + "}", actual
                )

        return command_parts

    @classmethod
    def get_containerconfig_name(cls, app, name):
        simple_name = cls.get_simple_name(name)[:20]
        h = cls.hash_containerconfig_name(app, name)
        return f"{simple_name}-{h}"

    @classmethod
    def get_container_name(cls, app, story_name, line, name):
        """
        Returns a generic name like twitter-hash(twitter).

        Why a hash? Story names can have DNS reserved characters in them,
        and hence to normalise it, we need to create a hash here.
        """
        # simple_name is included in the container name to aid debugging only.
        # It's 20 chars at max because 41 chars consists
        # of the hash and a hyphen. K8s names must be < 63 chars.
        simple_name = cls.get_simple_name(name)[:20]
        h = cls.hash_service_name(app, name)

        return f"{simple_name}-{h}"

    @classmethod
    def get_simple_name(cls, string):
        parts = re.findall("[a-zA-Z]*", string)
        out = ""
        for i in parts:
            if i != "":
                out += i

        return out.lower()

    @classmethod
    def hash_service_name(cls, app, name):
        return hashlib.sha1(
            f"{name}-{app.version}".encode("utf-8")
        ).hexdigest()

    @classmethod
    def hash_ingress_name(cls, expose: Forward):
        simple_name = cls.get_simple_name(expose.service_forward_name)[:20]
        h = hashlib.sha1(
            f"{expose.service}-{expose.service_forward_name}".encode("utf-8")
        ).hexdigest()
        return f"{simple_name}-{h}"

    @classmethod
    def hash_volume_name(cls, app, line, service, volume_name):
        key = f"{volume_name}-{service}"

        simple_name = cls.get_simple_name(volume_name)[:20]
        h = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return f"{simple_name}-{h}"

    @classmethod
    def hash_containerconfig_name(cls, app, name):
        return hashlib.sha1(
            f"{app.version}-{name}".encode("utf-8")
        ).hexdigest()

    @classmethod
    async def exec(cls, logger, story, line, container_name, command):
        """
        Executes a command in the given container.

        Returns:
        Output of the process (stdout).

        Raises:
        asyncy.Exceptions.K8sError:
            If the execution failed for an unknown reason.
        """
        raise K8sError(story=story, line=line, message="Not implemented")
