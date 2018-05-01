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
    version='0.0.2',
    packages=find_packages(),
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-mock'
    ],
    setup_requires=['pytest-runner'],
    install_requires=[
        'grpcio>=1.11.0',
        'grpcio-tools>=1.11.0',
        'click>=6.7',
        'cryptography>=2.1.4',
        'dateparser>=0.7.0',
        'docker>=2.7.0',
        'frustum>=0.0.1',
        'logdna>=1.2.5',
        'pymongo>=3.6.0',
        'requests>=2.18.4',
        'storyscript>=0.0.7',
        'ujson>=1.35'
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3'
    ],
    entry_points="""
        [console_scripts]
        asyncy-engine=asyncy.Cli:Cli.main
        asyncy-server=asyncy.Service:Service.main
    """
)
