#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
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
import struct
import socket
import urllib2
from BaseHTTPServer import BaseHTTPRequestHandler

from kusu.uat import UATPluginBase, UATHelper

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 69
DEFAULT_SOCKET_TIMEOUT_SECONDS = 10

class CheckTFTPD(UATPluginBase):
    def __init__(self, args=None):
        super(CheckTFTPD, self).__init__()
        self._logger = args['logger']
        self._return_code = 0
        self.status = ''
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
        try:
            old_default_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.__socket_timeout)
            buffer=struct.pack("!H10sx5sx7sx3sx", 1, 'pxelinux.0', 'octet', *['blksize','512'])
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind(("", 0))
                s.sendto(buffer, (DEFAULT_HOST, DEFAULT_PORT))

                (recv_buffer, (radd, rport)) = s.recvfrom(1024)
                (opcode,) = struct.unpack("!H", recv_buffer[:2])
                s.close()
            except Exception, e:
                self._return_code = 1
                self.status = str(e)
                return self._return_code, self.status
        finally:
            socket.setdefaulttimeout(old_default_timeout)

        self._return_code, self.status = self._generate_status(opcode)
        return self._return_code, self.status

    def _generate_status(self, opcode, message=''):
        return_code = 0
        status = ''
        #opcodes: 1-RRQ, 2-WRQ, 3-DAT, 4-ACK, 5-ERR, 6-0ACK
        if opcode in [3,4,6]:
            status = "tftp server accessible."
        else:
            return_code = opcode
            status = "tftp server error reported."

        return return_code, status + message.strip()

    def generate_output_artifacts(self, artifact_dir):
        filename = artifact_dir / 'check_tftpd.out'
        if self._return_code != 0:
            filename = artifact_dir / 'check_tftpd.err'
        UATHelper.generate_file_from_lines(filename, [self.status + '\n'])
