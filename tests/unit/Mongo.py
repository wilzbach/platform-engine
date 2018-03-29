# -*- coding: utf-8 -*-
import time

from asyncy.Mongo import Mongo

from bson import DBRef
from bson.errors import InvalidDocument

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
    client().asyncy.stories.find_one.assert_called_with(expected)
    assert result == client().asyncy.stories.find_one()


def test_results_story_new(client, mongo):
    mongo.mongo.asyncy.stories.find_one.return_value = None
    result = mongo.story(1, 2)
    query = {'application': 1, 'story': 2}
    client().asyncy.stories.insert_one.assert_called_with(query)
    assert result == client().asyncy.stories.insert_one()


def test_results_narration(patch, story, client, mongo):
    patch.object(Mongo, 'ref')
    story.environment = 'environment'
    result = mongo.narration(1, story, 'master', '1', '2')
    Mongo.ref.assert_called_with('stories', 1)
    expected = {
        'story_id': Mongo.ref(),
        'environment_data': story.environment,
        'version': 'master',
        'start': '1',
        'end': '2'
    }
    client().asyncy.narrations.insert_one.assert_called_with(expected)
    assert result == client().asyncy.narrations.insert_one()


def test_results_narration_invalid(patch, story, client, mongo):
    patch.object(Mongo, 'ref')
    client().asyncy.narrations.insert_one.side_effect = InvalidDocument
    story.environment = 'environment'
    assert mongo.narration(1, story, 'master', '1', '2') is None


def test_results_lines(patch, magic, client, mongo):
    patch.object(Mongo, 'ref', return_value=100)
    lines = {'1': {'output': 'out', 'start': '1', 'end': '2'}}
    result = mongo.lines(magic(inserted_id=1), lines)
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


def test_results_lines_no_output(patch, magic, client, mongo):
    patch.object(Mongo, 'ref', return_value=100)
    lines = {'1': {'start': '1', 'end': '2'}}
    mongo.lines(magic(inserted_id=1), lines)
    expected = {
        'narration_id': 100,
        'line': '1',
        'start': '1',
        'end': '2'
    }
    client().asyncy.lines.insert_many.assert_called_with([expected])


def test_results_lines_no_end(patch, magic, client, mongo):
    patch.object(Mongo, 'ref', return_value=100)
    lines = {'1': {'output': 'out', 'start': '1'}}
    result = mongo.lines(magic(inserted_id=1), lines)
    expected = {
        'narration_id': 100,
        'line': '1',
        'output': 'out',
        'start': '1'
    }
    Mongo.ref.assert_called_with('narrations', 1)
    client().asyncy.lines.insert_many.assert_called_with([expected])
    assert result == client().asyncy.lines.insert_many()
