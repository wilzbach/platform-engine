# -*- coding: utf-8 -*-
import time

from asyncy.models import Mongo

from bson import DBRef

import pymongo

from pytest import fixture


@fixture
def client(patch):
    patch.object(pymongo, 'MongoClient')
    return pymongo.MongoClient


@fixture
def mongo(client):
    return Mongo('mongo_url')


def test_results(mongo):
    pymongo.MongoClient.assert_called_with('mongo_url')
    assert mongo.mongo == pymongo.MongoClient()


def test_results_ref(mongo):
    assert isinstance(mongo.ref('collection', 'id'), DBRef)


def test_results_story(client, mongo):
    result = mongo.story(1, 2)
    expected = {'application': 1, 'story': 2}
    client().asyncy.stories.insert_one.assert_called_with(expected)
    assert result == client().asyncy.stories.insert_one()


def test_results_narration(patch, client, mongo):
    patch.object(Mongo, 'ref')
    result = mongo.narration({'_id': 1}, {}, {'env': 1}, 'master', '1', '2')
    Mongo.ref.assert_called_with('stories', 1)
    expected = {
        'story_id': Mongo.ref(),
        'initial_data': {},
        'environment_data': {'env': 1},
        'version': 'master',
        'start': '1',
        'end': '2'
    }
    client().asyncy.narrations.insert_one.assert_called_with(expected)
    assert result == client().asyncy.narrations.insert_one()


def test_results_lines(patch, client, mongo):
    patch.object(Mongo, 'ref', return_value=100)
    lines = {'1': {'output': 'out', 'start': '1', 'end': '2'}}
    result = mongo.lines({'_id': 1}, lines)
    expected = {
        'narration_id': 100,
        'line': '1',
        'output': 'out',
        'start': '1',
        'end': '2'
    }
    Mongo.ref.assert_called_with('narrations', 1)
    client().asyncy.lines.insert_many.assert_called_with([expected])
    assert result == client().asyncy.lines.insert_many()
