# -*- coding: utf-8 -*-
import os
import pathlib
import shutil

from .Decorators import Decorators
from ...Exceptions import StoryscriptError


def safe_path(story, path):
    """
    safe_path resolves a path completely (../../a/../b) completely
    and returns an absolute path which can be used safely by prepending
    the story's tmp dir. This ensures that the story cannot abuse the system
    and write elsewhere, for example, stories.json.
    :param story: The story (Story object)
    :param path: A path to be resolved
    :return: The absolute path, which can be used to read/write directly
    """
    story.app.create_tmp_dir()
    # Adding the leading "/" is important, otherwise the current working
    # directory will be used as the base path.
    path = f'/{path}'
    path = pathlib.Path(path).resolve()
    return f'{story.app.get_tmp_dir()}{os.fspath(path)}'


def clean_path(story, path):
    return f'/{str(pathlib.Path(path).relative_to(story.app.get_tmp_dir()))}'


@Decorators.create_service(name='file', command='mkdir', arguments={
    'path': {'type': 'string'}
})
async def file_mkdir(story, line, resolved_args):
    path = safe_path(story, resolved_args['path'])
    try:
        os.makedirs(path, exist_ok=True)
    except IOError as e:
        raise StoryscriptError(message=f'Failed to create directory: {e}',
                               story=story, line=line)


@Decorators.create_service(name='file', command='write', arguments={
    'path': {'type': 'string'},
    'binary': {'type': 'boolean', 'required': False},
    'encoding': {'type': 'string', 'required': False},
    'content': {'type': 'any'}
})
async def file_write(story, line, resolved_args):
    path = safe_path(story, resolved_args['path'])

    try:
        content = resolved_args['content']
        if resolved_args.get('binary', False):
            content = bytes(
                content,
                resolved_args.get('encoding', 'utf-8')
            )
        if isinstance(content, bytes):
            mode = 'wb'
        else:
            mode = 'w'
        with open(path, mode) as f:
            f.write(content)
    except (KeyError, IOError) as e:
        raise StoryscriptError(message=f'Failed to write to file: {e}',
                               story=story, line=line)


@Decorators.create_service(name='file', command='read', arguments={
    'path': {'type': 'string'},
    'binary': {'type': 'boolean', 'required': False},
    'raw': {'type': 'boolean', 'required': False}
}, output_type='string')
async def file_read(story, line, resolved_args):
    path = safe_path(story, resolved_args['path'])

    try:
        # This is used to support the raw argument in case any
        # stories are using it. The binary is the preferred
        # verbage when utilizing binary data.
        if resolved_args.get(
            'binary', resolved_args.get('raw', False)
        ):
            mode = 'rb'
        else:
            mode = 'r'
        with open(path, mode) as f:
            return f.read()
    except FileNotFoundError:
        raise StoryscriptError(
            message=f'Failed to read file: No such file: '
            f'\'{clean_path(story, path)}\'',
            story=story, line=line
        )
    except IOError as e:
        raise StoryscriptError(message=f'Failed to read file: {e}',
                               story=story, line=line)


@Decorators.create_service(name='file', command='list', arguments={
    'path': {'type': 'string', 'required': False},
    'recursive': {'type': 'boolean', 'required': False}
}, output_type='list')
async def file_list(story, line, resolved_args):
    path = safe_path(story, resolved_args.get('path', '.'))
    try:
        if not os.path.exists(path):
            raise StoryscriptError(
                message=f'Failed to list directory: '
                f'No such directory: '
                f'\'{clean_path(story, path)}\'',
                story=story, line=line
            )

        if not os.path.isdir(path):
            raise StoryscriptError(
                message=f'Failed to list directory: '
                        f'The provided path is not a directory: '
                        f'\'{clean_path(story, path)}\'',
                story=story, line=line
            )

        items = []
        p = pathlib.Path(path)

        if resolved_args.get('recursive', False):
            children = p.rglob('*')
        else:
            children = p.iterdir()

        for child in children:
            items.append(f'/{str(child.relative_to(p))}')

        items.sort()

        return items
    except FileNotFoundError:
        raise StoryscriptError(
            message=f'Failed to read file: No such file: '
                    f'\'{clean_path(story, path)}\'',
            story=story, line=line)
    except IOError as e:
        raise StoryscriptError(message=f'Failed to list directory: {e}',
                               story=story, line=line)


@Decorators.create_service(name='file', command='removeDir', arguments={
    'path': {'type': 'string'}
})
async def file_remove_dir(story, line, resolved_args):
    path = safe_path(story, resolved_args.get('path', None))
    try:
        if not os.path.exists(path):
            raise StoryscriptError(
                message=f'Failed to remove directory: '
                        f'No such file or directory: '
                        f'\'{clean_path(story, path)}\'',
                story=story, line=line
            )

        if not os.path.isdir(path):
            raise StoryscriptError(
                message=f'Failed to remove directory: '
                        f'The given path is a file: '
                        f'\'{clean_path(story, path)}\'',
                story=story, line=line
            )
        else:
            shutil.rmtree(path, ignore_errors=True)

    except IOError as e:
        raise StoryscriptError(
            message=f'Failed to remove directory: {e}',
                    story=story, line=line
        )


@Decorators.create_service(name='file', command='removeFile', arguments={
    'path': {'type': 'string'}
})
async def file_remove_file(story, line, resolved_args):
    path = safe_path(story, resolved_args['path'])
    try:
        if not os.path.exists(path):
            raise StoryscriptError(
                message=f'Failed to remove file: '
                f'No such file or directory: '
                f'\'{clean_path(story, path)}\'',
                story=story, line=line
            )

        if os.path.isdir(path):
            raise StoryscriptError(
                message=f'Failed to remove file: '
                f'The given path is a directory: '
                f'\'{clean_path(story, path)}\'',
                story=story, line=line
            )
        else:
            os.remove(path)

    except IOError as e:
        raise StoryscriptError(
            message=f'Failed to remove file: {e}',
            story=story, line=line
        )


@Decorators.create_service(name='file', command='exists', arguments={
    'path': {'type': 'string'}
}, output_type='boolean')
async def file_exists(story, line, resolved_args):
    path = safe_path(story, resolved_args['path'])
    return os.path.exists(path)


@Decorators.create_service(name='file', command='isDir', arguments={
    'path': {'type': 'string'}
}, output_type='boolean')
async def file_isdir(story, line, resolved_args):
    path = safe_path(story, resolved_args['path'])
    try:
        return os.path.isdir(path)
    except FileNotFoundError:
        raise StoryscriptError(
            message=f'No such file or directory: '
            f'\'{clean_path(story, path)}\'',
            story=story, line=line)


@Decorators.create_service(name='file', command='isFile', arguments={
    'path': {'type': 'string'}
}, output_type='boolean')
async def file_isfile(story, line, resolved_args):
    path = safe_path(story, resolved_args['path'])
    try:
        return os.path.isfile(path)
    except FileNotFoundError:
        raise StoryscriptError(
            message=f'No such file or directory: '
            f'\'{clean_path(story, path)}\'',
            story=story, line=line)


def init():
    pass
