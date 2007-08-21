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

    class_dict = { 'fedora' : {'6': repo.Fedora6Repo,
                               '7': repo.Fedora7Repo},
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
            raise InvalidArguments, 'More than 1 argument specified'
        
        if kwargs.has_key('ngname'):
            return self._refreshNgname(kwargs['ngname'])
        elif kwargs.has_key('ngtype'):
            return self._refreshNgtype(kwargs['ngtype'])
        else:
            raise InvalidArguments, 'Invalid arguments keyword'

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

        ng_kits = tools.getKits(self.db, ngname)
        ng_kits.sort()

        repos = self.db.Repos.select()
        for repo in repos:
            if len(repo.kits) == len(ng_kits) and \
               sorted(repo.kits) == ng_kits:
                return repo.repoid
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

            # An existing repo can be used
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
            
            # No existing repo can be used 
            # But since only 1 ng, the repo belongs
            # to the ng
            else:
                repo = self.db.Repos.select_by(repoid = oldRepoID)[0]
                kits = tools.getKits(self.db, ng.ngname) 
                repo.kits = kits
                repo.save()
                repo.flush()
                
                os_name, os_version, os_arch = tools.getOS(self.db, oldRepoID)
                r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
                r.test = self.test
                r = r.refresh(oldRepoID)

        else:

            ngs = [ng for ng in ngs if ng.ngname != ngname]

            # If all nodegroups with this repoid uses the same kits, we 
            # can simply update the repo with the kits and refresh
            ngKits = sorted(tools.getKits(self.db, ngname))
            simpleRefresh = True
            for ng in ngs:
                kits = sorted(tools.getKits(self.db, ng.ngname))

                if len(kits) != len(ngKits) or \
                   kits != ngKits:
                    simpleRefresh = False
                    break
             
            if simpleRefresh:
                    repo = self.db.Repos.select_by(repoid = oldRepoID)[0]
                    repo.kits = ngKits
                    repo.save()
                    repo.flush()

                    os_name, os_version, os_arch = tools.getOS(self.db, oldRepoID)
                    r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
                    r.test = self.test
                    r = r.refresh(oldRepoID)

            else:
                repoid = self.getBestRepo(ngname)
                
                if repoid:
                    ng = self.db.NodeGroups.select_by(ngname = ngname)[0]
                    ng.repoid = repoid
                    ng.save()
                    ng.flush()
                    
                    os_name, os_version, os_arch = tools.getOS(self.db, repoid)
                    r = self.class_dict[os_name][os_version](os_arch, self.prefix, self.db)
                    r.test = self.test
                    r = r.refresh(repoid)

                else:
                    ng = self.db.NodeGroups.select_by(ngname = ngname)[0]
                    ng.repoid = None
                    ng.save()
                    ng.flush()
                    r = self.make(ngname)

        if tools.repoExists(self.db, oldRepoID) and \
           not tools.repoInUse(self.db, oldRepoID):
            self.delete(oldRepoID)

        return r
       
