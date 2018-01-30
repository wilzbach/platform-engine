# -*- coding: utf-8 -*-
import os

from yaml import Loader, load


class Yaml:

    @staticmethod
    def path(path):
        if os.path.isfile(path):
            with open(path, 'r') as f:
                return load(f.read(), Loader=Loader)
