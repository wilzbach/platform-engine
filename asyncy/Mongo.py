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
        """
        Finds a story document with the given application and story id;
        otherwise creates it.
        """
        document = {'application': application_id, 'story': story_id}
        story = self.mongo.asyncy.stories.find_one(document)
        if story:
            return story
        return self.mongo.asyncy.stories.insert_one(document)

    def narration(self, mongo_story_id, story, version, start, end):
        """
        Saves the single run of a story and helpful data like environment and
        containers.
        """
        document = {
            'story_id': self.ref('stories', mongo_story_id),
            'environment_data': story.environment,
            'version': version,
            'start': start,
            'end': end
        }
        return self.mongo.asyncy.narrations.insert_one(document)

    def lines(self, narration, lines):
        narration_ref = self.ref('narrations', narration.inserted_id)
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
