#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.repoman import repo, tools
from kusu.util.errors import *
from kusu.core import database as db
from path import path
import sqlalchemy as sa

class RepoFactory(object):

    class_dict = { 'fedora' : {'6': repo.Fedora6Repo},
                   'centos' : {'5': repo.Centos5Repo},
                   'rhel'   : {'5': repo.Redhat5Repo} }

    def __init__(self, db, prefix='/', test=False):
        """Creates a RepoFactory.

           Accepts the following arguments:
           prefix: prefix of the root directory, if any
           db: The DB clas object
        """
        self.db = db
        self.prefix = path(prefix)
        self.test = test

    def make(self, ngname, reponame=None):
        """Creates and make a new repository"""
     
        if not tools.nodeGroupExists(self.db, ngname):
            raise NodeGroupNotFoundError, ngname
 
        if tools.repoForNodeGroupExists(self.db, ngname):
            raise NodeGroupHasRepoAlreadyError, ngname
             
        repoid  = self.getBestRepo(ngname)

        if repoid:
            # Existing repo can be used
            ng = self.db.NodeGroups.select_by(ngname=ngname)[0]
            ng.repoid = repoid
            ng.save()
            ng.flush()
   
            os_name, os_version, os_arch = tools.getOS(self.db, ngname)
            r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
            r.test = self.test

            r.repo_path = r.getRepoPath(repoid)
            r.repoid = repoid
            self.refreshScripts(r)
        else:
            # Make a new repo
            os_name, os_version, os_arch = tools.getOS(self.db, ngname)
            r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
            r.test = self.test
            r.make(ngname)

        return r

    def makeAll(self):
        """Creates all the repositories that have not been 
           assiocated with nodegroups"""
        pass

    #def clean(self, ngname):
    #    pass

    def refresh(self, **kwargs):
        """Refresh the repository"""

        if len(kwargs) != 1:
            raise InvalidArguements, 'More than 1 argument specified'
        
        if kwargs.has_key('ngname'):
            return self._refreshNgname(kwargs['ngname'])
        elif kwargs.has_key('ngtype'):
            return self._refreshNgtype(kwargs['ngtype'])
        else:
            raise InvalidArguements, 'Invalid arguments keyword'

    def refreshAll(self):
        """Refresh all the repositories"""
        pass

    def delete(self, repoid):
        """Delete the repository from the database and local disk"""
    
        if not tools.repoExists(self.db, repoid):
            raise RepoNotCreatedError, repoid

        ngs = self.db.NodeGroups.select_by(repoid = repoid)    

        if ngs:
            raise RepoCannotDeleteError
 
        os_name, os_version, os_arch = tools.getOS(self.db, repoid)
        r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
        r.delete(repoid)
        
        return r

    def snapshot(self, ngname_or_ngid):
        """Makes a snapshot for a nodegroup or nodegroup id"""
        pass

    def snapshotAll(self):
        """Makes snapshots for all nodegroups"""
        pass

    def getRepo(self, repoid):
        """Returns the repo obj for that repo"""

        os_name, os_version, os_arch = tools.getOS(self.db, repoid)
        r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
        r.repoid = repoid
        r.os_path = r.getOSPath()
        r.repo_path = r.getRepoPath()

        return r
 
    def getBestRepo(self, ngname):
        """Get a repo that uses the same set of kits"""

        ngs = self.db.NodeGroups.select_by(sa.not_(self.db.NodeGroups.c.repoid == None))
        repos = {}
        for ng in ngs:
            if ng.ngname == ngname:
                continue #Ignore the ng that you are checking against

            repoid = ng.repoid
            kits = tools.getKits(self.db, ng.ngname)
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
        
        ng_kits = tools.getKits(self.db, ngname)
        ng_kits.sort()

        for repoid, kits in repos.items():
            if len(kits) == len(ng_kits) and \
               kits == ng_kits:
                return repoid

        return None

    def refreshScripts(self, repoObj):
        # Ensure patch files and autoinstall script is generated.
        #
        # This is in the case when the master installer
        # has prepared the repository but the templates are not 
        # available then. This autoinstsall script is needed
        # for compute nodes that are using the same repository
        repoObj.copyKusuNodeInstaller()
        repoObj.makeAutoInstallScript()

    def _refreshNgtype(self, ngtypes=[]):

        repos = {}
        for ngtype in ngtypes:
            ngs = self.db.NodeGroups.select_by(type = ngtype)
            for ng in ngs:
                if ng.repoid:
                    if not repos.has_key(ng.repoid):
                        repos[ng.repoid] = []
                    repos[ng.repoid].append(ng.ngname)

        reposList = []
        for repoid, val in repos.items():
            for ngname in val:
                r = self._refreshNgname(ngname)
                reposList.append(r)

        return reposList

    def _refreshNgname(self, ngname):
        if not tools.nodeGroupExists(self.db, ngname):
            raise NodeGroupNotFoundError, ngname

        if not tools.repoForNodeGroupExists(self.db, ngname):
            raise RepoNotCreatedError, 'repo not created for \'%s\'' % ngname

        repoid = tools.getRepoFromNodeGroup(self.db, ngname)
        oldRepoID = repoid
        ngs = self.db.NodeGroups.select_by(repoid = repoid)

        if len(ngs) == 1:
            ng = ngs[0]

            repoid  = self.getBestRepo(ng.ngname)

            if repoid:
                ng.repoid = repoid
                ng.save()
                ng.flush()
                
                os_name, os_version, os_arch = tools.getOS(self.db, ngname)
                r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
                r.test = self.test

                r.repo_path = r.getRepoPath(repoid)
                r.repoid = repoid
                self.refreshScripts(r)
            else:
                os_name, os_version, os_arch = tools.getOS(self.db, oldRepoID)
                r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
                r.test = self.test
                r = r.refresh(oldRepoID)

        else:
            # Filter out the current ngname, other nodegroups
            # are using the same repo
            ngs = [ng for ng in ngs if ng.ngname != ngname]
            ng = ngs[0] # Take the 1st one, since all using same repo 

            # Determine whether a new repo is needed, i.e.
            # not the same anymore
            oldKits = tools.getKits(self.db, ng.ngname) 
            newKits = tools.getKits(self.db, ngname)

            oldKits.sort()
            newKits.sort()

            if len(oldKits) == len(newKits) and \
               oldKits == newKits:
                # No change

                os_name, os_version, os_arch = tools.getOS(self.db, repoid)
                r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
                r.test = self.test
                r = r.refresh(repoid)

            else:
                # New repo needed or can use another repo.
                ng = self.db.NodeGroups.select_by(ngname = ngname)[0]
                ng.repoid = None
                ng.save()
                ng.flush()
                r = self.make(ngname)

        if tools.repoExists(self.db, oldRepoID) and \
           not tools.repoInUse(self.db, oldRepoID):
            self.delete(oldRepoID)

        return r
       
