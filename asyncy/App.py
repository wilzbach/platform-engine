# -*- coding: utf-8 -*-
import os
from json import load


class App:

    environment = {}
    stories = {}
    services = {}

    def __init__(self):
        self.apply()

    def load_file(self, filepath):
        datapath = os.getenv('ASSET_DIR', os.getcwd())
        path = os.path.join(datapath, filepath)
        if os.path.exists(path):
            with open(path, 'r') as file:
                return load(file)

    def apply(self):
        """
        Build environment, stories, and services from start of service.
        """
        self.environment = self.load_file('environment.json')
        self.stories = self.load_file('stories.json')
        self.services = self.load_file('services.json')
