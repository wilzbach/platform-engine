# -*- coding: utf-8 -*-
from aratrum import Aratrum


class Config(Aratrum):

    default = {
        'database': 'postgresql://postgres:postgres@localhost:5432/database',
        'broker': 'amqp://:@localhost:5672/'
    }
