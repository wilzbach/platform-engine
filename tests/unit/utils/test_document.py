# -*- coding: utf-8 -*-
from asyncy.utils import Document

from pytest import fixture


@fixture
def mongo(magic):
    return magic()


@fixture
def document(mongo):
    return Document(mongo, 'collection', name='doc', length=100)


def test_document(mongo, document):
    assert document.mongo == mongo
    assert document.collection == 'collection'
    assert document.name == 'doc'
    assert document.length == 100


def test_document_data(mongo, document):
    assert document.data() == {'name': 'doc', 'length': 100}
    assert document.mongo == mongo
    assert document.collection == 'collection'


def test_document_save(patch, mongo, document):
    patch.object(Document, 'data')
    result = document.save()
    mongo.asyncy.collection.insert_one.assert_called_with(document.data())
    assert result == mongo.asyncy.collection.insert_one()
