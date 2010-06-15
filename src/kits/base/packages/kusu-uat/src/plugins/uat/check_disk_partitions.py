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
from optparse import Option, OptionParser
import sqlalchemy as sa
try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from kusu.uat import UATPluginBase, UATHelper, ModelSpecs

usage = """check_disk_partitions remote_host """

SSH_COMMAND = '/usr/bin/ssh'
SSH_FAILURE_EXIT_STATUS = 255
DEFAULT_SSH_CONNECT_TIMEOUT_SECONDS = '10'

# The desired result is a command as follows:
# $ ssh compute-00-00 -o ConnectTimeout=10 -o PasswordAuthentication=no -o PubkeyAuthentication=yes ifconfig | grep
# ConnectTimeout: we don't want to wait the default TCP timeout (3 minutes?)
#                 should the remote host be unreachable
# PasswordAuthentication: we disable password authentication as we won't be
#                         redirecting any input and we don't want the process
#                         to hang
# PubkeyAuthentication: we make sure that public key authentication is enabled
#                       for this connection
SSH_COMMAND_OPTIONS = ['-o', 'ConnectTimeout=10', '-o', 'PasswordAuthentication=no', '-o', 'PubkeyAuthentication=yes']
GREP_COMMAND = ['grep -P ']
DF_COMMAND = ['df -mPh ']

class CheckDiskPartitions(UATPluginBase):

    def __init__(self, args=None):
        super(CheckDiskPartitions, self).__init__()
        self._logger = args['logger']
        self._db = args['db']
        self._host = None

    def pre_check(self):
        pass

    def post_check(self):
        pass

    def node_setup(self, node):
        pass

    def node_teardown(self, node):
        pass

    def run(self, args):
        self._status = ''
        self._cmd_err = ''
        self._cmd_out = ''

        partition_layout = {}
        if len(args) != 2:  # require only one host
            print(usage)
            self._status = 'Please provide a host\n'
            self._logger.info('Please provide a host\n')
            return 1, self._status

        self._host = args[1]
        spec = ModelSpecs(self._host)
        if 'partitions' in spec.parser.sections():
             for option in spec.parser.options('partitions'):
                 partition_layout[option] = spec.parser.get('partitions', option)

        if partition_layout:
            returncode = self._check_partitions(partition_layout)
            if returncode:
                return returncode, self._status

        self._status = "Disk partition check passed."
        return 0, self._status

    def _check_partitions(self, partition_layout):
        for partition, size in partition_layout.iteritems():
            grep_command = GREP_COMMAND + ['\'%s$\'' % partition]
            cmd = [SSH_COMMAND, self._host] + SSH_COMMAND_OPTIONS + DF_COMMAND + ['|'] + grep_command
            sshP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = sshP.communicate()
            if sshP.returncode:
                self._status = "Disk Layout Error." + err
                self._cmd_err = ''
                return sshP.returncode
            if out:
                layout_size = UATHelper.convert_to_megabytes(out.split()[1])
                size = UATHelper.convert_to_megabytes(size)
                diff_size = size - layout_size

                if diff_size > 100 or diff_size < -100:
                    self._status = "Disk layout Error: partition %s size is %d not %d " % (partition, layout_size, size)
                    self._cmd_err = ''
                    return 1
            self._cmd_out += out
        return 0

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._host / 'check_disk_partitions.out'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_out])
        if self._cmd_err:
            filename = artifact_dir / self._host / 'check_disk_partitions.err'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_err])
