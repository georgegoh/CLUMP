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
import message

try:
    import subprocess
except:
    from popen5 import subprocess

ZYPPER_CMD = '/usr/bin/zypper --non-interactive --no-gpg-checks'
ZYPPER_SERVICE_ADD_OPTIONS = 'service-add -t YaST'
ZYPPER_SERVICE_ALIAS = 'KusuRepo'
KUSU_COMPONENTS = 'component-base-installer component-base-node component-gnome-desktop'

class RpmInstallReceiver(object):

    def _disableKusurcScript(self, kusurc_filename):
        kusurc_dir = path('/etc/rc.kusu.d')
        kusurc_script = kusurc_dir / kusurc_filename
        if not kusurc_script.exists(): return
        firstrun_dir = kusurc_dir / 'firstrun'
        if not firstrun_dir.isdir(): firstrun_dir.makedirs()
        kusurc_script.move(firstrun_dir)
        for f in kusurc_dir.glob(kusurc_filename + '*'):
            f.remove()

    def installRPMs(self, repoid):
        """
            Install RPMs from local repository
        """

        name, ver, arch = softprobe.OS()
        distro = name.lower()

        if distro in osfamily.getOSNames('rhelfamily') + ['fedora']:
            _install_successful = self._install_rhel_rpms(repoid)
        else:
            _install_successful = self._install_sles_rpms(repoid)

        if _install_successful:
            for script_name in ['S03KusuIptables.rc.py', 'S99KusuXorg.rc.py']:
                self._disableKusurcScript(script_name)

        return _install_successful

    def _install_rhel_rpms(self, repoid):
        self._repoTemplate = '''[bootstraprepo]
name=BootstrapRepo
baseurl=file:///depot/repos/%s%s
enabled=1
gpgcheck=0
'''
        repoText = self._repoTemplate % (repoid, Dispatcher.get('yum_repo_subdir', ''))

        #generate a tempfile for our yum config
        yum_file = tempfile.NamedTemporaryFile(mode='w')
        yum_file.file.writelines(repoText)
        yum_file.flush()

        cmd = "yum -c %s -y install %s" % (yum_file.name, KUSU_COMPONENTS)
        yumCmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        result, err = yumCmd.communicate()

        yum_file.close()

        #Loop until we have an exit status from YUM
        #Potentially harmful if YUM screws us
        while yumCmd.returncode is None:
            time.sleep(1)
            continue

        if yumCmd.returncode:
            message.failure("\nNot able to install RPMs: %s" % err)
            return False

        return yumCmd.returncode == 0 #assume success if returncode == 0

    def _install_sles_rpms(self, repoid):
        repo_dir = "file:///depot/repos/%s" % repoid
        # Add service
        zypper_service_add = "%s %s %s %s" % (ZYPPER_CMD, ZYPPER_SERVICE_ADD_OPTIONS,
                repo_dir, ZYPPER_SERVICE_ALIAS)
        service_add_cmd = subprocess.Popen(zypper_service_add, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = service_add_cmd.communicate()
        if service_add_cmd.returncode:
            message.failure("\nNot able to perform zypper service-add: %s" % err)
            return False

        zypper_install_components = "%s %s" % \
                (Dispatcher.get('zypper_install_cmd', ''), KUSU_COMPONENTS)
        install_cmd = subprocess.Popen(zypper_install_components, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = install_cmd.communicate()

        #Loop until we have an exit status from zypper
        while install_cmd.returncode is None:
            time.sleep(1)
            continue

        if install_cmd.returncode:
            message.failure("\nNot able to install RPMs: %s" % err)
            return False

        return True

