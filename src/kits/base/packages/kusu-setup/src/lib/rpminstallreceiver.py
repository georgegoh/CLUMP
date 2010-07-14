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

FIND_COMMAND = 'find -P %s -name kit-base*.rpm'

class RpmInstallReceiver:

    def __init__(self):
        pass

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

    def verifyKusuDistroSupported(self, basedir):
        kit_rpm_path = self.retrieveKitRPM(basedir)
        if path(kit_rpm_path).exists():
            kit_rpm = RPM(kit_rpm_path)
            kops = KitOps()
            kit, component = kops.getKitRPMInfo(kit_rpm)
            return self.verifyRPMDistro(component)
        else:
            print "kit-base RPM cannot be found. Please check the location of KUSU RPMS."
            return False

    def retrieveKitRPM(self, basedir):
        basedir = path(basedir)
        if basedir.exists():
            cmd = FIND_COMMAND % basedir
            fCmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            out, err = fCmd.communicate()
            if out:
                return out.rstrip('\n')

    def verifyRPMDistro(self, kit_info_component):
        if kit_info_component[0]['name'] == 'component-base-installer':
            base_os = kit_info_component[0]['os']
            base_os_name = base_os[0]['name']
            installer = InstallerInitReceiver()
            if installer.distroName.lower() in osfamily.getOSNames('rhelfamily') and base_os_name == 'rhelfamily':
                return True
        return False
