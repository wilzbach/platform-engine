# -*- coding: utf-8 -*-
from collections import namedtuple

FormField = namedtuple('FormField', ['name', 'body'])
FileFormField = namedtuple('FileFormField',
                           ['name', 'body', 'filename', 'content_type'])
