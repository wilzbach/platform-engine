# -*- coding: utf-8 -*-
import pytest

from storyruntime.Exceptions import StoryscriptError
from storyruntime.processing.Mutations import Mutations
from storyruntime.processing.mutations.StringMutations import StringMutations


# Note: All mutations are tested via integration
# in Lexicon.py under integration tests.


def test_mutations_unexpected_type(story):
    mutation = {
        'mutation': 'foo'
    }

    with pytest.raises(StoryscriptError):
        Mutations.mutate(mutation, Mutations, story, None)


def test_mutations_unexpected_mutation(story):
    mutation = {
        'mutation': 'foo'
    }

    with pytest.raises(StoryscriptError):
        Mutations.mutate(mutation, 'string', story, None)


def test_mutations_handler_exception(story, patch):
    def exc(*args):
        raise Exception()

    patch.object(StringMutations, 'replace', side_effect=exc)
    mutation = {
        'mutation': 'replace'
    }

    with pytest.raises(StoryscriptError):
        Mutations.mutate(mutation, 'string', story, None)
