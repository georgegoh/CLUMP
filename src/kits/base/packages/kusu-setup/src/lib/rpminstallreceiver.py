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
import time
import tempfile
from path import path
from primitive.support import osfamily
from primitive.support.rpmtool import RPM
from primitive.system.software.dispatcher import Dispatcher
from kusu.kitops.kitops import KitOps
from bootstrap.setup.installerinitreceiver import InstallerInitReceiver

from primitive.system.software import probe as softprobe

try:
    import subprocess
except:
    from popen5 import subprocess

class RpmInstallReceiver(object):

    def _disableIptablesKusurc(self):
        kusurc_dir = path('/etc/rc.kusu.d')
        iptables_kusurc_filename = 'S03KusuIptables.rc.py'
        iptables_kusurc = kusurc_dir / iptables_kusurc_filename
        firstrun_dir = kusurc_dir / 'firstrun'
        if not firstrun_dir.isdir(): firstrun_dir.makedirs()
        iptables_kusurc.move(firstrun_dir)
        for f in kusurc_dir.glob(iptables_kusurc_filename + '*'):
            f.remove()

    def installRPMs(self, repoid):
        """
            Install RPMs from local repository
        """

        name, ver, arch = softprobe.OS()
        distro = name.lower()

        self._repoTemplate = '''[bootstraprepo]
name=BootstrapRepo
baseurl=file://///depot/repos/%s%s
enabled=1
gpgcheck=0
'''
        repoText = self._repoTemplate % (repoid, Dispatcher.get('yum_repo_subdir', ''))

        #generate a tempfile for our yum config
        yum_file = tempfile.NamedTemporaryFile(mode='w')
        yum_file.file.writelines(repoText)
        yum_file.flush()

        yumCmd = subprocess.Popen("yum -c %s -y install component-base-installer component-base-node component-gnome-desktop" % yum_file.name, shell=True, stdout=subprocess.PIPE)
        result, code = yumCmd.communicate()

        yum_file.close()

        #Loop until we have an exit status from YUM
        #Potentially harmful if YUM screws us
        while yumCmd.returncode is None:
            time.sleep(1)
            continue

        if yumCmd.returncode == 0:
            self._disableIptablesKusurc()

        return yumCmd.returncode == 0 #assume success if returncode == 0

