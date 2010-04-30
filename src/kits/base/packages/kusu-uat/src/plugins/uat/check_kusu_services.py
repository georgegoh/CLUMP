#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: check_kusu_services.py 461 2010-01-28 08:04:46Z mike $
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
import socket
import urllib2
from BaseHTTPServer import BaseHTTPRequestHandler

from kusu.uat import UATPluginBase, UATHelper

DEFAULT_HTTP_URL = "http://127.0.0.1"
DEFAULT_SOCKET_TIMEOUT_SECONDS = 10

class CheckKusuServices(UATPluginBase):
    def __init__(self, args=None):
        super(CheckKusuServices, self).__init__()
        self._logger = args['logger']
        self._http_url = DEFAULT_HTTP_URL
        self._http_return_code = None
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
        returncode = self._run()
        return returncode, self.status

    def _run(self):
        try:
            old_default_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.__socket_timeout)
            try:
                http_response = urllib2.urlopen(self._http_url)
            except urllib2.URLError, e:
                self._return_code = 1
                self.status = self._generate_status(str(e))
                return self._return_code
        finally:
            socket.setdefaulttimeout(old_default_timeout)

        self._return_code = 0
        # Check for http error in response code. 100-299 indicates success.
        if http_response.code <100 and http_response.code >= 300:
            self._return_code = http_response.code
        self.status = self._generate_status()
        return self._return_code

    def _generate_status(self, message=''):
        status = ''
        if self._return_code == 0:
            status = "webserver accessible"
        elif self._return_code == 1:
            status = "webserver unavailable. "
        else: # http error occurred, get the standard error message
            try:
                status, message = BaseHTTPRequestHandler.responses[self._return_code]
            except KeyError:
                status = "webserver unavailable. "
            else:
                status += ': '

        return status + message.strip()

    def generate_output_artifacts(self, artifact_dir):
        filename = artifact_dir / 'check_kusu_services.out'
        if self._return_code != 0:
            filename = artifact_dir / 'check_kusu_services.err'
        UATHelper.generate_file_from_lines(filename, [self.status + '\n'])
