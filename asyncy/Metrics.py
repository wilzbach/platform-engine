# -*- coding: utf-8 -*-
from prometheus_client import Summary

story_request = Summary(
    'asyncy_engine_http_run_story_processing_seconds',
    'Time spent processing story run requests'
)

http_register = Summary(
    'asyncy_engine_http_endpoint_register_seconds',
    'Time spent registering a story with the gateway'
)

http_unregister = Summary(
    'asyncy_engine_http_endpoint_unregister_seconds',
    'Time spent unregistering a story with the gateway'
)

story_run_success = Summary(
    'asyncy_engine_success_seconds',
    'Time spent executing a story (successfully)',
    ['story_name']
)

story_run_failure = Summary(
    'asyncy_engine_failure_seconds',
    'Time spent executing a story (failed)',
    ['story_name']
)

story_run_total = Summary(
    'asyncy_engine_total_seconds',
    'Time spent executing a story (total)',
    ['story_name']
)

container_exec_seconds_total = Summary(
    'asyncy_engine_container_run_seconds',
    'Time spent executing commands in containers',
    ['story_name', 'container']
)
