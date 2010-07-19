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
import shutil
from time import sleep

try:
    import subprocess
except:
    from popen5 import subprocess

from kusu.kitops.kitops import KitOps
import kusu.core.database as db
from primitive.core.errors import ModuleException
from primitive.support.util import runCommand
from primitive.system.software import probe as softprobe
import message
from rpminstallreceiver import ZYPPER_SERVICE_ALIAS, KUSU_COMPONENTS

DROP_DB_COMMAND = "PGPASSWORD=%s psql -U postgres -c 'drop database kusudb'"
POSTGRES_DB_COMMAND = ['psql', 'kusudb', 'nobody', '--command', 'select * from appglobals;']
KUSU_RPM_LIST_COMMAND = 'rpm -qa|grep ^kusu-|grep -v kusu-setup'

class CleanupReceiver(object):
    """
       This class performs cleanup/sanitization of environment before
       bootstrap is run or re-run.
    """
    def __init__(self):
        self._need_to_dropdb = False
        self._need_to_remove_depot = False
        self._need_to_remove_rpms = False
        self._dirtyFlag = False

    def hasRPM(self, rpmName):
        outStr, errStr = runCommand("rpm -qai %s" % rpmName)
        if outStr.find(rpmName) >= 0:
            return True
        return False

    def dbIsAvailable(self):

        try:
            runP = subprocess.Popen(POSTGRES_DB_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            runP.communicate()
        except:
            return False

        if runP.returncode:
            return False

        return True

    def _get_pgpasswd(self):
        if os.path.exists("/opt/kusu/etc/pgdb.passwd"):
            try:
                outStr, errStr = runCommand("cat /opt/kusu/etc/pgdb.passwd")
                passwd = outStr.strip()
            except:
                pass

            return passwd
        else:
            return ""

    def detectOldKusu(self):

        dirtyFlag = False

        #Check for presence of /depot
        message.display("Checking for presence of '/depot'")
        if os.path.exists("/depot"):
            dirtyFlag = True
            self._need_to_remove_depot = True
            message.warning("\n'/depot' found")
        else:
            message.success()

        #Check for presence of kusudb
        message.display("Checking for presence of kusudb database")

        if self.dbIsAvailable():
            dirtyFlag = True
            self._need_to_dropdb = True
            message.warning("\nA kusudb database was found")
        else:
            message.success()

        #Check for presence of kusu component-* rpms
        message.display("Checking for presence of Kusu RPMs")

        if self.hasRPM("component-base-installer") or \
                self.hasRPM("component-base-node") or \
                self.hasRPM("component-gnome-desktop"):
            dirtyFlag = True
            self._need_to_remove_rpms = True
            message.warning("\nKusu RPMs was found")
        else:
            message.success()

        self._dirtyFlag = dirtyFlag
        return dirtyFlag

    def os_name(self):
        name, ver, arch = softprobe.OS()
        return name.lower()

    def remove_rpm(self, rpm_name):
        try:
            outStr, errStr = runCommand('rpm -e --nodeps --noscripts %s' % rpm_name)
        except ModuleException:
            pass

    def kusu_rpm_list(self):
        out, err = runCommand(KUSU_RPM_LIST_COMMAND)
        return out.split('\n')

    def cleanup(self):
        """
            This method completely removes all traces of a kusu
            install from the system.
        """
        if self._dirtyFlag:

            #remove all RPMs
            if self._need_to_remove_rpms:
                kusu_components = KUSU_COMPONENTS.split()
                message.display("\nRemoving Kusu component RPMs...")
                for kusu_component in kusu_components:
                    self.remove_rpm(kusu_component)
                message.success()

                message.display("\nRemoving Kusu RPMs...")
                for kusu_rpm in self.kusu_rpm_list():
                    self.remove_rpm(kusu_rpm)
                message.success()

            #drop kusudb
            if self._need_to_dropdb:
                message.display("\nDropping kusudb database...")
                #fetch kusudb password
                try:
                    passwd = self._get_pgpasswd()
                    if passwd != "":
                        outStr, errStr = runCommand(DROP_DB_COMMAND % passwd)
                        message.success()
                    else:
                        message.failure("Not able to retrieve kusudb password. kusudb is not dropped.")

                except Exception , msg:
                    message.failure("Not able to drop kusudb. %s" % msg)

            #remove /depot
            if self._need_to_remove_depot:

                # For SLES, remove the zypper source added by kusu-setup first.
                if self.os_name() in ['sles', 'opensuse', 'suse']:
                    cmd = 'zypper sl | grep %s' % ZYPPER_SERVICE_ALIAS
                    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
                    p.communicate()
                    if p.returncode == 0:
                        runCommand('zypper sd %s' % ZYPPER_SERVICE_ALIAS)

                message.display("\nRemoving '/depot'...")
                try:
                    if os.path.islink('/depot'):
                        realpath = os.path.realpath('/depot')
                        shutil.rmtree(realpath)
                        os.remove('/depot')

                    elif os.path.ismount('/depot'):
                        #remove all kusu subfolders, leaving /depot intact
                        message.display("\n'/depot' is a mountpoint. Only removing kusu subfolders.")

                        for subdir in ['contrib', 'kits', 'repos', 'www']:
                            if os.path.exists('/depot/%s' % subdir):
                                shutil.rmtree('/depot/%s' % subdir)

                    elif os.path.exists('/depot'):
                        shutil.rmtree("/depot")

                    message.success()

                except Exception, msg:
                    message.failure("\nNot able to remove '/depot'. %s" % msg)

