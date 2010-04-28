#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: check_tftpd.py 4742 2010-04-27 06:55:55Z kunalc $
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
import struct
import socket
import urllib2
from BaseHTTPServer import BaseHTTPRequestHandler

from kusu.uat import UATPluginBase, UATHelper

DEFAULT_SOCKET_TIMEOUT_SECONDS = 10

class CheckXserver(UATPluginBase):
    def __init__(self, args=None):
        super(CheckXserver, self).__init__()
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

    def _unpack_next_xauth_value(self, buf=''):
        length, = struct.unpack('>H', buf[:2])
        val = buf[2:2+length]
        return val, length

    def _get_local_Xauthorities(self):
        filename = os.environ.get('XAUTHORITY')
        if filename is None:
            filename = '/root/.Xauthority'

        xauth_entries = []
        try:
            raw = open(filename, 'rb').read()
        except IOError:
            return xauth_entries

        n = 0
        try:
            while n < len(raw):
                family, = struct.unpack('>H', raw[n:n+2])
                n = n + 2

                val_list = [family]
                for i in range(1, 5):
                    val, length = self._unpack_next_xauth_value(raw[n:])
                    n = n + 2 + length
                    val_list.append(val)

                if family == 256:
                    xauth_entries.append(val_list)
        except struct.error:
            pass
        return xauth_entries

    def run(self, args):
        self._return_code = 1
        self.status = 'X server could not be detected.'

        try:
            old_default_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.__socket_timeout)
            authorities = self._get_local_Xauthorities()

            if not authorities:
                self._return_code = 1
                self.status = 'Xauthority not established.'
                return self._return_code, self.status

            for family, addr, disp, name, data in authorities:
                format = '>BxHHHHxx'
                format += '%dsx' % len(name)
                format += 'x'* (4 - (len(name)+1)%4)
                format += '%dsx' % len(data)
                format += 'x'* (4 - (len(data)+1)%4)
                buffer = struct.pack(format, 0x42, 11, 0, len(name), len(data), name, data)

                try:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.connect("/tmp/.X11-unix/X%d" % int(disp))
                    s.send(buffer)
                    self.recv_buffer = s.recv(1024)

                except Exception, e:
                    self._return_code = 1
                    self.status = str(e)
                    s.close()
                    return self._return_code, self.status
                s.close()

                if self.recv_buffer:
                    self._return_code, self.status = self._generate_status(self.recv_buffer)
                    return self._return_code, self.status
        finally:
            socket.setdefaulttimeout(old_default_timeout)

        return self._return_code, self.status

    def _generate_status(self, recv_buffer=''):
        return_code = 0
        status = ''

        try:
            success_code, = struct.unpack('>Bx', recv_buffer[:2])
            #opcodes: 1-Success, 0-Failure
            if success_code == 1:
                status = self._generate_status_from_success(recv_buffer)
            else:
                return_code = 1
                status = self._generate_status_from_failure(recv_buffer)
        except struct.error:
            return 1, 'XServer relpied in wrong format'
        return return_code, status

    def _generate_status_from_failure(self, recv_buffer=''):
        opcode, reason_len, ver_major, ver_minor, data_len = struct.unpack('>BBHHH', recv_buffer[:8])
        reason, = struct.unpack('%dsx'%reason_len + 'x'*(4 - (reason_len+1)%4), recv_buffer[8:])

        return reason

    def _generate_status_from_success(self, recv_buffer=''):
        opcode, ver_major, ver_minor, data_len, release, id_base, id_mask, buf_size, \
        vendor_len, max_request_len, num_screens, num_formats, image_byte_order, bitmap_order, \
        scanline_unit, scanline_pad, min_keycode, max_keycode = struct.unpack('>BxHHHIIIIHHBBBBBBBBxxxx', recv_buffer[:40])

        vendor_pad = (4 - (vendor_len+1)%4)
        pos = 40+vendor_len+1+vendor_pad
        vendor, = struct.unpack('%dsx'%vendor_len + 'x'*vendor_pad, recv_buffer[40:pos])

        end = pos + 8*num_formats
        formats = struct.unpack('>'+'BBBxxxxx'*num_formats, recv_buffer[pos:end])

        pos = end
        end = pos + 30*num_screens
        screens = struct.unpack('>' + 'LLLLLHHHHH'*num_screens, recv_buffer[pos:end])

        return 'Connected to Xserver by vendor: %s' % vendor

    def generate_output_artifacts(self, artifact_dir):
        filename = artifact_dir / 'check_xserver.out'
        if self._return_code != 0:
            filename = artifact_dir / 'check_xserver.err'
        UATHelper.generate_file_from_lines(filename, [self.status + '\n'])
