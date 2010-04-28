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

usage = """check_mem_info -w remote_host  
           check_mem_info -s remote_host"""
                  
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
PROC_MEMINFO = '/proc/meminfo'
FDISK_COMMAND = ['fdisk -l ']

class CheckMemInfo(UATPluginBase):

    def __init__(self, args=None):
        super(CheckMemInfo, self).__init__()
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
        mem_size = None

        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])
        if len(remaining_args) != 1:  # require only one host
            parser.print_usage(file = sys.stderr)
            self._status = 'Please provide one host\n'
            self._logger.info('Please provide one host\n')
            return 1, self._status

        self._host = remaining_args[0]

        if options.spec_file:
            # We give preference to spec file
            config = UATHelper.get_config_parser(self._host)
            mem_size = UATHelper.read_config(config, 'memory', 'size') 
        else:
            if options.mem_size:
                mem_size = options.mem_size

        if mem_size:
            mem_size = UATHelper.convert_to_megabytes(mem_size)
            returncode = self._check_memsize(mem_size)
            if returncode:
                return returncode, self._status

        self._status = "Memory check passed."
        return 0, self._status

    def _configure_options(self):
        """Sets up command line options"""

        parser = OptionParser(option_class=MyOption, usage=usage)
        parser.add_option('-w', '--spec-file', action='store_true', dest="spec_file",
                          help='Read specification from the spec file.This option \
                                overrides other options.') 
        parser.add_option('-s', '--memory', dest='mem_size', type="int",
                          help='Specify the memory size in MBs.')
        return parser

    def _check_memsize(self, mem_size):
        grep_command = GREP_COMMAND + ['\'^MemTotal\s*:\'', ' %s' % PROC_MEMINFO ]
        cmd = [SSH_COMMAND, self._host] + SSH_COMMAND_OPTIONS + grep_command 
        sshP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._cmd_out, self._cmd_err = sshP.communicate()
        if sshP.returncode:
            self._status = "Memory check failed"
            return sshP.returncode
        if self._cmd_out:
            host_memsize = UATHelper.convert_to_megabytes(self._cmd_out.split()[1], self._cmd_out.split()[2])

            diff_size = mem_size - host_memsize
            if diff_size < -20 or diff_size > 20:
                self._status = "Host's memory size is \'%d\' rather than %d" % (host_memsize, mem_size)
                return 1 

        return 0
 
    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._host / 'check_mem_info.out'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_out])
        if self._cmd_err:
            filename = artifact_dir / self._host / 'check_mem_info.err'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + [self._cmd_err])
