# -*- coding: utf-8 -*-
import docker


class Containers:

    aliases = {
        'node': 'asyncy/asyncy-node',
        'python': 'asyncy/asyncy-python'
    }

    def __init__(self, name):
        self.name = self.alias(name)
        self.env = {}

    def alias(self, name):
        if name in self.aliases:
            return self.aliases[name]
        return name

    def environment(self, application, story):
        self.env = application.environment()
        story_environment = story.environment()
        for key, value in story_environment.items():
            self.env[key] = value

    def run(self, logger, *args):
        client = docker.from_env()
        client.images.pull(self.name)
        kwargs = {'command': (), 'environment': self.env}
        self.output = client.containers.run(self.name, **kwargs)
        logger.log('container-run', self.name)

    def result(self):
        return self.output
