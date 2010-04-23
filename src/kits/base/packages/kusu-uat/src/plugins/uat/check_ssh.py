#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: check_ssh.py 461 2010-01-28 08:04:46Z mike $
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
import telnetlib
import socket

from optparse import OptionParser
from kusu.uat import UATPluginBase, UATHelper

usage = """usage: check_ssh destination"""
DEFAULT_SSH_PORT = '22'
DEFAULT_SOCKET_TIMEOUT_SECONDS = 10

class CheckSSH(UATPluginBase):
    def __init__(self, args=None):
        super(CheckSSH, self).__init__()
        self._logger = args['logger']
         
        self._remote_host = ''
        self._remote_port = DEFAULT_SSH_PORT
        self._return_code = 0
        self.__socket_timeout = DEFAULT_SOCKET_TIMEOUT_SECONDS

    def pre_check(self):
        pass

    def post_check(self):
        pass

    def node_setup(self, node):
        pass

    def node_teardown(self, node):
        pass

    def run(self, args):
        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])

        if len(remaining_args) != 1:  # require only one destination
            parser.print_usage(file=sys.stderr)
            sys.stderr.write('Please provide destination\n')
            return 1

        self._remote_host = remaining_args[0]

        if options.port is not None:
            self.set_port(options.port)

        returncode = self._run()

        return returncode, self.status

    def _configure_options(self):
        """Sets up command line options"""
        parser = OptionParser(usage=usage)
        parser.add_option('-p', '--port',
                          help='Specify the remote port on which to check for an \
                                SSH server')
        return parser

    def set_port(self, remote_port):
        self._remote_port = remote_port

    def _run(self):
        telnet_connection = telnetlib.Telnet()
        try:
            old_default_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.__socket_timeout)
            try:
                telnet_connection.open(self._remote_host, self._remote_port)
            except socket.timeout, e:
                self._return_code = 1
                self.status = self._process_response(e.args[0])
                return self._return_code
            except socket.error, e:
                self._return_code = e.args[0]
                self.status = self._process_response(str(e.args))
                return self._return_code
        finally:
            socket.setdefaulttimeout(old_default_timeout)

        response = telnet_connection.read_until('\n')
        self.status = self._process_response(response)

        telnet_connection.write("SSH-2.0-uat_check_ssh-PCM-2.0")
        telnet_connection.close()

        return self._return_code

    def _process_response(self, response):
        # Perhaps in the future there will be more to process, such as
        # extracting the protocol version, such as Nagios does:
        # http://nagiosplug.svn.sourceforge.net/viewvc/nagiosplug/nagiosplug/trunk/plugins/check_ssh.c?view=markup
        # For now, we'll just strip the trailing newline and return the whole
        # string as-is.
        status = ""
        return status + response.strip()

    def generate_output_artifacts(self, artifact_dir):
        filename = artifact_dir / self._remote_host / 'check_ssh.out'
        if self._return_code != 0:
            filename = artifact_dir / self._remote_host / 'check_ssh.err'
        UATHelper.generate_file_from_lines(filename, [self.status + '\n'])
