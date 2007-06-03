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

    def make(self, os_name, os_version, os_arch, ngname, reponame):
        """Creates and make a new repository"""
        
        repo = self.class_dict[os_name](os_version, os_arch, self.prefix, self.db)
        repo.make(ngname, reponame)

        return repo

    def refresh(self, repoid):
        """Refresh the repository"""
        os_name, os_version, os_arch = self._getOSName(repoid)
        repo = self.class_dict[os_name](os_version, os_arch, self.prefix, self.db)
        repo.refresh(repoid)

        return repo

    def delete(self, repoid):
        """Delete the repository from the database and local disk"""
        
        os_name, os_version, os_arch = self._getOSName(repoid)
        repo = self.class_dict[os_name](os_version, os_arch, self.prefix, self.db)
        repo.delete(repoid)
        
        return repo

    def _getOSName(self, repoid):
        """Returns OS (name, version, arch) tuple from database 
           based on the repoid"""

        # Do not depend on os type in repo
        session = self.db.createSession()

        kit = session.query(self.db.kits).select_by \
                            (self.db.repos_have_kits.c.kid == self.db.kits.c.kid, \
                             self.db.repos_have_kits.c.repoid == repoid, \
                             self.db.kits.c.isOS)

        # There should only 1 be os kit for a repo. 
        if len(kit) > 1:
            raise RepoOSKitError, 'repoid \'%s\' has more than 1 OS Kit' % repoid 
        else:
            kit = kit[0]
        
        # returns (os_name, os_version, os_arch)
        return kit.rname.split('-') 
   
 
#if __name__ == '__main__':
#    dbs = db.DB('mysql', username='root', db='test') 
#    rfactory = RepoFactory(dbs, '/tmp/ff')
#    rfactory.make('fedora', '6', 'i386', 'installer', 'repo-name')
#    rfactory.refresh(2)
