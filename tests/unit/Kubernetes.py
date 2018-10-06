# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from asyncy.Exceptions import K8sError
from asyncy.Kubernetes import Kubernetes

import pytest
from pytest import fixture


@fixture
def line():
    return MagicMock()


def test_find_all_ports():
    services = {
        'alpine': {
            'http': {
                'port': 8080
            }
        },
        'alpha': {
            'http': {
                'port': 9092,
                'subscribe': {
                    'port': 9090
                },
                'unsubscribe': {
                    'port': 9091
                }
            }
        },
        'nested': {
            'a': {
                'b': {
                    'c': {
                        'd': {
                            'e': {
                                'http': {
                                    'subscribe': {
                                        'port': 1234
                                    },
                                    'unsubscribe': {
                                        'port': 1235
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    assert Kubernetes.find_all_ports(services['alpine']) == {8080}
    assert Kubernetes.find_all_ports(services['alpha']) == {9090, 9091, 9092}
    assert Kubernetes.find_all_ports(services['nested']) == {1234, 1235}


def test_raise_if_not_2xx(story, line):
    res = MagicMock()
    res.code = 401
    with pytest.raises(K8sError):
        Kubernetes.raise_if_not_2xx(res, story, line)

    res.code = 200
    assert Kubernetes.raise_if_not_2xx(res, story, line) is None


def test_is_2xx():
    res = MagicMock()
    res.code = 200
    assert Kubernetes.is_2xx(res) is True
    res.code = 210
    assert Kubernetes.is_2xx(res) is True
    res.code = 300
    assert Kubernetes.is_2xx(res) is False
    res.code = 400
    assert Kubernetes.is_2xx(res) is False
