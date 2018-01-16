# -*- coding: utf-8 -*-
import docker


class Containers:

    def __init__(self, name):
        self.name = name

    def run(self, *args):
        client = docker.from_env()
        client.images.pull(self.name)
        self.output = client.containers.run(self.name, command=args)

    def result(self):
        return self.output
