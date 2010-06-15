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

try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from kusu.uat import UATPluginBase, UATHelper

usage = """usage: check_cfmd remote_host"""
SSH_COMMAND = '/usr/bin/ssh'
SSH_FAILURE_EXIT_STATUS = 255
DEFAULT_SSH_CONNECT_TIMEOUT_SECONDS = '10'

# The desired result is a command as follows:
# $ ssh compute-00-00 -o ConnectTimeout=10 -o PasswordAuthentication=no -o PubkeyAuthentication=yes ps aux | grep [c]fmd
# ConnectTimeout: we don't want to wait the default TCP timeout (3 minutes?)
#                 should the remote host be unreachable
# PasswordAuthentication: we disable password authentication as we won't be
#                         redirecting any input and we don't want the process
#                         to hang
# PubkeyAuthentication: we make sure that public key authentication is enabled
#                       for this connection
SSH_COMMAND_OPTIONS = ['-o', 'ConnectTimeout=10', '-o', 'PasswordAuthentication=no', '-o', 'PubkeyAuthentication=yes']
PS_COMMAND = ['ps', '-eF']
GREP_COMMAND = ['grep', '[/]opt/kusu/sbin/cfmd']


class CheckCfmd(UATPluginBase):

    def __init__(self, args=None):
        super(CheckCfmd, self).__init__()
        self._logger = args['logger']
        self._remote_host = None
        self._cmd_out = []
        self._cmd_err = []
        self._cmd_returncode = 0

    def pre_check(self):
        self._logger.info("CFMD at setup")

    def post_check(self):
        self._logger.info("CFMD at teardown")

    def node_setup(self, node):
        self._logger.info("CFMD setting up node: %s" % node)

    def node_teardown(self, node):
        self._logger.info("CFMD at node teardown : %s " % node)

    def run(self, args):
        if len(args) != 2:  # require only one remote host
            sys.stderr.write(usage)
            sys.stderr.write('Please provide one remote host\n')
            self._logger.info('Please provide one remote host\n')
            return 1

        self._remote_host = args[1]
        cmd = [SSH_COMMAND, self._remote_host] + SSH_COMMAND_OPTIONS + PS_COMMAND
        sshP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        grepP = subprocess.Popen(GREP_COMMAND, stdin=sshP.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._process_command_results(sshP, grepP)
        self.status = self._generate_status()
        returncode =  self._cmd_returncode
        self._logger.info(self.status + '\n')
        return returncode, self.status

    def _process_command_results(self, sshP, grepP):
        out, err = grepP.communicate()
        if grepP.returncode == 0:
            self._cmd_returncode = grepP.returncode
            self._cmd_out = out.splitlines(True)
        else:
            sshP.poll()  # "generates" the returncode
            if sshP.returncode == SSH_FAILURE_EXIT_STATUS:
                self._cmd_returncode = sshP.returncode
                self._cmd_err = sshP.stderr.readlines()
            else:
                self._cmd_returncode = grepP.returncode
                self._cmd_err = err.splitlines(True)

    def _generate_status(self):
        status = "cfmd running"
        if self._cmd_returncode == SSH_FAILURE_EXIT_STATUS:
            status = "SSH access denied"
        elif self._cmd_returncode != 0:
            status = "cfmd not running"
        return status

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._remote_host / 'check_cfmd.out'
            UATHelper.generate_file_from_lines(filename, [self.status + '\n'] + self._cmd_out)
        if self._cmd_err:
            filename = artifact_dir / self._remote_host / 'check_cfmd.err'
            UATHelper.generate_file_from_lines(filename, [self.status + '\n'] + self._cmd_err)
