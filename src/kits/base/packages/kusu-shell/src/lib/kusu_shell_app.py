#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import sys
from optparse import OptionParser

import kusu.core.database as kusudb

DEFAULT_VERSION = "version ${VERSION_STR}"
DEFAULT_DB_DRIVER = 'postgres'
DEFAULT_DB_NAME = 'kusudb'
DEFAULT_DB_USER = 'apache'

class KusuShellApp(object):
    def __init__(self, args, db=None, **kwargs):
        """Set up the KusuShellApp object.

        Arguments:
        args -- a list of arguments to be parsed by OptionParser

        Keyword arguments:
        db -- a kusudb instance, defaults to None, in which case it will be
              initialized according to defaults
        out -- stream to write stdout to, default sys.stdout
        err -- stream to write stderr to, default sys.stderr

        """
        super(KusuShellApp, self).__init__()
        self._db = db
        self._out = kwargs.pop('out', sys.stdout)
        self._err = kwargs.pop('err', sys.stderr)
        self._parser = self._configure_options()
        self._options, self._remaining_args = self._parser.parse_args(args[1:])

    def _configure_options(self, usage=None, version=DEFAULT_VERSION):
        """Configure default command line options.

        Call from subclasses to obtain an OptionParser instance with default
        options added.

        """
        parser = OptionParser(usage=usage, version=version)

        parser.add_option('--db-driver', default=DEFAULT_DB_DRIVER, help='Database driver (sqlite, mysql, postgres)')
        parser.add_option('--db-name', default=DEFAULT_DB_NAME, help='Database name')
        parser.add_option('--db-user', default=DEFAULT_DB_USER, help='Database username')
        parser.add_option('--db-password', help='Database password')

        return parser

    def run(self):
        raise NotImplementedError

    def _needs_database(self):
        """Called by subclasses when DB access is required."""
        if self._db is None:
            self._configure_database()

    def _configure_database(self):
        self._db = kusudb.DB(self._options.db_driver,
                             db=self._options.db_name,
                             username=self._options.db_user,
                             password=self._options.db_password)

    def print_result(self):
        """Override in subclasses when required."""
        pass

    def generate_output_artifacts(self):
        """Override in subclasses when required."""
        pass
