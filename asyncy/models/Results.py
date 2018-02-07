# -*- coding: utf-8 -*-
import time

import pymongo


class Results:

    def __init__(self, mongo_url):
        self.mongo = pymongo.MongoClient(mongo_url)

    def save(self, application, story_name, start_time, data):
        document = {
            'data': data,
            'application': application,
            'story': story_name,
            'started': start_time,
            'finished': time.time()
        }
        return self.mongo.asyncy.main.insert_one(document)

    def story(self, application_id, story_id):
        document = {
            'application': application_id,
            'story': story_id
        }
        return self.mongo.asyncy.stories.insert_one(document)
