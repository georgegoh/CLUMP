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

from kusu.uat import UATPluginBase, UATHelper, MyOption

usage = """check_proc_info -w remote_host  
           check_proc_info -n remote_host"""
                  
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
PROC_CPUINFO = '/proc/cpuinfo'
LSMOD_COMMAND = ['lsmod ']

class CheckProcInfo(UATPluginBase):

    def __init__(self, args=None):
        super(CheckProcInfo, self).__init__()
        self._logger = args['logger']
        self._db = args['db'] 
        self._host = None
       
        self._cmd_out = ''
        self._cmd_err = ''
        self._cmd_returncode = 0
        
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
        proc_number = None

        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])
        if len(remaining_args) != 1:  # require only one host
            parser.print_usage(file = sys.stderr)
            self.status = 'Please provide one host\n'
            self._logger.info('Please provide one host\n')
            return 1, self.status

        self._host = remaining_args[0]

        if options.spec_file:
            # We give preference to spec file
            config = UATHelper.get_config_parser(self._host)
            proc_number = UATHelper.read_config(config, 'processor', 'number', type='int') 
        else:
            if options.proc_number:
                proc_number = options.proc_number
 
        if proc_number:
            returncode = self._check_proc_number(proc_number)
            if returncode:
                return returncode, self._status

        self._status = "Processor check passed."
        return 0, self._status

    def _configure_options(self):
        """Sets up command line options"""

        parser = OptionParser(option_class=MyOption, usage=usage)
        parser.add_option('-w', '--spec-file', action='store_true', dest="spec_file",
                          help='Read specification from the spec file.This option \
                                overrides other options.') 
        parser.add_option('-n', '--proc-number', dest='proc_number', type="int",
                          help='Specify the number of processors.') 
        return parser

    def _check_proc_number(self, proc_num):
        grep_num_proc = GREP_COMMAND + ['-c ','\'^processor\s*:\'', ' %s' % PROC_CPUINFO]
        grep_command = GREP_COMMAND + ['%d' % proc_num] 
        cmd = [SSH_COMMAND, self._host] + SSH_COMMAND_OPTIONS + grep_num_proc + ['|'] + grep_command
        sshP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._cmd_out, self._cmd_err = sshP.communicate()
        if sshP.returncode:
            self._status = "Number of processors doesn\'t match: " + self._cmd_err
            return sshP.returncode

        return 0

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._host / 'check_proc_info.out'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_out])
        if self._cmd_err:
            filename = artifact_dir / self._host / 'check_proc_info.err'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_err])
