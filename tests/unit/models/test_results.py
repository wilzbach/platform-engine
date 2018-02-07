# -*- coding: utf-8 -*-
import time

from asyncy.models import Results

from bson import DBRef

import pymongo

from pytest import fixture


@fixture
def results():
    return Results('mongo_url')


@fixture
def mongo(mocker):
    mocker.patch.object(pymongo, 'MongoClient')
    return pymongo.MongoClient


def test_results(mongo, results):
    pymongo.MongoClient.assert_called_with('mongo_url')
    assert results.mongo == pymongo.MongoClient()


def test_results_save(mocker, mongo, results):
    mocker.patch.object(time, 'time', return_value=1)
    result = results.save('application', 'story', 'start', 'data')
    expected = {
        'application': 'application',
        'story': 'story',
        'data': 'data',
        'started': 'start',
        'finished': time.time()
    }
    mongo().asyncy.main.insert_one.assert_called_with(expected)
    assert result == mongo().asyncy.main.insert_one()


def test_results_ref(results):
    assert isinstance(results.ref('collection', 'id'), DBRef)


def test_results_story(mongo, results):
    result = results.story(1, 2)
    expected = {'application': 1, 'story': 2}
    mongo().asyncy.stories.insert_one.assert_called_with(expected)
    assert result == mongo().asyncy.stories.insert_one()


def test_results_narration(patch, mongo, results):
    patch.object(Results, 'ref')
    result = results.narration({'_id': 1}, {}, {'env': 1}, 'master', '1', '2')
    Results.ref.assert_called_with('stories', 1)
    expected = {
        'story_id': Results.ref(),
        'initial_data': {},
        'environment_data': {'env': 1},
        'version': 'master',
        'start': '1',
        'end': '2'
    }
    mongo().asyncy.narrations.insert_one.assert_called_with(expected)
    assert result == mongo().asyncy.narrations.insert_one()


def test_results_lines(patch, mongo, results):
    patch.object(Results, 'ref', return_value=100)
    lines = {'1': {'output': 'out', 'start': '1', 'end': '2'}}
    result = results.lines({'_id': 1}, lines)
    expected = {
        'narration_id': 100,
        'line': '1',
        'output': 'out',
        'start': '1',
        'end': '2'
    }
    Results.ref.assert_called_with('narrations', 1)
    mongo().asyncy.lines.insert_many.assert_called_with([expected])
    assert result == mongo().asyncy.lines.insert_many()
