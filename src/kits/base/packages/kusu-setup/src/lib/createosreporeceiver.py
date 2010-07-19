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

sys.path.append('/opt/kusu/bootstrap/lib/python')
sys.path.append('/opt/kusu/bootstrap/primitive/lib/python2.4/site-packages/')

from path import path
from primitive.support.util import runCommand
import kusu.core.database as db
import message

REPOMAN_NEW_REPO_COMMAND = 'kusu-repoman -n -r %s'
REPOMAN_ADD_KIT_COMMAND = 'kusu-repoman -r %s -a -i %s'
REPOMAN_REFRESH_REPO_COMMAND = 'kusu-repoman -u -r %s'

class CreateOSRepoReceiver(object):
    """
    This class creates/initializes the OS repo.
    """
    def __init__(self, db):
        self.__db = db

    def makeRepo(self):
        """ This method updates our temporary DELETEME repo, and creates
            the new repo with id 1000. This new repo must be refreshed.
        """
        os_kit_id =  self.__db.Kits.select_by(self.__db.Kits.c.isOS == True)[0]

        os_kit_info =  self.__db.OS.select_by(self.__db.OS.c.osid == os_kit_id.osid)[0]

        reponame = '%s-%s.%s-%s' % (os_kit_info.name, os_kit_info.major, os_kit_info.minor, os_kit_info.arch)

        repo = self.__db.Repos()
        repo.reponame = reponame
        row = self.__db.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
        masterNode = self.__db.Nodes.select_by(name=row.kvalue)[0]
        repo.installers = ';'.join([nic.ip for nic in masterNode.nics if nic.ip])
        repo.kits = self.__db.Kits.select()

        oskit = self.__db.Kits.select_by(isOS = True)[0]
        oskitname = oskit.rname
        oskitversion = oskit.version
        oskitarch = oskit.arch

        repo.ostype = '%s-%s-%s' % (oskitname, oskitversion, oskitarch)
        repo.save()
        repo.flush()

        location = "/depot/repos/%s" % repo.repoid
        path(location).makedirs()

        repo.repository = location
        repo.save()
        repo.flush()

        ng = self.__db.NodeGroups.select_by(type = 'installer')[0]
        ng.repoid = repo.repoid
        ng.save()
        ng.flush()

        #expose repo_name and repo_id properties
        self.default_repo_name = repo.reponame
        self.default_repo_id = repo.repoid

        # remove our placeholder DELETEME repo
        self.__db.Repos.selectfirst_by(repoid=999).delete()
        self.__db.flush()

        #self.refresh_repo(reponame)

        return True


if __name__ == "__main__":
    cor = CreateOSRepoReceiver()
    cor.create_os_repo()
