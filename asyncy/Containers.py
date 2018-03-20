# -*- coding: utf-8 -*-
import docker


class Containers:

    def __init__(self, logger, containers, name):
        self.containers = containers
        self.name = self.alias(name)
        self.client = docker.from_env()
        self.env = {}
        self.volume = None
        self.logger = logger

    def alias(self, name):
        """
        Converts a container alias to its real pull location
        """
        if name in self.containers:
            return self.containers[name]['pull_url']
        return name

    def image(self, name):
        """
        Pull an image if it does not exist locally
        """
        try:
            self.client.images.get(name)
        except docker.errors.ImageNotFound:
            self.client.images.pull(name)

    def make_volume(self, name):
        try:
            self.volume = self.client.volumes.get(name)
        except docker.errors.NotFound:
            self.volume = self.client.volumes.create(name)
        self.logger.log('container-volume', name)

    def summon(self, command, environment):
        """
        Summons the docker container to do his job.
        """
        self.image(self.name)
        kwargs = {'command': command, 'environment': environment,
                  'cap_drop': 'all', 'auto_remove': True}
        if self.volume:
            kwargs['volumes'] = {self.volume.name: {'bind': '/opt/v1',
                                                    'mode': 'rw'}}
        self.logger.log('container-start', self.name)
        self.output = self.client.containers.run(self.name, **kwargs)
        self.logger.log('container-end', self.name)

    def result(self):
        return self.output

    @staticmethod
    def run(logger, story, name, command):
        container = Containers(logger, story.containers, name)
        container.make_volume(story.name)
        container.summon(command, story.environment)
        return container.result()
