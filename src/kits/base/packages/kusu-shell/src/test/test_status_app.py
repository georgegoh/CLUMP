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

import os
import sys
from xml.dom.minidom import Document

from path import path
from nose.tools import raises
from mock import Mock, patch

KUSU_SHELL_PLUGIN_DIR = path(os.getenv("KUSU_ROOT", "/opt/kusu")) / 'lib' / 'plugins' / 'shell'
sys.path.append(str(KUSU_SHELL_PLUGIN_DIR))

from status_app import StatusApp, KUSU_SHELL_COMMAND

class TestStatusApp(object):
    @raises(ValueError)
    def test_no_arguments(self):
        StatusApp([KUSU_SHELL_COMMAND])

    @raises(RuntimeError)
    def test_invalid_argument(self):
        status_app = StatusApp([KUSU_SHELL_COMMAND, 'this_command_does_not_exist'])
        status_app.run()

    @raises(ValueError)
    def test_summary_no_arguments(self):
        StatusApp([KUSU_SHELL_COMMAND, 'summary'])

    @raises(RuntimeError)
    def test_summary_invalid_argument(self):
        status_app = StatusApp([KUSU_SHELL_COMMAND, 'summary', 'this_summary_command_does_not_exist'])
        status_app.run()

    @patch('status_app.Status')
    def test_run_nodegroups(self, mock_status):
        mock_status.return_value = mock_status

        args = [KUSU_SHELL_COMMAND, 'nodegroups']
        status_app = StatusApp(args)
        status_app.run()

        assert status_app._db is not None, "status_app._db was not initialized"
        assert status_app.result is not None, "status_app.result has not been assigned, is still None"
        assert mock_status.nodegroups.called, "status.nodegroups() was not called"

    @patch('status_app.Status')
    def test_run_nodes_summary(self, mock_status):
        mock_status.return_value = mock_status

        args = [KUSU_SHELL_COMMAND, 'summary', 'nodes']
        status_app = StatusApp(args)
        status_app.run()

        assert status_app._db is not None, "status_app._db was not initialized"
        assert status_app.result is not None, "status_app.result has not been assigned, is still None"
        assert mock_status.nodes_summary.called, "status.nodes_summary() was not called"

    def test_print_result_xml_custom_out(self):
        mock_out = Mock()

        xml_document = Document()
        test_node = xml_document.createElement("test")
        xml_document.appendChild(test_node)

        args = [KUSU_SHELL_COMMAND, 'nodegroups']
        status_app = StatusApp(args, out=mock_out)
        status_app.result = xml_document
        status_app.print_result()

        assert mock_out.write.called, "out.write() was not called"

    def test_use_custom_db(self):
        mock_DB = Mock()
        args = [KUSU_SHELL_COMMAND, 'nodegroups']
        status_app = StatusApp(args, db=mock_DB)
        assert mock_DB == status_app._db, "Could not set StatusApp._db"

        status_app._needs_database()
        assert mock_DB == status_app._db, "Supplied database object clobbered"

    @patch('kusu.shell.kusu_shell_app.kusudb')
    def test_specify_db_at_command_line(self, mock_kusudb):
        expected_db_driver = 'couchdb'
        expected_db_name = 'everything'
        expected_db_user = 'superman'
        expected_db_password = 'tornado'

        args = [KUSU_SHELL_COMMAND, 'nodegroups',
                '--db-driver', expected_db_driver,
                '--db-name', expected_db_name,
                '--db-user', expected_db_user,
                '--db-password', expected_db_password]
        status_app = StatusApp(args)
        status_app._needs_database()

        assert mock_kusudb.DB.called, "DB was not created"

        db_call_args = mock_kusudb.DB.call_args
        assert len(db_call_args[0]) > 0, "Required argument to DB() missing"

        db_call_dict = db_call_args[1]
        assert 'db' in db_call_dict, "'db' keyword argument to DB() not specified"
        assert 'username' in db_call_dict, "'username' keyword argument to DB() not specified"
        assert 'password' in db_call_dict, "'password' keyword argument to DB() not specified"
        assert db_call_dict['db'] == expected_db_name, "DB name was %s, expected %s" % (db_call_dict['db'], expected_db_name)
        assert db_call_dict['username'] == expected_db_user, "DB username was %s, expected %s" % (db_call_dict['username'], expected_db_user)
        assert db_call_dict['password'] == expected_db_password, "DB password was %s, expected %s" % (db_call_dict['password'], expected_db_password)
