# -*- coding: utf-8 -*-
from prometheus_client import Summary


story_request = Summary(
    'asyncy_engine_http_run_story_processing_seconds',
    'Time spent processing story run requests',
    ['app_id', 'story_name']
)

story_run_success = Summary(
    'asyncy_engine_success_seconds',
    'Time spent executing a story (successfully)',
    ['app_id', 'story_name']
)

story_run_failure = Summary(
    'asyncy_engine_failure_seconds',
    'Time spent executing a story (failed)',
    ['app_id', 'story_name']
)

story_run_total = Summary(
    'asyncy_engine_total_seconds',
    'Time spent executing a story (total)',
    ['app_id', 'story_name']
)

container_exec_seconds_total = Summary(
    'asyncy_engine_container_exec_seconds',
    'Time spent executing commands in containers',
    ['app_id', 'story_name', 'service']
)

container_start_seconds_total = Summary(
    'asyncy_engine_container_start_seconds',
    'Time spent executing commands in containers',
    ['app_id', 'story_name', 'service']
)
