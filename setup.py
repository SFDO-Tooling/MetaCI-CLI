#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup
from pkgutil import walk_packages

import metaci_cli

def find_packages(path='.', prefix=""):
    yield prefix
    prefix = prefix + "."
    for _, name, ispkg in walk_packages(path, prefix):
        if ispkg:
            yield name

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'coreapi-cli==1.0.6',
    'cumulusci>=2.0.0b87',
    'heroku3==3.3.0',
    'requests==2.18.4',
]

setup_requirements = [
    # TODO(jlantz): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='metaci_cli',
    version='0.1.3',
    description="A command line interface for MetaCI, a CI app run on Heroku for Salesforce development projects",
    long_description=readme + '\n\n' + history,
    author="Jason Lantz",
    author_email='jlantz@salesforce.com',
    url='https://github.com/jlantz/metaci_cli',
    packages=list(find_packages(metaci_cli.__path__, metaci_cli.__name__)),
    package_dir={'metaci_cli': 'metaci_cli'},
    entry_points={
        'console_scripts': [
            'metaci=metaci_cli.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="BSD license",
    zip_safe=False,
    keywords='metaci_cli',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
