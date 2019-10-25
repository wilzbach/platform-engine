# -*- coding: utf-8 -*-
from unittest.mock import call

import pytest
from pytest import mark

from storyruntime.Exceptions import StoryscriptError
from storyruntime.entities.Multipart import FileFormField
from storyruntime.utils import Resolver
from storyruntime.utils.TypeUtils import TypeUtils

# Note: Actual resolution tests for resolution are in integration/Lexicon.


def test_expression_invalid_type(resolver):
    with pytest.raises(Exception):
        assert (
            resolver.expression({"expression": "a", "values": [b"asd"]}, {})
            == 1
        )


@mark.parametrize(
    "paths",
    [
        [
            "r",
            {"dot": "file", "$OBJECT": "dot"},
            {"string": "body", "$OBJECT": "string"},
        ],
        ["r", {"dot": "file", "$OBJECT": "dot"}, {"int": 3, "$OBJECT": "int"}],
        [
            "r",
            {"dot": "array", "$OBJECT": "dot"},
            {
                "range": {
                    "start": {"$OBJECT": "int", "int": 0},
                    "end": {"$OBJECT": "int", "int": 2},
                },
                "$OBJECT": "range",
            },
        ],
    ],
)
def test_path(patch, story, resolver, paths):
    patch.object(resolver, "object", side_effect=resolver.object)
    patch.object(TypeUtils, "isnamedtuple", side_effect=TypeUtils.isnamedtuple)
    patch.object(resolver, "range", side_effect=resolver.range)
    data = {
        "r": {
            "file": FileFormField(
                name="file",
                body=b"body",
                filename="file",
                content_type="content_type",
            ),
            "array": ["1", "2", "3"],
        }
    }
    story.set_context(data)
    resolved = resolver.path(paths)
    object_calls = []
    for path in paths[1:]:
        if path["$OBJECT"] == "range":
            object_calls.append(call(path["range"]["start"]))
            object_calls.append(call(path["range"]["end"]))
        else:
            object_calls.append(call(path))

    resolver.object.assert_has_calls(object_calls)

    nt_calls = [call(data["r"])]
    if paths[2]["$OBJECT"] == "string":
        nt_calls.append(call(data["r"][paths[1][paths[1]["$OBJECT"]]]))

        assert resolved == b"body"
    elif paths[2]["$OBJECT"] == "range":
        assert resolved == ["1", "2"]

    TypeUtils.isnamedtuple.assert_has_calls(nt_calls)


@mark.parametrize(
    "paths",
    [
        [
            "r",
            {"dot": "file", "$OBJECT": "dot"},
            {"string": "invalid", "$OBJECT": "string"},
        ],
        ["r", {"dot": "file", "$OBJECT": "dot"}, {"int": 5, "$OBJECT": "int"}],
        [
            "r",
            {"dot": "array", "$OBJECT": "dot"},
            {"int": 5, "$OBJECT": "int"},
        ],
    ],
)
def test_path_invalid_key(patch, story, resolver, paths):
    data = {
        "r": {
            "file": FileFormField(
                name="file",
                body=b"body",
                filename="file",
                content_type="content_type",
            ),
            "array": ["1", "2", "3"],
        }
    }
    story.set_context(data)
    with pytest.raises(StoryscriptError):
        resolver.path(paths)
