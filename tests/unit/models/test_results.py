# -*- coding: utf-8 -*-
import time

from asyncy.models import Results

import pymongo

from bson import DBRef

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
