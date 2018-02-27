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

    def run(self, logger, command, environment):
        """
        Runs a docker image.
        """
        self.client.images.pull(self.name)
        kwargs = {'command': command, 'environment': environment,
                  'cap_drop': 'all'}
        if self.volume:
            kwargs['volumes'] = {self.volume.name: {'bind': '/opt/v1',
                                                    'mode': 'rw'}}
        logger.log('container-start', self.name)
        self.output = self.client.containers.run(self.name, **kwargs)
        logger.log('container-end', self.name)

    def result(self):
        return self.output
