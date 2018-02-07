# -*- coding: utf-8 -*-


class Document:
    def __init__(self, mongo, collection, **kwargs):
        self.mongo = mongo
        self.collection = collection
        for key, value in kwargs.items():
            setattr(self, key, value)

    def data(self):
        """
        Shows document data as dictionary.
        """
        data = dict(self.__dict__)
        del data['mongo']
        del data['collection']
        return data

    def save(self):
        return self.mongo.asyncy.collection.insert_one(self.data())
