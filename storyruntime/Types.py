# -*- coding: utf-8 -*-
from collections import namedtuple

StreamingService = namedtuple('StreamingService',
                              ['name', 'command',
                               'container_name', 'hostname'])

SafeStreamingService = namedtuple('StreamingService',
                                  ['name', 'command'])

InternalCommand = namedtuple('InternalCommand',
                             ['arguments', 'output_type', 'handler'])

SafeInternalCommand = namedtuple('InternalCommand',
                                 ['arguments', 'output_type'])

InternalService = namedtuple('InternalService', ['commands'])

Service = namedtuple('Service', ['name'])
Command = namedtuple('Command', ['name'])
Event = namedtuple('Event', ['name'])
