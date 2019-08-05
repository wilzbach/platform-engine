from collections import namedtuple

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
