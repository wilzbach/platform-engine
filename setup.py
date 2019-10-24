#!/usr/bin/env python
import io
import os
import sys

from setuptools import find_packages, setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()


readme = io.open('README.md', 'r', encoding='utf-8').read()

setup(
    name='storyruntime',
    description='The runtime powering Storyscript Cloud & executing stories.',
    long_description=readme,
    author='Storyscript',
    author_email='noreply@storyscript.io',
    version='0.2.0',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'prometheus-client==0.2.0',
        'tornado==5.0.2',
        'click==7.0',
        'frustum==0.0.6',
        'sentry-sdk==0.10.2',
        'storyscript==0.25.3',
        'ujson==1.35',
        'certifi>=2018.8.24',
        'asyncpg==0.18.3',
        'numpy==1.16.4',
        'expiringdict==1.1.4',
        'requests==2.21.0'  # Used for structures like CaseInsensitiveDict.
    ],
    extras_require={
        'pep8': [
            'flake8==3.5.0',
            'flake8-quotes==1.0.0',
            'flake8-import-order==0.18',
            'pep8-naming==0.7.0'
        ],
        'py37': [
            'pytest==3.6.3',
            'pytest-cov==2.5.1',
            'pytest-mock==1.10.0',
            'pytest-asyncio==0.8.0',
        ]
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3'
    ],
    entry_points="""
        [console_scripts]
        storyscript-server=storyruntime.Service:Service.main
    """
)
