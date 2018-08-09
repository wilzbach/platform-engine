# -*- coding: utf-8 -*-
from collections import namedtuple

StreamingService = namedtuple('StreamingService',
                              ['name', 'command',
                               'container_name', 'hostname'])

StreamingEvent = namedtuple('StreamingEvent',
                            ['service', 'output_name'])
