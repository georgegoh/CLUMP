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
from kusu.core.database import DB
from optparse import OptionParser

from kusu.uat import UATPluginBase, UATHelper

NSLOOKUP_COMMAND = '/usr/bin/nslookup'

class CheckNSLookup(UATPluginBase):

    def __init__(self, args=None):
        super(CheckNSLookup, self).__init__()
        self._logger = args['logger']
        self._db = args=['db']
        self.usage = """usage: check_nslookup destination"""
        self._destination = None

        self._cmd_out = []
        self._cmd_err = []
        self._returncode = 0
  
    def pre_check(self):
        pass

    def post_check(self):
        pass

    def node_setup(self, node):
        pass     

    def node_teardown (self, node):
        pass

    def run(self, args):
        parser = OptionParser(usage=self.usage)
        options, remaining_args = parser.parse_args(args[1:])

        if len(remaining_args) != 1:  # require only one destination
            parser.print_usage(file=sys.stderr)
            sys.stderr.write('Please provide destination\n')
            self._logger.info('Please provide destination\n')
            return 1, 'Target host not provided'

        self._destination = remaining_args[0]

        self._returncode = self._run()
        self._returncode, self.status = self._generate_status()
        return self._returncode, self.status

    def _run(self):
        cmd = self._build_nslookup_command()
        check_nslookupP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check_nslookupP.wait()
        self._cmd_out = check_nslookupP.stdout.readlines()
        self._cmd_err = check_nslookupP.stderr.readlines()
        return check_nslookupP.returncode

    def _build_nslookup_command(self):
        return [NSLOOKUP_COMMAND, self._destination] # remote host to ping

    def _generate_status(self):
        if self._cmd_out:
            return self._generate_status_from_cmd_out()
        elif self._cmd_err:
            return self._generate_status_from_cmd_err()
        return ''

    def _generate_status_from_cmd_out(self):
        server_line = self._cmd_out[0]
        if not server_line.startswith('Server:'):
            return 1, 'No DNS Servers could be reached.'

        result_line = self._cmd_out[3].strip()
        if result_line.startswith('Name:\t%s' % self._destination):
            address_line = self._cmd_out[4].strip()
            return 0, '%s resolved to %s' % (result_line, address_line)

        else:
            return 1, self._cmd_out[3].strip('* \n')

    def _generate_status_from_cmd_err(self):
        return self._cmd_err[0].strip()

    def generate_output_artifacts(self, artifact_dir):
        if self._cmd_out:
            filename = artifact_dir / self._destination / 'check_nslookup.out'
            UATHelper.generate_file_from_lines(filename, [self.status + '\n'] + self._cmd_out)
        if self._cmd_err:
            filename = artifact_dir / self._destination / 'check_nslookup.err'
            UATHelper.generate_file_from_lines(filename, [self.status + '\n'] + self._cmd_err)
        
