#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.repoman import repo
from kusu.util.errors import *
from kusu.core import database as db
from path import path
import sqlalchemy as sa

class RepoFactory(object):

    class_dict = { 'fedora' : {'6': repo.Fedora6Repo},
                   'centos' : {'5': repo.Centos5Repo},
                   'rhel'   : {'5': repo.Redhat5Repo} }

    def __init__(self, db, prefix='/'):
        """Creates a RepoFactory.

           Accepts the following arguments:
           prefix: prefix of the root directory, if any
           db: The DB clas object
        """
        self.db = db
        self.prefix = path(prefix)

    def make(self, ngname, reponame):
        """Creates and make a new repository"""
        
        os_name, os_version, os_arch = repo.getOS(self.db, ngname)
        r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
        r.make(ngname, reponame)

        return r

    def makeAll(self):
        """Creates all the repositories that have not been 
           assiocated with nodegroups"""
        pass

    def refresh(self, repoid):
        """Refresh the repository"""
        os_name, os_version, os_arch = repo.getOS(self.db, repoid)
        r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
        r.refresh(repoid)

        return r

    def refreshAll(self):
        """Refresh all the repositories"""
        pass

    def delete(self, repoid):
        """Delete the repository from the database and local disk"""
        
        os_name, os_version, os_arch = repo.getOS(self.db, repoid)
        r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
        r.delete(repoid)
        
        return r

    def snapshot(self, ngname_or_ngid):
        """Makes a snapshot for a nodegroup or nodegroup id"""
        pass

    def snapshotAll(self):
        """Makes snapshots for all nodegroups"""
        pass


    def getRepo(self, repoid_or_reponame):
        pass
