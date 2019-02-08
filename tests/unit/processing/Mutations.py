# -*- coding: utf-8 -*-
from asyncy.Exceptions import AsyncyError
from asyncy.processing.Mutations import Mutations
from asyncy.processing.mutations.StringMutations import StringMutations

import pytest


# Note: All mutations are tested via integration
# in Lexicon.py under integration tests.


def test_mutations_unexpected_type(story):
    mutation = {
        'mutation': 'foo'
    }

    with pytest.raises(AsyncyError):
        Mutations.mutate(mutation, Mutations, story, None)


def test_mutations_unexpected_mutation(story):
    mutation = {
        'mutation': 'foo'
    }

    with pytest.raises(AsyncyError):
        Mutations.mutate(mutation, 'string', story, None)


def test_mutations_handler_exception(story, patch):
    def exc():
        raise Exception()

    patch.object(StringMutations, 'replace', side_effect=exc)
    mutation = {
        'mutation': 'replace'
    }

    with pytest.raises(AsyncyError):
        Mutations.mutate(mutation, 'string', story, None)
