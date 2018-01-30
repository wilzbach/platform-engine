# -*- coding: utf-8 -*-
import os

from yaml import Loader, load


class Yaml:

    @staticmethod
    def string(string):
        return load(string, Loader=Loader)

    @staticmethod
    def path(path):
        if os.path.isfile(path):
            with open(path, 'r') as f:
                return Yaml.string(f.read())
