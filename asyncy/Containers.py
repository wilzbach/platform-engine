# -*- coding: utf-8 -*-
import docker


class Containers:

    aliases = {
        'node': 'asyncy/asyncy-node',
        'python': 'asyncy/asyncy-python'
    }

    def __init__(self, name):
        self.name = self.alias(name)
        self.client = docker.from_env()
        self.env = {}
        self.volume = None

    def alias(self, name):
        """
        Converts a container alias to its real name.
        """
        if name in self.aliases:
            return self.aliases[name]
        return name

    def make_volume(self, name):
        try:
            self.volume = self.client.volumes.get(name)
        except docker.errors.NotFound:
            self.volume = self.client.volumes.create(name)

    def environment(self, story, application):
        """
        Sets the environment from story and application.
        """
        self.env = story.environment()
        application_environment = application.environment()
        for key, value in self.env.items():
            if key in application_environment:
                self.env[key] = application_environment[key]

    def run(self, logger, command):
        """
        Runs a docker image.
        """
        self.client.images.pull(self.name)
        kwargs = {'command': command, 'environment': self.env,
                  'cap_drop': 'all'}
        if self.volume:
            kwargs['volumes'] = {self.volume.name: {'bind': '/opt/v1',
                                                    'mode': 'rw'}}
        self.output = self.client.containers.run(self.name, **kwargs)
        logger.log('container-run', self.name)

    def result(self):
        return self.output
