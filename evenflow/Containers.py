# -*- coding: utf-8 -*-
import docker


class Containers:

    def __init__(self, name):
        self.name = name

    def run(self):
        docker.from_env().containers.run()
