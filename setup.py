#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018 Guillaume Kulakowski <guillaume@kulakowski.fr>
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.
#

from setuptools import setup, find_packages
from seedboxsync.core.version import get_version

VERSION = get_version()

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()

setup(
    name='seedboxsync',
    version=VERSION,
    description='Script for sync operations between your NAS and your seedbox',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Guillaume Kulakowski',
    author_email='guillaume@kulakowski.fr',
    url='https://llaumgui.github.io/seedboxsync/',
    license='GPL-2.0',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    package_data={'seedboxsync': ['templates/*']},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        seedboxsync = seedboxsync.main:main
    """,
)
