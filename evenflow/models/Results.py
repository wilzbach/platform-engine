# -*- coding: utf-8 -*-
import pymongo


class Results:

    def __init__(self, data, application, story_name):
        self.data = data
        self.application = application
        self.story_name = story_name

    def save(self):
        client = pymongo.MongoClient()
        document = {
            'data': self.data,
            'application': self.application,
            'story': self.story_name
        }
        return client.asyncy.main.insert_one(document)
