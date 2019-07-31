# -*- coding: utf-8 -*-
import os

import pytest
from pytest import fixture, mark

from storyruntime.Exceptions import StoryscriptError
from storyruntime.processing.Services import Services
from storyruntime.processing.internal import File


@fixture
def line():
    return {}


@fixture
def service_patch(patch):
    patch.object(Services, 'register_internal')


@fixture
def file_io(patch, service_patch):
    patch.object(File, 'open')
    patch.object(os, 'makedirs')


@fixture
def exc():
    def throw(*args, **kwargs):
        raise IOError()

    return throw


def test_service_file_safe_path(patch, story):
    patch.object(story, 'get_tmp_dir', return_value='')
    assert File.safe_path(story, '../') == '/'
    assert File.safe_path(story, '/a') == '/a'
    assert File.safe_path(story, '../../../../') == '/'


@mark.asyncio
async def test_service_file_mkdir(story, line, file_io):
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    await File.file_mkdir(story, line, resolved_args)
    os.makedirs.assert_called_with(f'{story.get_tmp_dir()}/my_path',
                                   exist_ok=True)


@mark.asyncio
async def test_service_file_mkdir_exc(patch, story, line, file_io, exc):
    patch.object(os, 'makedirs', side_effect=exc)
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    with pytest.raises(StoryscriptError):
        await File.file_mkdir(story, line, resolved_args)


@mark.asyncio
async def test_service_file_write(story, line, file_io):
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path',
        'content': 'my_content'
    }
    await File.file_write(story, line, resolved_args)
    File.open.assert_called_with(f'{story.get_tmp_dir()}/my_path', 'w')
    File.open().__enter__().write.assert_called_with('my_content')


@mark.asyncio
async def test_service_file_write_bytes(story, line, file_io):
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path',
        'content': b'my_content'
    }
    await File.file_write(story, line, resolved_args)
    File.open.assert_called_with(f'{story.get_tmp_dir()}/my_path', 'wb')
    File.open().__enter__().write.assert_called_with(b'my_content')


@mark.asyncio
async def test_service_file_write_exc(patch, story, line, service_patch, exc):
    patch.object(File, 'open', side_effect=exc)
    resolved_args = {
        'path': 'my_path'
    }
    with pytest.raises(StoryscriptError):
        await File.file_write(story, line, resolved_args)


@mark.asyncio
async def test_service_file_read(story, line, file_io):
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    result = await File.file_read(story, line, resolved_args)
    File.open.assert_called_with(f'{story.get_tmp_dir()}/my_path', 'r')

    assert result == File.open().__enter__().read()


@mark.asyncio
async def test_service_file_read_bytes(story, line, file_io):
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path',
        'raw': True
    }
    result = await File.file_read(story, line, resolved_args)
    File.open.assert_called_with(f'{story.get_tmp_dir()}/my_path', 'rb')

    assert result == File.open().__enter__().read()


@mark.asyncio
async def test_service_file_read_exc(patch, story, line, service_patch, exc):
    patch.object(File, 'open', side_effect=exc)
    resolved_args = {
        'path': 'my_path'
    }
    with pytest.raises(StoryscriptError):
        await File.file_read(story, line, resolved_args)


@mark.asyncio
async def test_service_file_exists(patch, story, line):
    patch.object(os.path, 'exists')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    result = await File.file_exists(story, line, resolved_args)
    os.path.exists.assert_called_with(f'{story.get_tmp_dir()}/my_path')

    assert result == os.path.exists()
