# -*- coding: utf-8 -*-
import pymongo


class Results:

    def __init__(self, mongo_url):
        self.mongo = pymongo.MongoClient(mongo_url)

    def save(self, application, story_name, data):
        document = {
            'data': data,
            'application': application,
            'story': story_name
        }
        return self.mongo.asyncy.main.insert_one(document)
