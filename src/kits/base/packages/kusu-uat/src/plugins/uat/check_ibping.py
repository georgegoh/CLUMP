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
import time
from sets import Set

try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from path import path
from kusu.core.database import DB
from optparse import OptionParser

from kusu.uat import UATPluginBase, UATHelper

IBPING_HOST_FILE = path(os.environ.get("KUSU_ROOT", "/opt/kusu")) / 'etc' / '.ibping_host'

PDSH_COMMAND = '/usr/bin/pdsh'
IBPING_COMMAND = '/usr/sbin/ibping'

DEFAULT_PING_DEADLINE = '10'   # seconds
DEFAULT_PACKET_COUNT = '5'

os.putenv('PDSH_SSH_ARGS_APPEND', '-o PasswordAuthentication=no -o ConnectTimeout=10 -o PubkeyAuthentication=yes')

class CheckIBPing(UATPluginBase):
    def __init__(self, args=None):
        super(CheckIBPing, self).__init__()
        self._logger = args['logger']
        self._db = args['db']
        self._usage = """usage: check_ibping [options] destination"""

        self._destination = None
        self._deadline = DEFAULT_PING_DEADLINE
        self._packet_count = DEFAULT_PACKET_COUNT

        self._ibping_host = ''
        self._destination_ibGUID = ''

        self._cmd_out = []
        self._cmd_err = []
        self._cmd_returncode = 0

    def _configure_options(self):
        """Sets up command line options"""
        parser = OptionParser(usage=self._usage)
        parser.add_option('-w', '--deadline')
        parser.add_option('-c', '--packet-count')
        return parser

    def _is_node_ib_active(self, node):
        # Run ibstatus command remotely using pdsh
        cmd = [PDSH_COMMAND, '-w', node, 'ibstatus']
        check_ibstatusP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check_ibstatusP.wait()

        out = check_ibstatusP.stdout.readlines()
        err = check_ibstatusP.stderr.readlines()

        # Check error stream (shows blurb if non-zero return code on the remote host)
        if check_ibstatusP.returncode != 0 or err:
            return False

        # Strip out pdsh artifacts
        lines = [line.strip('%s: ' % node).strip() for line in out]

        # Search for the 'active' state lines
        state_lines_check = [line for line in lines if line.startswith('state:') and line.endswith('ACTIVE')]

        if state_lines_check:
            return True
        else:
            return False

    def _find_ibping_host(self):
        # Check what nodes belong to those nodegroups
        ib_nodes = [node.name for ng in ib_associated_ngs for node in ng.nodes if node.name != self._destination]

        # Check if an active ibping host is already known
        ibping_nodes = []
        if IBPING_HOST_FILE.isfile():
            ibping_nodes = [line.strip() for line in IBPING_HOST_FILE.lines()]
            ibping_nodes = [node for node in ibping_nodes if node  in ib_nodes]

            for node in ibping_nodes:
                if node != self._destination and self._is_node_ib_active(node):
                    return node

        # No known ibping host is active. Find a new one.
        # Find nodegroups using ib components
        ib_comps = ['component-Mellanox-OFED', 'component-ofed']
        installed_ib_comps = [comp for comp in self._db.Components.select() if comp.cname in ib_comps]
        ib_associated_ngs = [ng for ng in self._db.NodeGroups.select() if Set(ng.components) & Set(installed_ib_comps)]

        for node in ib_nodes:
            if self._is_node_ib_active(node):
                # Found an active ibnode. Remember and return its name
                ibping_nodes.append(node)
                IBPING_HOST_FILE.write_lines(ibping_nodes)
                return node

        # Ran through all ibnodes, no ibping host found.
        return None

    def _get_destination_ibGUID(self):
        cmd = [PDSH_COMMAND, '-w', self._destination, 'ibstat']

        ibstatP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ibstatP.wait()

        out = ibstatP.stdout.readlines()
        err = ibstatP.stderr.readlines()
        if err or ibstatP.returncode != 0:
            return None

        # Strip out pdsh artifacts
        lines = [line.strip('%s: ' % self._destination).strip() for line in out]

        pick_next_flag = False
        for line in lines:
            if line == 'State: Active':
                pick_next_flag = True

            elif pick_next_flag and line.startswith('Port GUID:'):
                return line.split(':')[-1].strip()

        # No active port found
        return None

    def _start_remote_ibping_server(self):
        cmd = [PDSH_COMMAND, '-w', self._destination, 'ibping', '-S', '&']
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)

    def _stop_remote_ibping_server(self):
        cmd = [PDSH_COMMAND, '-w', self._destination, 'ps', '-C', 'ibping', '-o', 'pid=', '|', 'xargs', '-e', 'kill', '-9']
        kill_ibpingP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        kill_ibpingP.wait()

    def run(self, args):
        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])

        if len(remaining_args) != 1:  # require only one destination
            parser.print_usage(file=sys.stderr)
            self.status = 'Destination not provided by check.'
            self._logger.info('Please provide destination\n')
            return 1, self.status

        self._destination = remaining_args[0]

        if options.deadline is not None:
            self._deadline = options.deadline
        if options.packet_count is not None:
            self._packet_count = options.packet_count

        self._ibping_host = self._find_ibping_host()
        if not self._ibping_host:
            self.status = 'Could not find a host from which to ibping the destination node.'
            return -1, self.status

        self._destination_ibGUID = self._get_destination_ibGUID()
        if not self._destination_ibGUID:
            self.status = 'Could not determine the ib port GUID of the destination node.'
            return -2, self.status

        self._start_remote_ibping_server()

        cmd = self._build_remote_ibping_command()
        check_pingP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check_pingP.wait()

        self._stop_remote_ibping_server()

        self._cmd_out = check_pingP.stdout.readlines()
        self._cmd_err = check_pingP.stderr.readlines()
        self._cmd_returncode = check_pingP.returncode
        self.status = self._generate_status()
        return self._cmd_returncode, self.status

    def _build_remote_ibping_command(self):
        return [PDSH_COMMAND,
                '-w', self._ibping_host,	# host from which ibping is to be run
                IBPING_COMMAND,
                '-t', self._deadline,		# deadline in seconds
                '-c', self._packet_count,	# number of packets to send
                '-G', self._destination_ibGUID]	# ib port GUID of remote host to ping

    def _generate_status(self):
        if self._cmd_out:
            return self._generate_status_from_cmd_out()
        elif self._cmd_err:
            return self._generate_status_from_cmd_err()
        return ''

    def _generate_status_from_cmd_out(self):
        packet_loss_line = self._cmd_out[-2]
        m = re.compile('.* (\d{1,3})% packet loss.*').match(packet_loss_line)
        status = "%s%% packet loss" % m.groups()[0]
        rtt_line = self._cmd_out[-1]
        m = re.compile('.* = \d+.\d{3}/(\d+.\d{3}).*').match(rtt_line)
        if m is not None:
            status += ", %sms RTA" % m.groups()[0]
        return status

    def _generate_status_from_cmd_err(self):
        return self._cmd_err[0].strip()

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._destination / 'check_ibping.out'
            UATHelper.generate_file_from_lines(filename, [self.status + '\n'] + self._cmd_out)
        if self._cmd_err:
            filename = artifact_dir / self._destination / 'check_ibping.err'
            UATHelper.generate_file_from_lines(filename, [self.status + '\n'] + self._cmd_err)
