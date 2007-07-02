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

    def __init__(self, db, prefix='/', debug=False):
        """Creates a RepoFactory.

           Accepts the following arguments:
           prefix: prefix of the root directory, if any
           db: The DB clas object
        """
        self.db = db
        self.prefix = path(prefix)
        self.debug = debug

    def make(self, ngname, reponame=None):
        """Creates and make a new repository"""
        
        repoid  = self.getBestRepo(ngname)

        if repoid:
            # Existing repo can be used
            ng = self.db.NodeGroups.select_by(ngname=ngname)[0]
            ng.repoid = repoid
            ng.save()
            ng.flush()

            os_name, os_version, os_arch = repo.getOS(self.db, ngname)
            r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
            r.debug = self.debug

            r.repo_path = r.getRepoPath(repoid)
            r.repoid = repoid     
 
            # Ensure patch files and autoinstall script is generated.
            #
            # This is in the case when the master installer
            # has prepared the repository but the tempaltes are not 
            # available then. This autoinstsall script is needed
            # for compute nodes that are using the same repository
            r.copyKusuNodeInstaller()
            r.makeAutoInstallScript()
        else:
            # Make a new repo
            os_name, os_version, os_arch = repo.getOS(self.db, ngname)
            r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
            r.debug = self.debug
            r.make(ngname)

        return r

    def makeAll(self):
        """Creates all the repositories that have not been 
           assiocated with nodegroups"""
        pass

    #def clean(self, ngname):
    #    pass

    def refresh(self, ngname):
        """Refresh the repository"""

        repoid = self.getRepo(ngname)

        if not repoid:
            raise RepoNotCreatedError, 'repo not created for \'%s\'' % ngname

        ngs = self.db.NodeGroups.select_by(repoid = repoid)

        if ngs:
            # All nodegroups uses the same repo
            ng = ngs[0] 
        else:
            raise KusuError # This should not happen at all 

        if ng.ngname == ngname:
            # Only 1 nodegroup uses that repo, meaning itself
            # Just do a refresh
            
            os_name, os_version, os_arch = repo.getOS(self.db, repoid)
            r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
            r.debug = self.debug
            r = r.refresh(repoid)

        else:
            # Not the same nodegroup
            # Determine whether a new repo is needed, i.e.
            # not the same anymore
            oldKits = repo.getKits(self.db, ng.ngname) 
            newKits = repo.getKits(self.db, ngname)

            oldKits.sort()
            newKits.sort()

            if len(oldKits) == len(newKits) and \
               oldKits == newKits:
                # No change

                os_name, os_version, os_arch = repo.getOS(self.db, repoid)
                r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
                r.debug = self.debug
                r = r.refresh(repoid)

            else:
                # New repo needed
                r = self.make(ngname)

        return r
            
    def refreshAll(self):
        """Refresh all the repositories"""
        pass

    def delete(self, repoid):
        """Delete the repository from the database and local disk"""
    
        ngs = self.db.NodeGroups.select_by(repoid = repoid)    

        if ngs:
            raise RepoCannotDeleteError
 
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


    def getRepo(self, ngname):
        ng = self.db.NodeGroups.select_by(ngname = ngname)

        if ng:
            return ng[0].repoid
        else:
            return None

    def getBestRepo(self, ngname):
        """Get a repo that uses the same set of kits"""

        ngs = self.db.NodeGroups.select_by(sa.not_(self.db.NodeGroups.c.repoid == None))
        repos = {}
        for ng in ngs:
            if ng.ngname == ngname:
                continue #Ignore the ng that you are checking against

            repoid = ng.repoid
            kits = repo.getKits(self.db, ng.ngname)
            kits.sort()

            if repos.has_key(repoid):
                if len(kits) != len(repos[repoid]):
                    raise ReposIntegrityError
                elif kits != repos[repoid]:
                    raise ReposIntegrityError
                else:
                    pass # Do nothing, same
            else:
                repos[repoid] = kits
        
        ng_kits = repo.getKits(self.db, ngname)
        ng_kits.sort()

        for repoid, kits in repos.items():
            if len(kits) == len(ng_kits) and \
               kits == ng_kits:
                return repoid

        return None
 
    def checkNodeGroup(self, ngname):
        return True
