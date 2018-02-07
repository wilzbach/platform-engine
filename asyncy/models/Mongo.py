# -*- coding: utf-8 -*-
import time

from bson import DBRef

import pymongo


class Mongo:

    def __init__(self, mongo_url):
        self.mongo = pymongo.MongoClient(mongo_url)

    def ref(self, collection, item_id):
        """
        Returns a reference object.
        """
        return DBRef(collection, item_id)

    def story(self, application_id, story_id):
        document = {
            'application': application_id,
            'story': story_id
        }
        return self.mongo.asyncy.stories.insert_one(document)

    def narration(self, story, initial_data, environment_data, version,
                  start, end):
        document = {
            'story_id': self.ref('stories', story['_id']),
            'initial_data': initial_data,
            'environment_data': environment_data,
            'version': version,
            'start': start,
            'end': end
        }
        return self.mongo.asyncy.narrations.insert_one(document)

    def lines(self, narration, lines):
        narration_ref = self.ref('narrations', narration['_id'])
        documents = []
        for line, data in lines.items():
            document = {
                'narration_id': narration_ref,
                'line': line,
                'output': data['output'],
                'start': data['start'],
                'end': data['end']
            }
            documents.append(document)
        return self.mongo.asyncy.lines.insert_many(documents)
