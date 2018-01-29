# -*- coding: utf-8 -*-
import docker


class Containers:

    aliases = {
        'node': 'asyncy/asyncy-node',
        'python': 'asyncy/asyncy-python'
    }

    def __init__(self, name):
        self.name = name

    def alias(self, name):
        if name in self.aliases:
            return self.aliases[name]
        return name

    def run(self, logger, *args):
        client = docker.from_env()
        client.images.pull(self.name)
        self.output = client.containers.run(self.name, command=())
        logger.log('container-run', self.name)

    def result(self):
        return self.output
