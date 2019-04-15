# -*- coding: utf-8 -*-
from asyncy.Containers import Containers
from asyncy.constants.ServiceConstants import ServiceConstants

import storyscript


def test_containers_format_command(story):
    """
    Ensures a simple resolve can be performed
    """
    story_text = 'alpine echo msg:"foo"\n'
    story.context = {}
    story.app.services = {
        'alpine': {
            ServiceConstants.config: {
                'actions': {
                    'echo': {
                        'arguments': {'msg': {'type': 'string'}}
                    }
                }
            }
        }
    }

    story.tree = storyscript.Api.loads(story_text)['tree']
    assert Containers.format_command(
        story, story.line('1'), 'alpine', 'echo'
    ) == ['echo', '{"msg":"foo"}']


def test_containers_format_command_no_arguments(story):
    story_text = 'alpine echo\n'
    story.context = {}
    story.app.services = {
        'alpine': {
            ServiceConstants.config: {
                'actions': {
                    'echo': {}
                }
            }
        }
    }
    story.tree = storyscript.Api.loads(story_text)['tree']
    assert Containers.format_command(
        story, story.line('1'), 'alpine', 'echo'
    ) == ['echo']
