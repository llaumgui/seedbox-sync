#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Guillaume Kulakowski <guillaume@kulakowski.fr>
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.
#

"""
Start CLI interface.

Exit code:
    - 0: All is good
    - 1:
    - 2: Logging error
    - 3: Lock error
    - 4: Transfert error
    - 5: Configuration error
    - 6: Unsupported protocole
    - 8: Dependency error
"""

try:
    from seedboxsync.exceptions import (ConnectionException, ConfigurationException, DependencyException,
                                        IsLockedException, LockException, LogException, TransportProtocoleException)
    from seedboxsync.cli import CLI
    from seedboxsync.helper import Helper
except DependencyException as exc:
    print(str(exc))
    exit(8)
import os
import sys

# If avalaible, insert local directories into path
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seedboxsync')):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    if __name__ == '__main__':
        cli = CLI()
except LogException as exc:
    exit(2)
    print(str(exc))
except LockException as exc:
    exit(2)
    print(str(exc))
except ConnectionException as exc:
    Helper.log_print(str(exc), msg_type='error')
    exit(4)
except ConfigurationException as exc:
    Helper.log_print(str(exc), msg_type='error')
    exit(5)
except TransportProtocoleException as exc:
    print(str(exc))
    exit(6)
except DependencyException as exc:
    print(str(exc))
    exit(8)
except IsLockedException:
    exit(0)
except KeyboardInterrupt:
    exit(0)
