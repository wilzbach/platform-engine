# -*- coding: utf-8 -*-
import enum


@enum.unique
class ReleaseState(enum.Enum):
    QUEUED = 'QUEUED'
    DEPLOYING = 'DEPLOYING'
    DEPLOYED = 'DEPLOYED'
    TERMINATING = 'TERMINATING'
    TERMINATED = 'TERMINATED'
    NO_DEPLOY = 'NO_DEPLOY'
    FAILED = 'FAILED'
    SKIPPED_CONCURRENT = 'SKIPPED_CONCURRENT'
