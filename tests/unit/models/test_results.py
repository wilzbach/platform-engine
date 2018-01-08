# -*- coding: utf-8 -*-
from evenflow.models import Results

import pymongo

from pytest import fixture


@fixture
def results():
    return Results('data', 'application', 'storyname')


@fixture
def mongo(mocker):
    mocker.patch.object(pymongo, 'MongoClient')
    return pymongo.MongoClient


def test_results(results):
    assert results.data == 'data'
    assert results.application == 'application'
    assert results.story_name == 'storyname'


def test_results_save(mongo, results):
    result = results.save()
    expected = {
        'data': results.data,
        'application': results.application,
        'story': results.story_name
    }
    mongo().asyncy.main.insert_one.assert_called_with(expected)
    assert result == mongo().asyncy.main.insert_one()
