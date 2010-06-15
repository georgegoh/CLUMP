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
import tempfile

try:
    import subprocess
except ImportError:
    from popen5 import subprocess
from optparse import OptionParser

from kusu.core.database import DB
from kusu.uat import UATPluginBase, UATHelper

PDSH_COMMAND = '/usr/bin/pdsh'
MOUNT_COMMAND = '/bin/mount'
UMOUNT_COMMAND = '/bin/umount'
MKTEMP_COMMAND = '/bin/mktemp'
GREP_COMMAND = '/bin/grep'

DEFAULT_EXPORT_DIR = '/depot/shared'

class CheckNFS(UATPluginBase):
    def __init__(self, args=None):
        super(CheckNFS, self).__init__()
        self._logger = args['logger']
        self._db = args['db']
        self.usage = """usage: check_nfs destination"""
        self.destination = None
        self._export_dir = DEFAULT_EXPORT_DIR

        self._returncode = 0
        self.status = ''

    def pre_check(self):
        pass

    def post_check(self):
        pass

    def node_setup(self, node):
        pass

    def node_teardown(self, node):
        pass

    def run(self, args):
        parser = OptionParser(usage=self.usage)
        options, remaining_args = parser.parse_args(args[1:])

        if len(remaining_args) != 1:  # require only destination
            parser.print_usage(file=sys.stderr)
            sys.stderr.write('Please provide destination\n')
            self._logger.info('Destination not provided\n')
            self._returncode = 1
            self.status = 'Target host not provided'
            return self._returncode, self.status

        self.destination = remaining_args[0]

        self._returncode, self.status = self._run()
        return self._returncode, self.status

    def _server_hostname(self):
        return self._db.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue

    def _touch_marker_file(self, dir='/depot/shared'):
        handle, filepath = tempfile.mkstemp(dir=dir)
        atexit.register(os.unlink, filepath)
        return filepath.split('/')[-1]

    def _make_destination_dir(self, base_dir='/tmp'):
        cmd = [PDSH_COMMAND, '-w', self.destination,
               MKTEMP_COMMAND, '-d', '-p', base_dir]

        mktempP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mktempP.wait()
        out = mktempP.stdout.readlines()
        err = mktempP.stderr.readlines()
        ret_code = mktempP.returncode

        if not out or (err and ret_code!=0):
            return ''
        return out[0].split(':')[-1].strip()

    def _umount_destination_dir(self, dir):
        cmd = [PDSH_COMMAND, '-w', self.destination,
               UMOUNT_COMMAND, dir]

        umountP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        umountP.wait()
        out = umountP.stdout.readlines()
        err = umountP.stderr.readlines()
        ret_code = umountP.returncode

        if err or ret_code!=0:
            return False
        return True

    def _verify_destination_mount(self, share, target):
        cmd = [PDSH_COMMAND, '-w', self.destination,
               MOUNT_COMMAND, '|', GREP_COMMAND,
               '"^%s:%s on %s"' % (self._server_hostname(), share, target)]

        check_mountP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check_mountP.wait()
        out = check_mountP.stdout.readlines()
        err = check_mountP.stderr.readlines()
        ret_code = check_mountP.returncode

        if not out or err or ret_code != 0:
            return False
        return True

    def _run(self):
        tmp_dir = self._make_destination_dir()
        if not tmp_dir:
            self._returncode = 1
            self.status = 'Failed to make target directory.'
            return self._returncode, self.status

        cmd = [PDSH_COMMAND, '-w', self.destination, MOUNT_COMMAND,
        '%s:%s' % (self._server_hostname(), self._export_dir), tmp_dir]

        mountP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mountP.wait()
        out = mountP.stdout.readlines()
        err = mountP.stderr.readlines()
        ret_code = mountP.returncode

        if err or ret_code!=0:
            self._returncode = 1
            self.status = err[0].split(':')[-1].strip() or 'NFS mount failed.'
            return self._returncode, self.status

        if not self._verify_destination_mount(share=self._export_dir, target=tmp_dir):
            self._returncode = 1
            self.status = 'NFS mount not established on destination node.'
            return self._returncode, self.status

        self._returncode = 0
        self.status = 'NFS share %s mounted on destination node.' % self._export_dir
        if not self._umount_destination_dir(tmp_dir):
            self.status += ' Warning: Unmount failed on destination node.'

        return self._returncode, self.status

    def generate_output_artifacts(self, artifact_dir):
        filename = artifact_dir / 'check_nfs.out'
        if self._returncode != 0:
            filename = artifact_dir / 'check_nfs.err'
        UATHelper.generate_file_from_lines(filename, [self.status + '\n'])
