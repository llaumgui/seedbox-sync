# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Guillaume Kulakowski <guillaume@kulakowski.fr>
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.
#
# flake8: noqa

"""
The seedboxsync package with all SeedBoxSync modules.

Exit code:
    - 0: All is good
    - 1:
    - 2: Logging error
    - 3: Lock error
    - 4: Transfert error
    - 5: Configuration error
    - 6: Unsupported protocole
    - 7: Unsupported protocole module
    - 8: Dependency error
"""

from .exceptions import DependencyException
from .helper import Helper, SeedboxDbHelper
from .seedboxsync import BlackHoleSync, DownloadSync, GetInfos
from .cli import CLI
from .transport import SeedboxAbstractClient
