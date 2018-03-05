#!/usr/bin/env python
import io
import os
import sys

from setuptools import find_packages, setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()


readme = io.open('README.rst', 'r', encoding='utf-8').read()

setup(
    name='asyncy-platform-engine',
    description='The engine of the Asyncy platform',
    long_description=readme,
    author='Asyncy',
    author_email='noreply@asyncy.com',
    version='0.0.1',
    packages=find_packages(),
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-mock'
    ],
    setup_requires=['pytest-runner'],
    install_requires=[
        'celery>=4.1.0',
        'click>=6.7',
        'cryptography>=2.1.4',
        'docker>=2.7.0',
        'frustum>=0.0.1',
        'peewee>=2.10.2',
        'psycopg2>=2.7.3.2',
        'pyjwt>=1.5.3',
        'pymongo>=3.6.0',
        'pyyaml>=3.12',
        'requests>=2.18.4',
        'storyscript>=0.0.3'
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3'
    ],
    entry_points="""
        [console_scripts]
        asyncy=asyncy.Cli:Cli.main
    """
)
