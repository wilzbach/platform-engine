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
    name='evenflow',
    description='Asyncy server',
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
        'aratrum==0.3.2',
        'celery==4.1.0',
        'docker==2.7.0',
        'peewee==2.10.2',
        'psycopg2==2.7.3.2',
        'pyjwt==1.5.3',
        'pymongo==3.6.0',
        'requests==2.18.4',
        'statsd==3.2.2',
        'storyscript==0.0.2',
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3'
    ],
    entry_points="""
        [console_scripts]
        evenflow=evenflow.Cli:Cli.main
    """
)
