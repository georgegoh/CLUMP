#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: supported_os.py 623 2010-04-21 11:36:48Z ankit $
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
import glob
from path import path

try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from primitive.support import osfamily
from setup_errors import KusuProbePluginError

LSB_COMMAND = 'lsb_release '
UNAME_COMMAND = 'uname -i '
GREP_COMMAND = 'grep -P '

def get_short_name(os_name):
    if os_name.lower().startswith('redhat') or os_name.lower().startswith('red hat'):
        return 'rhel'
    elif os_name.lower().startswith('centos'):
        return 'centos'
    elif os_name.lower().startswith('fedora'):
        return 'fedora'
    elif os_name.lower().startswith('suse') or  os_name.lower().startswith('sles'):
        return 'sles'

    return None

def read_file(file, check):
    result = None
    fp = open(file, 'r')
    line = [x for x in fp.readlines() if x.rstrip('\n') != ''][0]

    line_list =  line.split('release')
    if len(line_list) < 2:
        # There is no release tag.
        if check == 'os':
            if line.lower().find('suse') or line.lower().find('sles'):
                return 'sles'
            if line.lower().find('redhat') or line.lower().find('red hat'):
                return 'rhel'
            if line.lower().find('centos'):
                return 'centos'
            if line.lower().find('fedora'):
                return 'fedora'
        elif check == 'release':
            words = line_list[0].split()
            for word in words:
                try:
                    float(word)
                    result = word
                    break
                except:
                    continue

        return result

    if check == 'os':
        result = line_list[0].rstrip()
    if check == 'release':
        result = line_list[1].split()[0]
    return result

class InstallerInitReceiver(object):

    def __init__(self):
        super(InstallerInitReceiver, self).__init__(self)
        self.functions = ['check_issue', 'check_release', 'check_lsb']
        self.distro_name = None
        self.distro_arch = None
        self.distro_release = None

    def check_lsb(self, check):
        """ Use linux standard base utility
            output format for -i:
            Distributor ID: <DISTRONAME>
            output format for -r:
            Release: <RELEASE-NUMBER> """

        if check == 'os':
            cmd = LSB_COMMAND + '-i'
        elif check == 'release':
            cmd = LSB_COMMAND + '-r'
        else:
            return False, None

        run_command = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if run_command.returncode:
            return False, None

        out = run_command.stdout.readlines()
        if out:
            result = out[0].split(':')[1].strip()
            return True, result
        return False, None

    def check_release(self, check):
        file_list = glob.glob('/etc/*-release')
        for file in file_list:
            if not file.startswith('kusu'):
                return True, read_file(file, check)
        return False, None

    def check_issue(self, check):
        file = '/etc/issue'
        if path(file).exists():
            return True, read_file(file, check)
        return False, None

    def run_checks(self, check):
        # Try to discover distro name, version and arch
        for func in self.functions:
            status, result = getattr(self, func)(check)
            if status:
                break
        return result

    def get_distro_name(self):
        os_name = self.run_checks('os')
        if os_name:
            self.distro_name = get_short_name(os_name)
            return self.distro_name
        else:
            raise KusuProbePluginError, "kusu failed to probe the name of the installed Operating System."

    def get_distro_release(self):
        os_version = self.run_checks('release')
        if os_version:
            self.distro_release = os_version
            return self.distro_release
        else:
            raise KusuProbePluginError, "kusu failed to probe the version of the installed Operating System."

    def get_distro_arch(self):
        self.distro_arch = os.uname()[4]
        if not self.distro_arch:
            return False, None

        return self.distro_arch

    distroName = property(get_distro_name)
    distroRelease = property(get_distro_release)
    distroArch = property(get_distro_arch)

if __name__ == '__main__':
    probe_os = InstallerInitReceiver()

