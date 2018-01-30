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

    def environment(self, application, story):
        """
        Sets the environment from application and story.
        """
        self.env = application.environment()
        story_environment = story.environment()
        for key, value in story_environment.items():
            self.env[key] = value

    def run(self, logger, *args):
        """
        Runs a docker image.
        """
        self.client.images.pull(self.name)
        kwargs = {'command': (), 'environment': self.env}
        self.output = self.client.containers.run(self.name, **kwargs)
        logger.log('container-run', self.name)

    def result(self):
        return self.output
