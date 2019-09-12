# -*- coding: utf-8 -*-
from storyruntime.Containers import Containers
from storyruntime.constants.ServiceConstants import ServiceConstants

import storyscript


def test_containers_format_command(story):
    """
    Ensures a simple resolve can be performed
    """
    story_text = 'yaml parse data:"foo"\n'
    story.app.services = {
        'yaml': {
            ServiceConstants.config: {
                'actions': {
                    'parse': {
                        'arguments': {'data': {'type': 'string'}}
                    }
                }
            }
        }
    }

    story.tree = storyscript.Api.loads(story_text).result().output()['tree']
    assert Containers.format_command(
        story, story.line('1'), 'yaml', 'parse'
    ) == ['parse', '{"data":"foo"}']


def test_containers_format_command_no_arguments(story):
    story_text = 'uuid generate\n'
    story.app.services = {
        'uuid': {
            ServiceConstants.config: {
                'actions': {
                    'generate': {}
                }
            }
        }
    }
    story.tree = storyscript.Api.loads(story_text).result().output()['tree']
    assert Containers.format_command(
        story, story.line('1'), 'uuid', 'generate'
    ) == ['generate']
