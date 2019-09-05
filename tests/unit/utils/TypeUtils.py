from collections import namedtuple

from storyruntime.Types import InternalCommand, InternalService, \
    SafeInternalCommand, SafeStreamingService, StreamingService
from storyruntime.utils.TypeUtils import TypeUtils


def test_isnamedtuple():
    namedtuple_obj = namedtuple(
        'NamedTupleObj',
        ['key']
    )

    assert TypeUtils.isnamedtuple(namedtuple_obj(
        key='key'
    ))
    assert not TypeUtils.isnamedtuple(namedtuple_obj)
    assert not TypeUtils.isnamedtuple(('a', 'b', 'c'))
    assert not TypeUtils.isnamedtuple({})
    assert not TypeUtils.isnamedtuple(1)
    assert not TypeUtils.isnamedtuple('a')
    assert not TypeUtils.isnamedtuple(False)


def test_safe_type_none():
    assert TypeUtils.safe_type(None) is None


def test_safe_type_streaming_service():
    assert isinstance(
        TypeUtils.safe_type(
            StreamingService(
                name='name',
                command='command',
                container_name='container_name',
                hostname='hostname'
            )
        ),
        SafeStreamingService
    )


def test_safe_type_internal_service(magic):
    service = InternalService(commands={
        'command': InternalCommand(
            arguments=[],
            output_type='output_type',
            handler=magic()
        )
    })
    safe_type = TypeUtils.safe_type(service)

    assert isinstance(safe_type, InternalService)
    assert 'command' in safe_type.commands
    assert isinstance(
        safe_type.commands['command'],
        SafeInternalCommand
    )


def test_safe_type_internal_command(magic):
    command = InternalCommand(
        arguments=[],
        output_type='output_type',
        handler=magic()
    )
    safe_type = TypeUtils.safe_type(command)

    assert isinstance(safe_type, SafeInternalCommand)
