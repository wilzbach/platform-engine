# -*- coding: utf-8 -*-
import os
import pathlib
import shutil

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
    patch.object(story.app, 'get_tmp_dir', return_value='')
    assert File.safe_path(story, '../') == '/'
    assert File.safe_path(story, '/a') == '/a'
    assert File.safe_path(story, '../../../../') == '/'


@mark.asyncio
async def test_service_file_mkdir(patch, story, line, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    await File.file_mkdir(story, line, resolved_args)
    os.makedirs.assert_called_with(f'{story.app.get_tmp_dir()}/my_path',
                                   exist_ok=True)


@mark.asyncio
async def test_service_file_mkdir_exc(patch, story, line, file_io, exc):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    patch.object(os, 'makedirs', side_effect=exc)
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    with pytest.raises(StoryscriptError):
        await File.file_mkdir(story, line, resolved_args)


@mark.asyncio
async def test_service_file_write(patch, story, line, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path',
        'content': 'my_content'
    }
    await File.file_write(story, line, resolved_args)
    File.open.assert_called_with(f'{story.app.get_tmp_dir()}/my_path', 'w')
    File.open().__enter__().write.assert_called_with('my_content')


@mark.asyncio
async def test_service_file_write_bytes(patch, story, line, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path',
        'content': b'my_content'
    }
    await File.file_write(story, line, resolved_args)
    File.open.assert_called_with(f'{story.app.get_tmp_dir()}/my_path', 'wb')
    File.open().__enter__().write.assert_called_with(b'my_content')


@mark.asyncio
async def test_service_file_write_exc(patch, story, line, service_patch, exc):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    patch.object(File, 'open', side_effect=exc)
    resolved_args = {
        'path': 'my_path'
    }
    with pytest.raises(StoryscriptError):
        await File.file_write(story, line, resolved_args)


@mark.asyncio
async def test_service_file_read(patch, story, line, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    result = await File.file_read(story, line, resolved_args)
    File.open.assert_called_with(f'{story.app.get_tmp_dir()}/my_path', 'r')

    assert result == File.open().__enter__().read()


@mark.asyncio
async def test_service_file_read_bytes(patch, story, line, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path',
        'raw': True
    }
    result = await File.file_read(story, line, resolved_args)
    File.open.assert_called_with(f'{story.app.get_tmp_dir()}/my_path', 'rb')

    assert result == File.open().__enter__().read()


@mark.asyncio
async def test_service_file_read_exc(patch, story, line, service_patch, exc):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    patch.object(File, 'open', side_effect=exc)
    resolved_args = {
        'path': 'my_path'
    }
    with pytest.raises(StoryscriptError):
        await File.file_read(story, line, resolved_args)


@mark.asyncio
@mark.parametrize('recursive', [True, False])
async def test_service_file_list(magic, patch, story, line,
                                 recursive, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path',
        'recursive': recursive
    }
    patch.object(os.path, 'exists', return_value=True)
    patch.object(os.path, 'isdir', return_value=True)
    patch.object(os.path, 'join')
    patch.object(pathlib.Path, 'iterdir', new=magic())
    patch.object(pathlib.Path, 'rglob', new=magic())

    await File.file_list(story, line, resolved_args)

    path = f'{story.app.get_tmp_dir()}/my_path'

    os.path.exists.assert_called_with(path)
    os.path.isdir.assert_called_with(path)

    if recursive:
        pathlib.Path.rglob.assert_called()
    else:
        pathlib.Path.iterdir.assert_called()


@mark.asyncio
async def test_service_file_remove_dir(patch, story, line, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    patch.object(os.path, 'exists', return_value=True)
    patch.object(os.path, 'isdir', return_value=True)
    patch.object(shutil, 'rmtree')

    await File.file_remove_dir(story, line, resolved_args)

    path = f'{story.app.get_tmp_dir()}/my_path'

    os.path.exists.assert_called_with(path)
    os.path.isdir.assert_called_with(path)

    shutil.rmtree.assert_called_with(path, ignore_errors=True)


@mark.asyncio
@mark.parametrize('exists', [True, False])
async def test_service_file_remove_dir_exc(patch, story, line,
                                           exists, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    patch.object(os.path, 'exists', return_value=exists)
    patch.object(os.path, 'isdir', return_value=False)

    with pytest.raises(StoryscriptError):
        await File.file_remove_dir(story, line, resolved_args)


@mark.asyncio
async def test_service_file_remove_file(patch, story, line, file_io):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    patch.object(os.path, 'exists', return_value=True)
    patch.object(os.path, 'isdir', return_value=False)
    patch.object(os, 'remove')

    await File.file_remove_file(story, line, resolved_args)

    path = f'{story.app.get_tmp_dir()}/my_path'

    os.path.exists.assert_called_with(path)
    os.path.isdir.assert_called_with(path)
    os.remove.assert_called_with(path)


@mark.asyncio
@mark.parametrize('exists', [True, False])
async def test_service_file_remove_file_exc(patch, story, line, exists):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    patch.object(os.path, 'exists', return_value=exists)
    patch.object(os.path, 'isdir', return_value=True)

    with pytest.raises(StoryscriptError):
        await File.file_remove_file(story, line, resolved_args)


@mark.asyncio
async def test_service_file_exists(patch, story, line):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    patch.object(os.path, 'exists')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    result = await File.file_exists(story, line, resolved_args)
    os.path.exists.assert_called_with(f'{story.app.get_tmp_dir()}/my_path')

    assert result == os.path.exists()


@mark.asyncio
async def test_service_file_isdir(patch, story, line):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    patch.object(os.path, 'isdir')

    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    result = await File.file_isdir(story, line, resolved_args)
    os.path.isdir.assert_called_with(f'{story.app.get_tmp_dir()}/my_path')

    assert result == os.path.isdir()


@mark.asyncio
async def test_service_file_isfile(patch, story, line):
    patch.object(story.app, 'get_tmp_dir', return_value='/tmp/my.story')
    patch.object(os.path, 'isfile')
    story.execution_id = 'super_super_tmp'
    resolved_args = {
        'path': 'my_path'
    }
    result = await File.file_isfile(story, line, resolved_args)
    os.path.isfile.assert_called_with(f'{story.app.get_tmp_dir()}/my_path')

    assert result == os.path.isfile()
