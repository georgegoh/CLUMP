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

import os
import sys
import re

try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from path import path
from optparse import OptionParser

from kusu.uat import UATPluginBase, UATHelper


PING_COMMAND = '/bin/ping'
DEFAULT_PING_DEADLINE_SECONDS = '10'
DEFAULT_PACKET_COUNT = '5'

class CheckPing(UATPluginBase):

    def __init__(self, args=None):
        super(CheckPing, self).__init__()
        self._logger = args['logger']
        self.usage = """usage: check_ping [options] destination"""
        self._destination = None
        self._deadline = DEFAULT_PING_DEADLINE_SECONDS
        self._packet_count = DEFAULT_PACKET_COUNT

        self._cmd_out = []
        self._cmd_err = []
        self._cmd_returncode = 0

    def pre_check(self):
        pass

    def post_check(self):
        pass

    def node_setup(self, node):
        pass

    def node_teardown (self, node):
        pass

    def run(self, args):
        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])

        if len(remaining_args) != 1:  # require only one destination
            parser.print_usage(file=sys.stderr)
            sys.stderr.write('Please provide destination\n')
            self._logger.info('Please provide destination\n')
            return 1

        self._destination = remaining_args[0]

        if options.deadline is not None:
            self._deadline = options.deadline
        if options.packet_count is not None:
            self._packet_count = options.packet_count

        returncode = self._run()
        self.status = self._generate_status()
        return returncode, self.status

    def _configure_options(self):
        """Sets up command line options"""
        parser = OptionParser(usage=self.usage)
        parser.add_option('-w', '--deadline',
		                  help='Specify a timeout, in seconds, before ping exits \
						  regardless of how many packets have been sent or \
						  received.')
        parser.add_option('-c', '--packet-count',
		                  help='Stop after sending count ECHO_REQUEST packets. \
		                  with deadline option, ping waits for count \
						  ECHO_REPLY packets, until the timeout expires.')
        return parser

    def _run(self):
        cmd = self._build_ping_command()
        check_pingP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check_pingP.wait()
        self._cmd_out = check_pingP.stdout.readlines()
        self._cmd_err = check_pingP.stderr.readlines()
        return check_pingP.returncode

    def _build_ping_command(self):
        return [PING_COMMAND,
                '-n',                       # numeric output (no hostname lookup)
                '-U',                       # print user-to-user time
                '-w', self._deadline,       # deadline in seconds
                '-c', self._packet_count,   # number of packets to send
                self._destination]          # remote host to ping

    def _generate_status(self):
        if self._cmd_out:
            return self._generate_status_from_cmd_out()
        elif self._cmd_err:
            return self._generate_status_from_cmd_err()
        return ''

    def _generate_status_from_cmd_out(self):
        # Sample ping output:
        #
        # PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
        # 64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.763 ms
        # 64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.057 ms
        # 64 bytes from 127.0.0.1: icmp_seq=3 ttl=64 time=0.053 ms
        # 64 bytes from 127.0.0.1: icmp_seq=4 ttl=64 time=0.081 ms
        # 64 bytes from 127.0.0.1: icmp_seq=5 ttl=64 time=0.046 ms
        #
        # --- 127.0.0.1 ping statistics ---
        # 5 packets transmitted, 5 received, 0% packet loss, time 4001ms
        # rtt min/avg/max/mdev = 0.046/0.200/0.763/0.281 ms
        #
        # So the last line (_cmd_out[-1]) contains round-trip time information,
        # while the second-to-last line (_cmd_out[-2]) contains packet loss
        # information. Regular expressions extract what we care about.
        packet_loss_line = self._cmd_out[-2]
        m = re.compile('.* (\d{1,3})% packet loss.*').match(packet_loss_line)
        status = "%s%% packet loss" % m.groups()[0]

        # In cases where the remote host times out or similar, the last line is
        # blank, so the return value of re.match() is None. We extract the
        # average round-trip time.
        rtt_line = self._cmd_out[-1]
        m = re.compile('.* = \d+.\d{3}/(\d+.\d{3}).*').match(rtt_line)
        if m is not None:
            status += ", %sms RTA" % m.groups()[0]
        return status

    def _generate_status_from_cmd_err(self):
        return self._cmd_err[0].strip()

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._destination / 'check_ping.out'
            UATHelper.generate_file_from_lines(filename, [self.status + '\n'] + self._cmd_out)
        if self._cmd_err:
            filename = artifact_dir / self._destination / 'check_ping.err'
            UATHelper.generate_file_from_lines(filename, [self.status + '\n'] + self._cmd_err)

