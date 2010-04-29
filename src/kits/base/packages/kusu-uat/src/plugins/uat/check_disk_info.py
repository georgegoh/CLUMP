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

usage = """check_disk_info -w remote_host  
           check_disk_info -[n|s] remote_host"""
                  
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
FDISK_COMMAND = ['fdisk -l ']

class CheckDiskInfo(UATPluginBase):

    def __init__(self, args=None):
        super(CheckDiskInfo, self).__init__()
        self._logger = args['logger']
        self._db = args['db'] 
        self._host = None
       
        self._cmd_out = []
        self._cmd_err = []
        
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
        disk_num = None
        disk_size = None
        self._cmd_returncode = 0

        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])
        if len(remaining_args) != 1:  # require only one host
            parser.print_usage(file = sys.stderr)
            self._status = 'Please provide one host\n'
            self._logger.info('Please provide one host\n')
            self._cmd_returncode = 1
            return self._cmd_returncode, self._status

        self._host = remaining_args[0]

        if options.spec_file:
            # We give preference to spec file
            config = UATHelper.get_config_parser(self._host)
            disk_num = UATHelper.read_config(config, 'disk', 'number', type='int')
            disk_size = UATHelper.read_config(config, 'disk', 'size')
        else:
            if options.disk_num:
                disk_num = options.disk_num
            if options.disk_size:
                disk_size = options.disk_size * 1024

        self._cmd_returncode = self._run_fdisk_command()
        if self._cmd_returncode:
            return self._cmd_returncode, self._status
 
        if disk_size:
            disk_size = UATHelper.convert_to_megabytes(disk_size)
            self._cmd_returncode = self._check_disksize(disk_size)
            if self._cmd_returncode:
                return self._cmd_returncode, self._status

        if disk_num:
            self._cmd_returncode = self._check_disknum(disk_num)
            if self._cmd_returncode:
                return self._cmd_returncode, self._status
  
        self._status = "Disk check passed."
        return self._cmd_returncode, self._status

    def _configure_options(self):
        """Sets up command line options"""

        parser = OptionParser(option_class=MyOption, usage=usage)
        parser.add_option('-w', '--spec-file', action='store_true', dest="spec_file",
                          help='Read specification from the spec file.This option \
                                overrides other options.') 
        parser.add_option('-s', '--disk-size', dest='disk_size', type="int",
                          help='Specify the total harddisk size in GBs.')
        parser.add_option('-n', '--disk-num', dest='disk_num', type="int",
                          help='Specify the number of  harddisks.')
        return parser

    def _run_fdisk_command(self):
        grep_command = GREP_COMMAND + ['\'^Disk\s*/dev/(s|h)da:\'']
        cmd = [SSH_COMMAND, self._host] + SSH_COMMAND_OPTIONS + FDISK_COMMAND + ['|'] + grep_command 
        sshP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._cmd_out = sshP.stdout.readlines()
        self._cmd_err = sshP.stdout.readlines()
        if sshP.returncode:
            self._status = 'Harddisk size test failed'
            return sshP.returncode
  

    def _check_disknum(self, disknum):
        if self._cmd_out:
            host_disknum = len(self._cmd_out)
            if host_disknum != disknum:
                self._status = "Number of disk %d on the host is not equal to %d " %(host_disknum, disknum)
                return 1
               
        return 0

    def _check_disksize(self, disk_size):
        host_disksize = 0
        if self._cmd_out:
            for line in self._cmd_out:
                host_disksize += UATHelper.convert_to_megabytes(line.split()[2], line.split()[3][:-1]) 
            diff_size = disk_size - host_disksize
            if diff_size < -200 or diff_size > 200:
                self._status = "Host's disksize is \'%d\' rather than \'%d\'" %(host_disksize, disk_size)
                return 1

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out or self._cmd_returncode==0:
            filename = artifact_dir / self._host / 'check_disk_info.out'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + self._cmd_out)
        if self._cmd_err or self._cmd_returncode:
            filename = artifact_dir / self._host / 'check_disk_info.err'
            UATHelper.generate_file_from_lines(filename, [self._status + '\n'] + self._cmd_err)
