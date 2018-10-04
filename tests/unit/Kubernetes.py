# -*- coding: utf-8 -*-
from asyncy.Kubernetes import Kubernetes


def test_find_all_ports():
    services = {
        'alpine': {
            'http': {
                'port': 8080
            }
        },
        'alpha': {
            'http': {
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
    assert Kubernetes.find_all_ports(services['alpha']) == {9090, 9091}
    assert Kubernetes.find_all_ports(services['nested']) == {1234, 1235}
