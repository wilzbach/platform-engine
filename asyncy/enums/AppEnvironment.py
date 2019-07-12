# -*- coding: utf-8 -*-
import enum


@enum.unique
class AppEnvironment(enum.Enum):
    PRODUCTION = 'PRODUCTION'
    STAGING = 'STAGING'
    DEV = 'DEV'  # Not used anywhere in the engine right now.
