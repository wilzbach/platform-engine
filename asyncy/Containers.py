# -*- coding: utf-8 -*-
import docker


class Containers:

    aliases = {
        'node': 'asyncy/asyncy-node',
        'python': 'asyncy/asyncy-python'
    }

    def __init__(self, name, logger):
        self.name = self.alias(name)
        self.client = docker.from_env()
        self.env = {}
        self.volume = None
        self.logger = logger

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
        self.logger.log('container-volume', name)

    def run(self, command, environment):
        """
        Runs a docker image.
        """
        self.client.images.pull(self.name)
        kwargs = {'command': command, 'environment': environment,
                  'cap_drop': 'all'}
        if self.volume:
            kwargs['volumes'] = {self.volume.name: {'bind': '/opt/v1',
                                                    'mode': 'rw'}}
        self.logger.log('container-start', self.name)
        self.output = self.client.containers.run(self.name, **kwargs)
        self.logger.log('container-end', self.name)

    def result(self):
        return self.output
