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
import os
try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from operator import itemgetter
from setup_errors import KusuProbePluginError
from path import path
import message

DF_COMMAND = 'df -lh '
MOUNT_COMMAND = 'mountpoint '
MINIMUM_DISK_SPACE_REQ = 10240

def convert_to_megabytes(number, pattern=''):
    value = None
    try:
        value = float(number)
    except ValueError:
        if number[-1].upper() == 'K':
            value = float(number[:-1]) / 1024
        elif number[-1].upper() == 'M':
            value = float(number[:-1])
        elif number[-1].upper() == 'G':
            value = float(number[:-1]) * 1024
        elif number[-1].upper == 'T':
            value = float(number[:-1]) * 1024 * 1024
        return value

    if pattern:
        if pattern.upper() == 'K' or pattern.upper() == 'KB':
            value = value / 1024
        elif pattern.upper() == 'G' or pattern.upper() == 'GB':
            value = value * 1024
        elif pattern.upper() == 'T' or pattern.upper() == 'TB':
            value = value * 1024 * 1024

    return value

class DiskSpaceCheckReceiver(object):

    def __init__(self, args=None):
        super(DiskSpaceCheckReceiver, self).__init__()
        self._depot_present = False
        self._partition_dir= {}

    def is_depot_mountpoint(self):

        if not path('/depot').exists():
            return False

        cmd = MOUNT_COMMAND + '/depot'
        sshP = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = sshP.communicate()
        if sshP.returncode:
            return False

        return True

    def is_depot_valid_installdir(self):

        cmd = DF_COMMAND + '/depot'
        sshP = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = sshP.communicate()
        if out:
            self._partition_dir = self._process_df_output(out)
            if len(self._partition_dir) < 1:
                return False

        return True

    def _get_free_disk_space(self):

        if len(self._partition_dir) > 0:
            return self._partition_dir

        cmd = DF_COMMAND
        sshP = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = sshP.communicate()
        if sshP.returncode:
            raise KusuProbePluginError, 'Partition probe failed'

        if out:
            self._partition_dir = self._process_df_output(out)
            return self._partition_dir

    def _process_df_output(self, out):

        partition_dir = {}
        is_physical_part = False
        for line in out.split('\n'):
            if is_physical_part:
                values = line.split()
                if len(values) > 1:
                    free_space = convert_to_megabytes(values[2])
                    if free_space > MINIMUM_DISK_SPACE_REQ:
                        partition_dir[values[4]] = values[2]
                    is_physical_part = False

            if line.startswith('/dev'):
                is_physical_part = True
                values = line.split()
                if len(values) > 1:
                    free_space = convert_to_megabytes(values[3])
                    if free_space > MINIMUM_DISK_SPACE_REQ:
                        partition_dir[values[5]] = values[3]
                    is_physical_part = False

        return sorted(partition_dir.items(), key=itemgetter(1), reverse=True)

    def prepareDepotFolder(self, depot_partition):
        """
            Handle creation of symlinks to /depot before we perform our kit installs
        """
        depot_location = depot_partition[0].strip()
        if depot_location != '/' and depot_location != '/depot':
            try:
                (path(depot_location) / 'depot').rmdir()
            except:
                pass
            (path(depot_location) / 'depot').makedirs()

            symlink_target = ( path(depot_location) / 'depot')
            os.symlink(str(symlink_target), '/depot')

    freeDiskSpace = property(_get_free_disk_space)

