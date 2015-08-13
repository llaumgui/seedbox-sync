# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Guillaume Kulakowski <guillaume@kulakowski.fr>
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.
#

"""
Main module of used by seedboxseed CLI.
"""

from __future__ import print_function, absolute_import
from seedboxsync.transport import SeedboxSftpTransport
from seedboxsync.helper import (Helper, SeedboxDbHelper)
from prettytable import from_db_cursor
import ConfigParser as configparser
import logging
import glob
import os
import datetime


#
# SeedboxSync main class
#
class SeedboxSync(object):
    """
    Super class for SeedboxSync projet.

    Exit code:
        - 0: All is good
        - 1: Import error
        - 2: Logging error
        - 3: Lock error
        - 4: connection error
        - 5: No configuration file found
    """

    CONF_PREFIX = None

    def __init__(self):
        """
        Main constructor: initialize the synchronization for child classes.
        """

        # Load configuration (seedbox.ini) from the good location
        self.__config_file = self.__get_config_file()

        # ConfigParser instance
        self._config = configparser.ConfigParser()
        self._config.read(self.__config_file)

        # Some path used by classes
        self.__lock_file = self._config.get('PID', self.CONF_PREFIX + 'path')
        self._db_path = self._config.get('Local', 'sqlite_path')
        self._finished_path = self._config.get('Seedbox', 'finished_path')

        # Load and configure logging
        self.__setup_logging()

        # Set empty transport
        self._transport = None

        # Set empty DB storage
        self._db = None

    def __get_config_file(self):
        """
        Load configuration from the good location:
            - seedboxsync folder
            - User folder (~)
            - /etc/seedboxsync
            - From environment variable SEEDBOXSYNC_CONF
        """
        config_file = None
        for location in os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'), \
                os.path.expanduser("~"), os.path.expanduser("~/.seedboxsync"), \
                '/etc/seedboxsync', os.environ.get('SEEDBOXSYNC_CONF'):
            try:
                seedbox_ini = os.path.join(location, 'seedboxsync.ini')
                if os.path.isfile(seedbox_ini):
                    config_file = seedbox_ini
                    break
            except:
                pass

        if config_file is None:
            print('No configuration file found !')
            exit(5)

        return config_file

    def __setup_logging(self):
        """
        Set the logging instance.
        See: https://docs.python.org/2/library/logging.html
        """
        try:
            logging.basicConfig(format='%(asctime)s %(levelname)s %(process)d - %(message)s',
                                filename=self._config.get('Log', self.CONF_PREFIX + 'file_path'),
                                level=eval('logging.' + self._config.get('Log', self.CONF_PREFIX + 'level')))
            logging.debug('Start')
            Helper.log_print('Load config from "' + self.__config_file + '"', msg_type='debug')
        except Exception, exc:
            Helper.log_print(str(exc), msg_type='error')
            exit(2)

    def _lock(self):
        """
        Lock task by a pid file to prevent launch two time.
        """
        logging.debug('Lock task by ' + self.__lock_file)
        try:
            lock = open(self.__lock_file, 'w+')
            lock.write(str(os.getpid()))
            lock.close()
        except Exception, exc:
            Helper.log_print(str(exc), msg_type='error')
            exit(3)

    def _unlock(self):
        """
        Unlock task, remove pid file.
        """
        logging.debug('Unlock task by ' + self.__lock_file)
        try:
            os.remove(self.__lock_file)
        except Exception, exc:
            Helper.log_print(str(exc), msg_type='error')

    def is_locked(self):
        """
        Test if task is locked by a pid file to prevent launch two time.
        """
        if os.path.isfile(self.__lock_file):
            Helper.log_print('Already running', msg_type='info')
            return True

        return False

    def _get_transport(self):
        """
        Init transport class. Currently only support sFTP.
        """
        try:
            return SeedboxSftpTransport(host=self._config.get('Seedbox', 'transfer_host'),
                                        port=int(self._config.get('Seedbox', 'transfer_port')),
                                        login=self._config.get('Seedbox', 'transfer_login'),
                                        password=self._config.get('Seedbox', 'transfer_password'))
        except Exception, exc:
            Helper.log_print('Connection fail: ' + str(exc), msg_type='error')
            self._unlock()
            exit(4)

    def _store_torrent_infos(self, torrent_path):
        """
        Get and store information about torrent.
        """
        torrent_name = os.path.basename(torrent_path)
        torrent_info = Helper.get_torrent_infos(torrent_path)

        if torrent_info is not None:
            files = torrent_info['info']['files']
            logging.debug('Torrent announce: "' + torrent_info['announce'] + '"')

            # Store torrent informations in torrent table
            self._db.cursor.execute('''INSERT INTO torrent(name, announce, sent) VALUES (?, ?, ?)''', (
                torrent_name, torrent_info['announce'], datetime.datetime.now()))

            # Store file information in torrent_file table
            torrent_id = int(self._db.cursor.lastrowid)
            for file in files:
                path = os.path.join(*file['path'])
                logging.debug('Torrent file: ' + str(torrent_id) + '" ' + path + '" ' + str(file['length']) + 'o')
                self._db.cursor.execute('''INSERT INTO torrent_file(torrent_id, path, length) VALUES (?, ?, ?)''', (
                    torrent_id, path, int(file['length'])))

            self._db.commit()


#
# BlackHoleSync class
#
class BlackHoleSync(SeedboxSync):
    """
    Class which allows to sync a local black hole (ie: from a NAS) with a SeedBox
    black hole.
    """

    CONF_PREFIX = 'blackhole_'

    def __init__(self):
        """
        Constructor: initialize the blackhole synchronization.
        """
        # Call super class
        super(self.__class__, self).__init__()

    def __upload_torrent(self, torrent_path):
        """
        Upload a single torrent
        """

        torrent_name = os.path.basename(torrent_path)
        Helper.log_print('Upload "' + torrent_name + '"', msg_type='info')

        try:
            logging.debug('Upload "' + torrent_path + '" in "' + self._config.get('Seedbox', 'tmp_path') + '" directory')
            self._transport.client.put(torrent_path,  os.path.join(self._config.get('Seedbox', 'tmp_path'), torrent_name))

            # Chmod
            if self._config.get('Seedbox', 'transfer_chmod') != "false":
                logging.debug('Change mod in ' + self._config.get('Seedbox', 'transfer_chmod'))
                self._transport.client.chmod(os.path.join(self._config.get('Seedbox', 'tmp_path'), torrent_name),
                                             int(self._config.get('Seedbox', 'transfer_chmod'), 8))

            # Move from tmp
            logging.debug('Move from "' + self._config.get('Seedbox', 'tmp_path') + '" to "' + self._config.get('Seedbox', 'watch_path') + '"')
            self._transport.client.rename(os.path.join(self._config.get('Seedbox', 'tmp_path'), torrent_name),
                                          os.path.join(self._config.get('Seedbox', 'watch_path'), torrent_name))

            # Store in DB
            self._store_torrent_infos(torrent_path)

            # Remove local torent
            logging.debug('Remove local torrent "' + torrent_path + '"')
            os.remove(torrent_path)
        except Exception, exc:
            Helper.log_print(str(exc), msg_type='warning')

    def do_sync(self):
        """
        Do the blackhole synchronization.
        """
        # Create lock file.
        self._lock()

        # Get all torrents
        torrents = glob.glob(self._config.get('Local', 'wath_path') + '/*.torrent')
        if len(torrents) > 0:
            # Init transport_client
            self._transport = self._get_transport()

            # Init DB
            self._db = SeedboxDbHelper(self._db_path)

            # Upload torrents one by one
            for torrent in torrents:
                self.__upload_torrent(torrent)

            # Close resources
            self._transport.close()
            self._db.close()
        else:
            Helper.log_print('No torrent in "' + self._config.get('Local', 'wath_path') + '"', msg_type='info')

        # Remove lock file.
        self._unlock()


#
# GetFinished class
#
class DownloadSync(SeedboxSync):
    """
    Class which allows ti download files from Seedbox to NAS and store files
    already downloaded in a sqlite database.
    """

    CONF_PREFIX = 'download_'

    def __init__(self):
        """
        Constructor: initialize download.
        """
        # Call super class
        super(self.__class__, self).__init__()

    def __get_file(self, filepath):
        """
        Download a single file.
        """
        # Local path (without seedbox folder prefix)
        filepath_without_prefix = filepath.replace(self._config.get('Seedbox', 'finished_path').strip("/"), "", 1).strip("/")
        local_filepath = os.path.join(self._config.get('Local', 'download_path'), filepath_without_prefix)
        local_path = os.path.dirname(local_filepath)
        Helper.mkdir_p(local_path)

        try:
            # Start timestamp in database
            self._db.cursor.execute('''INSERT INTO download(path, started) VALUES (?, ?)''', (filepath, datetime.datetime.now()))
            self._db.commit()

            # Get file
            Helper.log_print('Download "' + filepath + '"', msg_type='info')
            logging.debug('Download "' + filepath + '" in "' + local_path + '"')
            self._transport.client.get(filepath, local_filepath)

            # Store in database
            self._db.cursor.execute('''UPDATE download SET finished = ? WHERE id=?''', (datetime.datetime.now(), self._db.cursor.lastrowid))
            self._db.commit()
        except Exception, exc:
            Helper.log_print('Upload fail: ' + str(exc), msg_type='error')

    def __already_download(self, filepath):
        """
        Get in database if file was already downloaded.
        """
        self._db.cursor.execute('''SELECT count(*) FROM download WHERE path=? AND finished > 0''', [filepath])
        (number_of_rows,) = self._db.cursor.fetchone()
        if number_of_rows == 0:
            return False
        else:
            return True

    def do_sync(self):
        """
        Do the synchronization.
        """
        # Create lock file.
        self._lock()

        # Init transport_client
        self._transport = self._get_transport()

        # Init DB
        self._db = SeedboxDbHelper(self._db_path)

        Helper.log_print('Get file list in "' + self._finished_path + '"', msg_type='debug')

        # Get all files
        self._transport.client.chdir(os.path.split(self._finished_path)[0])
        parent = os.path.split(self._finished_path)[1]
        for walker in self._transport.walk(parent):
            for filename in walker[2]:
                filepath = os.path.join(walker[0], filename)
                if os.path.splitext(filename)[1] == self._config.get('Seedbox', 'part_suffix'):
                    Helper.log_print('Skip part file "' + filename + '"', msg_type='debug')
                elif self.__already_download(filepath):
                    Helper.log_print('Skip already downloaded "' + filename + '"', msg_type='debug')
                else:
                    self.__get_file(filepath)

        # Close resources
        self._transport.close()
        self._db.close()

        # Remove lock file.
        self._unlock()


#
# GetInfos class
#
class GetInfos(SeedboxSync):
    """
    Class which get informations about sync from database.
    """

    CONF_PREFIX = 'blackhole_'

    def __init__(self):
        """
        Constructor: initialize the blackhole synchronization.
        """
        # Call super class
        super(self.__class__, self).__init__()

        # Init DB
        self._db = SeedboxDbHelper(self._db_path)

    def get_lasts_torrents(self, number=10):
        """
        Get lasts 10 torrents from database.
        """
        self._db.cursor.execute('''SELECT id, name, sent FROM torrent ORDER BY sent ASC LIMIT ?''', [number])
        prettytable = from_db_cursor(self._db.cursor)
        self._db.close()

        return prettytable

    def get_lasts_downloads(self, number=10):
        """
        Get lasts 10 torrents from database.
        """
        self._db.cursor.execute('''SELECT * FROM download ORDER BY finished ASC LIMIT ?''', [number])
        prettytable = from_db_cursor(self._db.cursor)
        self._db.close()

        return prettytable

    def get_unfinished_downloads(self):
        """
        Get lasts 10 torrents from database.
        """
        self._db.cursor.execute('''SELECT * FROM download  WHERE finished is null ORDER BY started asc''')
        prettytable = from_db_cursor(self._db.cursor)
        self._db.close()

        return prettytable
