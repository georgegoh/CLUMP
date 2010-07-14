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
from time import sleep
from primitive.support.util import runCommand
from primitive.core.errors import ModuleException
from kusu.kitops.kitops import KitOps
import kusu.core.database as db
import message

#CHECK_DB_COMMAND = "PGPASSWORD=%s psql -U postgres -l | grep kusudb"
DROP_DB_COMMAND = "PGPASSWORD=%s psql -U postgres -c 'drop database kusudb'"
POSTGRES_DB_COMMAND = ['psql', 'kusudb', 'nobody', '--command', 'select * from appglobals;']

KUSU_RPM_LIST = [
'kusu-buildkit',
'kusu-ui',
'kusu-networktool',
'kusu-primitive',
'kusu-uat',
'kusu-net-tool',
'kusu-core',
'kusu-repoman',
'kusu-md5crypt',
'kusu-license-tool',
'kusu-base-installer',
'kusu-kitops',
'kusu-path',
'kusu-appglobals-tool',
'kusu-nodeinstaller',
'kusu-hardware',
'kusu-shell',
'kusu-kit-install',
'kusu-power',
'kusu-base-node',
'kusu-driverpatch',
'kusu-boot',
'kusu-release',
'kusu-util',
'kusu-nodeinstaller-patchfiles'
]

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
            returncode = subprocess.call(POSTGRES_DB_COMMAND)
        except:
            return False

        if returncode:
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
        message.display("Checking for presence of '/depot' folder")
        if os.path.exists("/depot"):
            dirtyFlag = True
            self._need_to_remove_depot = True
            message.warning("\n/depot folder found")
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

    def cleanup(self):
        """
            This method completely removes all traces of a kusu
            install from the system.
        """
        if self._dirtyFlag:
            #remove all RPMs
            if self._need_to_remove_rpms:
                message.display("\nRemoving Kusu component RPMs...")
                outStr, errStr = runCommand("yum -y remove component-base-installer component-base-node component-gnome-desktop")
                message.success()

                message.display("\nRemoving Kusu RPMs...")
                rpmList = ' '.join(KUSU_RPM_LIST)
                outStr, errStr = runCommand("yum -y remove %s" % rpmList)
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

            #remove /depot folder
            if self._need_to_remove_depot:
                message.display("\nRemoving '/depot' folder....")
                import shutil
                try:
                    if os.path.islink('/depot'):
                        realpath = os.path.realpath('/depot')
                        shutil.rmtree(realpath)
                        os.remove('/depot')
                        message.success()

                    elif os.path.ismount('/depot'):
                        #remove all kusu subfolders, leaving /depot intact
                        message.display('\n/depot is a mountpoint. Only removing kusu subfolders.')

                        for subdir in ['contrib', 'kits', 'repos', 'www']:
                            if os.path.exists('/depot/%s' % subdir):
                                shutil.rmtree('/depot/%s' % subdir)

                        message.success()

                    elif os.path.exists('/depot'):
                        shutil.rmtree("/depot")
                        message.success()

                except Exception, msg:
                    message.failure("\nNot able to remove /depot folder. %s" % msg)

