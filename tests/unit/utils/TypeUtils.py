from collections import namedtuple

import pytest
from requests.structures import CaseInsensitiveDict

from storyruntime.Exceptions import StoryscriptRuntimeError
from storyruntime.Types import (
    InternalCommand,
    InternalService,
    SafeInternalCommand,
    SafeStreamingService,
    StreamingService,
)
from storyruntime.utils.TypeUtils import TypeUtils


def test_isnamedtuple():
    namedtuple_obj = namedtuple("NamedTupleObj", ["key"])

    assert TypeUtils.isnamedtuple(namedtuple_obj(key="key"))
    assert not TypeUtils.isnamedtuple(namedtuple_obj)
    assert not TypeUtils.isnamedtuple(("a", "b", "c"))
    assert not TypeUtils.isnamedtuple({})
    assert not TypeUtils.isnamedtuple(1)
    assert not TypeUtils.isnamedtuple("a")
    assert not TypeUtils.isnamedtuple(False)


def test_safe_type():
    assert TypeUtils.safe_type(None) is None
    assert TypeUtils.safe_type(1) is 1
    assert TypeUtils.safe_type(1.5) is 1.5
    assert TypeUtils.safe_type(True) is True
    assert TypeUtils.safe_type(False) is False
    assert TypeUtils.safe_type("1234") is "1234"
    assert TypeUtils.safe_type(b"1234") is b"1234"


def test_safe_type_exc(story):
    with pytest.raises(StoryscriptRuntimeError):
        TypeUtils.safe_type(story)


def test_safe_type_streaming_service():
    assert isinstance(
        TypeUtils.safe_type(
            StreamingService(
                name="name",
                command="command",
                container_name="container_name",
                hostname="hostname",
            )
        ),
        SafeStreamingService,
    )


def test_safe_type_internal_service(magic):
    service = InternalService(
        commands={
            "command": InternalCommand(
                arguments=[], output_type="output_type", handler=magic()
            )
        }
    )
    safe_type = TypeUtils.safe_type(service)

    assert isinstance(safe_type, InternalService)
    assert "command" in safe_type.commands
    assert isinstance(safe_type.commands["command"], SafeInternalCommand)


def test_safe_type_internal_command(magic):
    command = InternalCommand(
        arguments=[], output_type="output_type", handler=magic()
    )
    safe_type = TypeUtils.safe_type(command)

    assert isinstance(safe_type, SafeInternalCommand)


def test_safe_type_list():
    expected = [
        "hello",
        1234,
        {"hello": "world", "WORLD": "hello"},
        {"hello": "world", "WORLD": "hello"},
    ]

    assert expected == TypeUtils.safe_type(
        [
            "hello",
            1234,
            {"hello": "world", "WORLD": "hello"},
            CaseInsensitiveDict({"hello": "world", "WORLD": "hello"}),
        ]
    )


def test_safe_type_dict():
    expected = {"hello": "world", "WORLD": "hello"}

    assert expected == TypeUtils.safe_type(expected)


def test_safe_type_caseinsensitivedict():
    expected = {
        "hello": "world",
        "WORLD": "hello",
        "else": {"hello": "world", "WORLD": "hello"},
    }

    assert expected == TypeUtils.safe_type(
        {
            "hello": "world",
            "WORLD": "hello",
            "else": CaseInsensitiveDict(expected["else"]),
        }
    )
