# -*- coding: utf-8 -*-
from storyruntime.AppConfig import AppConfig


def test_app_config():
    expose = [
        {
            'service': 'service_0',
            'name': 'expose_name_0',
            'http': {
                'path': '/my_expose_path_0'
            }
        },
        {
            'service': 'service_1',
            'name': 'expose_name_1',
            'http': {
                'path': '/my_expose_path_1'
            }
        }
    ]
    config = AppConfig({'expose': expose})
    exposes = config.get_expose_config()

    assert len(exposes) == 2

    for i in range(0, 2):
        assert exposes[i].service == f'service_{i}'
        assert exposes[i].http_path == f'/my_expose_path_{i}'
        assert exposes[i].service_expose_name == f'expose_name_{i}'
