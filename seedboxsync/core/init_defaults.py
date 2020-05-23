# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Guillaume Kulakowski <guillaume@kulakowski.fr>
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.
#

from cement.utils.misc import init_defaults

# setup the nested dicts
CONFIG = init_defaults('seedboxsync', 'seedbox', 'local', 'pid')

#
# Informations about your seedbox
#

# Informations about your seedbox connection
CONFIG['seedbox']['host'] = 'my-seedbox.ltd'
CONFIG['seedbox']['port'] = '22'
CONFIG['seedbox']['login'] = 'me'
CONFIG['seedbox']['password'] = 'p4sw0rd'

# For the moment, only sftp
CONFIG['seedbox']['protocol'] = 'sftp'

# Chmod torrent after upload (false = disable)
# Use octal notation like https://docs.python.org/3.4/library/os.html#os.chmod
CONFIG['seedbox']['chmod'] = '0o777'

# Use a tempory directory (you must create it !)
CONFIG['seedbox']['tmp_path'] = '/tmp'

# Your "watch" folder you must create it!)
CONFIG['seedbox']['watch_path'] = '/watch'

# Your finished folder you must create it!)
CONFIG['seedbox']['finished_path'] = '/files'

# Allow to remove a part of the synced path. In General, same path than "finished_path".
CONFIG['seedbox']['prefixed_path'] = '/files'

# Exclude part files
CONFIG['seedbox']['part_suffix'] = '.part'

# Exclude pattern from sync
# Use re syntaxe: https://docs.python.org/3/library/re.html
# Example: .*missing$|^\..*\.swap$
CONFIG['seedbox']['exclude_syncing'] = ''


#
# Informations about local environment (NAS ?)
#

# Your local "watch" folder
CONFIG['local']['watch_path'] = '~/watch'

# Path where download files
CONFIG['local']['download_path'] = '~/Download/'

# Use local sqlite database for store downloaded files
CONFIG['local']['db_file'] = '~/.config/seedboxsync/seedboxsync.db'


#
# PID and lock management to prevent several launch
#

# PID for blackhole sync
CONFIG['pid']['blackhole_path'] = '~/.config/seedboxsync/lock/blackhole.pid'

# PID for seedbox downloaded sync
CONFIG['pid']['download_path'] = '~/.config/seedboxsync/lock/download.pid'
