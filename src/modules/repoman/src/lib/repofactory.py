#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.repoman import repo
from kusu.util.errors import *
from kusu.core import database as db
from path import path
import sqlalchemy as sa

class RepoFactory(object):

    class_dict = { 'fedora' : repo.FedoraRepo }

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
        
        name, os_name, os_version, os_arch = repo.getOS(self.db, ngname)
        r = self.class_dict[os_name](os_version, os_arch, self.prefix, self.db)
        r.make(ngname, reponame)

        return r

    def makeAll(self):
        """Creates all the repositories that have not been 
           assiocated with nodegroups"""
        pass

    def refresh(self, repoid):
        """Refresh the repository"""
        name, os_name, os_version, os_arch = repo.getOS(self.db, repoid)
        r = self.class_dict[os_name](os_version, os_arch, self.prefix, self.db)
        r.refresh(repoid)

        return r

    def refreshAll(self):
        """Refresh all the repositories"""
        pass

    def delete(self, repoid):
        """Delete the repository from the database and local disk"""
        
        os_name, os_version, os_arch = repo.getOS(self.db, repoid)
        r = self.class_dict[os_name](os_version, os_arch, self.prefix, self.db)
        r.delete(repoid)
        
        return r

    def getRepo(self, key):
        pass
 
#if __name__ == '__main__':
#    dbs = db.DB('mysql', username='root', db='test') 
#    rfactory = RepoFactory(dbs, '/tmp/ff')
#    rfactory.make('installer', 'repo-name')
#    rfactory.refresh(2)
