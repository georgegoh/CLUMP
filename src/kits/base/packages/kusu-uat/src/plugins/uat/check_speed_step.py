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
from optparse import OptionParser
import sqlalchemy as sa
try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from kusu.uat import UATPluginBase, UATHelper, ModelSpecs

usage = """check_speedstep_info -w remote_host
           check_speedstep_info -s remote_host"""

SSH_COMMAND = '/usr/bin/ssh'
SSH_FAILURE_EXIT_STATUS = 255
DEFAULT_SSH_CONNECT_TIMEOUT_SECONDS = '10'

# The desired result is a command as follows:
# $ ssh compute-00-00 -o ConnectTimeout=10 -o PasswordAuthentication=no -o PubkeyAuthentication=yes ifconfig | grep
# ConnectTimeout: we don't want to wait the default TCP timeout (3 minutes?)
#                 should the remote host be unreachable
# PasswordAuthentication: we disable password authentication as we won't be
#                         redirecting any input and we don't want the speedstepess
#                         to hang
# PubkeyAuthentication: we make sure that public key authentication is enabled
#                       for this connection
SSH_COMMAND_OPTIONS = ['-o', 'ConnectTimeout=10', '-o', 'PasswordAuthentication=no', '-o', 'PubkeyAuthentication=yes']
GREP_COMMAND = ['grep -P ']
PROC_CPUINFO = '/proc/cpuinfo'
LSMOD_COMMAND = ['lsmod ']

class CheckSpeedStep(UATPluginBase):

    def __init__(self, args=None):
        super(CheckSpeedStep, self).__init__()
        self._logger = args['logger']
        self._db = args['db']
        self._host = None

        self._cmd_out = ''
        self._cmd_err = ''

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
        speedstep = False
        self._cmd_returncode = 0

        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])
        if len(remaining_args) != 1:  # require only one host
            self._cmd_returncode = 1
            parser.print_usage(file = sys.stderr)
            self.status = 'Please provide one host\n'
            self._logger.info('Please provide one host\n')
            return self._cmd_returncode, self.status

        self._host = remaining_args[0]

        if options.spec_file:
            # We give preference to spec file
            spec = ModelSpecs(self._host)
            speedstep = spec.read_config('speedstepessor', 'speedstep', type='boolean')
        elif options.speedstep:
            speedstep = True

        self._cmd_returncode = self._check_speedstep(speedstep)
        if self._cmd_returncode:
           return self._cmd_returncode, self._status

        self._status = "Processor speedstep check passed."
        return self._cmd_returncode, self._status

    def _configure_options(self):
        """Sets up command line options"""

        parser = OptionParser(usage=usage)
        parser.add_option('-w', '--spec-file', action='store_true', dest="spec_file",
                          help='Read specification from the spec file.This option \
                                overrides other options.')
        parser.add_option('-s', '--speedstep', dest="speedstep", action="store_true",
                          help='Speedstep is enabled.')

        return parser

    def _check_speedstep(self, speedstep):
        cmd = [SSH_COMMAND, self._host] + SSH_COMMAND_OPTIONS + LSMOD_COMMAND + ['|'] + GREP_COMMAND + ['p4_clockmod']
        sshP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._cmd_out, self._cmd_err = sshP.communicate()
        if sshP.returncode:
            if speedstep:
                self._status = 'Speedstep check failed %s' % self._cmd_err
                return sshP.returncode
        else:
            if not speedstep:
                self._status = 'Speedstep check failed.'
                return 1
        return 0

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out or self._cmd_returncode == 0:
            filename = artifact_dir / self._host / 'check_speedstep.out'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_out])
        if self._cmd_err or self._cmd_returncode:
            filename = artifact_dir / self._host / 'check_speedstep.err'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_err])
