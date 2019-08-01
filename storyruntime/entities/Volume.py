# -*- coding: utf-8 -*-
import typing

Volume = typing.NamedTuple('Volume', [
    ('persist', bool),
    ('name', str),
    ('mount_path', str)
])

Volumes = typing.List[Volume]
