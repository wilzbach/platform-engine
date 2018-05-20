# -*- coding: utf-8 -*-
import docker

from .Exceptions import DockerContainerNotFoundError, DockerError

MAX_RETRIES = 3


class Containers:
    # Caches the container name (key) to the Container instance from docker.
    container_cache = {}

    client = docker.from_env()

    @classmethod
    def exec(cls, logger, story, name, command):
        """
        Executes a command in the given container.

        Returns:
        Output of the process.

        Raises:
        asyncy.Exceptions.DockerContainerNotFoundError:
            When the container is not found.
        asyncy.Exceptions.DockerError:
            If the execution failed for an unknown reason.
        """
        logger.log('container-start', name)
        environment = story.environment
        tries = 0
        while tries < MAX_RETRIES:
            tries = tries + 1
            container = Containers.container_cache.get(name)
            try:
                if container is None:
                    container = cls.client.containers.get(container_id=name)
                    if container is None:
                        raise DockerContainerNotFoundError(
                            'Container not found')
                    Containers.container_cache[name] = container

                result = container.exec_run(command, environment=environment)
                logger.log('container-end', name)
                return result[1]  # container.exec_run returns a tuple.
            except docker.errors.DockerException:
                logger.log_raw('error',
                               'Error finding container, trying again.')
                # Remove the container from container_cache.
                Containers.container_cache[name] = None

        logger.log_raw('error',
                       'Execution failed after all retries.')
        raise DockerError('Execution failed')
