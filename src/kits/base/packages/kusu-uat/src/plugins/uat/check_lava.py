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

BSUB_COMMAND = '/usr/bin/bsub'
BRUN_COMMAND = '/usr/bin/brun'
BHOSTS_COMMAND = '/usr/bin/bhosts'
BJOBS_COMMAND = '/usr/bin/bjobs'

DEFAULT_TARGET_COMMAND = 'uname -a'

class CheckLava(UATPluginBase):
    def __init__(self, args=None):
        super(CheckLava, self).__init__()
        self._logger = args['logger']
        self._db = args['db']
        self._usage = """usage: check_lava [options] target_host"""

        self._destination = None
        self._target_cmd = DEFAULT_TARGET_COMMAND

        self._cluster_master = ''

        self._cmd_out = []
        self._cmd_err = []
        self._cmd_returncode = 0

    def _configure_options(self):
        """Sets up command line options"""
        parser = OptionParser(usage=self._usage)
        parser.add_option('--target_job', help='Specify the shell command to \
                          be scheduled on the target host.')
        return parser

    def _run_cmd(self, cmd):
        cmdP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmdP.wait()

        out = cmdP.stdout.readlines()
        err = cmdP.stderr.readlines()

        return out, err, cmdP.returncode

    def _mod_user_login_script(self, user, script):
        cmd = ['/usr/sbin/usermod', '-s', script, user]
        out, err, ret_code = self._run_cmd(cmd)

        if ret_code != 0 or err:
            return False

        return True

    def _is_lava_node_avail(self):
        cmd = [BHOSTS_COMMAND, self._destination]
        out, err, ret_code = self._run_cmd(cmd)

        if ret_code != 0 or err:
            return False

        status_line = out[1]
        parts = [part for part in status_line.split(' ') if part]
        status = parts[1]
        if status == 'ok':
            return True
        return False

    def run(self, args):
        parser = self._configure_options()
        options, remaining_args = parser.parse_args(args[1:])

        if len(remaining_args) != 1:  # require only one destination
            parser.print_usage(file=sys.stderr)
            sys.stderr.write('Please provide a target host\n')
            return 1, 'Target host not provided'

        self._destination = remaining_args[0]

        if options.target_job is not None:
            self._target_cmd = options.target_job

        if not self._mod_user_login_script('lavaadmin', '/bin/bash'):
            self.status = 'Could not switch to lavaadmin user to run jobs.'
            return -1, self.status

        if not self._is_lava_node_avail():
            self.status = 'Lava is not available on the target host.'
            return -2, self.status

        cmd = self._build_bsub_command()
        check_bsubP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        check_bsubP.wait()

        self._cmd_out = check_bsubP.stdout.readlines()
        self._cmd_err = check_bsubP.stderr.readlines()
        self._cmd_returncode = check_bsubP.returncode
        self.status = self._generate_status()
        return self._cmd_returncode, self.status

    def _build_bsub_command(self):
        return 'su lavaadmin -c ' \
               '"%s -I -q priority -m %s %s"' % \
               (BSUB_COMMAND,
                self._destination,                # destination node name for bsub command
                self._target_cmd)                 # target command to be run on destination node

    def _generate_status(self):
        if self._cmd_out:
            return self._generate_status_from_cmd_out()
        if self._cmd_err:
            return self._generate_status_from_cmd_err()
        return ''

    def _generate_status_from_cmd_out(self):
        submit_line = self._cmd_out[0]
        m = re.compile('^Job <(\d{3,4})> .*').match(submit_line)
        status = "Job id %s submitted" % m.groups()[0]
        return status

    def _generate_status_from_cmd_err(self):
        if self._cmd_returncode != 0:
            return self._cmd_err[0].strip()
        return ''

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._destination / 'check_ping.out'
            UATHelper.generate_file_from_lines(filename, '\n'.join(self._cmd_out))
        if self._cmd_err:
            filename = artifact_dir / self._destination / 'check_ping.err'
            UATHelper.generate_file_from_lines(filename, '\n'.join(self._cmd_err))
