#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.util.errors import *
from kusu.core import database as db
from path import path
import sqlalchemy as sa

try:
    import subprocess
except:
    from popen5 import subprocess

class BaseRepo(object):

    ngname = None

    def __init__(self, os_version, os_arch, prefix, db):
        self.os_version = os_version
        self.os_arch = os_arch
        self.prefix = prefix
        self.db = db

    def getOSPath(self):
        """Get the OS path for the repository"""

        ###############################################
        # This is not very clean and I don't like it
        ###############################################
        AND = sa.and_(self.db.nodegroups.c.ngid == self.db.ng_has_comp.c.ngid, \
                      self.db.ng_has_comp.c.cid == self.db.components.c.cid, \
                      self.db.components.c.kid == self.db.kits.c.kid, \
                      self.db.kits.c.isOS == True, \
                      self.db.nodegroups.c.ngname == '%s' % self.ngname)

        names = sa.select([self.db.kits.c.rname], AND).execute().fetchall()

        # There should only be 1 OS for a nodegroup
        if len(names) > 1:
            raise RepoOSKitError, 'repoid \'%s\' has more than 1 OS Kit' % repoid 
        else:
            name = names[0]['rname']

        os_name, os_version, os_arch = name.split('-')
        return self.getKitPath(name, os_version)

    def getKitPath(self, name, version):
        """Get the kit path given the name and version"""

        return self.prefix / 'depot' / 'kits' / str(name) / str(version)
        
    def getRepoPath(self, repoid):
        """Returns the repository path"""

        return self.prefix / 'depot' / 'repos' / str(repoid)

        session.close()

    def UpdateDatabase(self, reponame):
        """Update the database with the new repository""" 

        session = self.db.createSession()

        ng = session.query(self.db.nodegroups).select_by(ngname=self.ngname)[0]

        kits = {} 
        for component in ng.components:
            # Store all the kits, uniq them via dictionary
            kits[component.kit.kid] = component.kit

        # Add new repo into table      
        repo = db.Repos(reponame=reponame)
        repo.kits = kits.values()
        session.save(repo)
        session.flush()
        
        # Update nodegroup with the new repoid
        ng.repoid = repo.repoid
        session.save_or_update(ng)
        session.flush()

        session.close()

        self.repoid = repo.repoid
        self.repo_path = self.getRepoPath(self.repoid)

    def clean(self):
        """Remove the repository from local disk"""

        if not hasattr(self, repo_path):
            raise RepoNotCreatedError

        elif not self.repo_path.exists():
            raise RepoNotFoundError

        else:
            path.rmtree(self.repo_path)

    def make(self, ngname, reponame=None):
        """makes the repository"""
        raise NotImplementedError

    def refresh(self):
        """refresh the repository"""
        raise NotImplementedError

    def delete(self):
        """delete the repository from disk and database"""
        raise NotImplementedError

    def verify(self):
        """verify the repository"""
        raise NotImplementedError

    def copyKitsPackages(self):
        """copy the kits packages to the repository"""
        raise NotImplementedError

    def copyRamDisk(self):
        """copy the initrd/kernel/stage2.img/etc to the repository"""
        raise NotImplementedError

    def makeMetaInfo(self):
        """makes the meta data for the repository"""
        raise NotImplementedError

    def makeRepoDirs(self):
        """creates the necessary repository directories"""
        raise NotImplementedError

        
class FedoraRepo(BaseRepo):
    def __init__(self, os_version, os_arch, prefix, db):
        BaseRepo.__init__(self, os_version, os_arch, prefix, db)
        
        # Need to use a common lib later, maybe boot-media-tool
        self.dirlayout = {}
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Fedora/RPMS'
        self.dirlayout['basedir'] = 'Fedora/base'

    def make(self, ngname, reponame=None):
        self.ngname = ngname
        self.os_path = self.getOSPath()

        # Really fedora
        if not reponame:
            reponame='fedora-%s-%s' % (self.os_version, self.os_arch)
        self.UpdateDatabase(reponame)
        self.makeRepoDirs()
        self.copyOSKit()
        self.copyKitsPackages()
        self.copyRamDisk()
        self.makeComps()
        self.makeMetaInfo()
        self.verify()

        return self.repo_path

    def refresh(self, repoid):
        #self.clean()
        #self.makeRepoDirs()
        #self.copyOSKit()
        #self.copyKitsPackages()
        #self.copyRamDisk()
        #self.makeComps()
        #self.makeMetaInfo()
        #self.verify()
        pass

    def copyKitsPackages(self):
        session = self.db.createSession()

        # Need a better method for this
        kits = session.query(self.db.kits).select_by \
                             (self.db.repos_have_kits.c.repoid==self.repoid, \
                              self.db.repos_have_kits.c.kid == self.db.kits.c.kid,
                              self.db.kits.c.isOS==False)

        for kit in kits:
            pkgdir = self.getKitPath(kit.rname, kit.version)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir('[!TRANS.TBL]*'):

                dest = self.repo_path / self.dirlayout['rpmsdir'] / file.basename()

                if dest.exists():
                   raise FileAlreadyExistError, '%s already exists' % dest

                file.symlink(dest)

        session.close()

    def copyOSKit(self):
        for key, dir in self.dirlayout.items():
            if key != 'repodatadir':
                for file in (self.os_path / dir).listdir('[!TRANS.TBL]*'):
                    file.symlink(self.repo_path / dir / file.basename())

    def makeRepoDirs(self):
        # Need to move/use a common lib 
        for dir in self.dirlayout.values():
            (self.repo_path / dir).makedirs()

    def copyRamDisk(self):
        pass
        
    def makeComps(self):
        # symlink comps.xml
        repodatadir = self.repo_path / self.dirlayout['repodatadir']
        self.comps_file = repodatadir / 'comps.xml'

        (self.os_path / self.dirlayout['repodatadir'] / 'comps.xml').symlink \
         (self.comps_file)

        
    def makeMetaInfo(self):
        cmd = 'createrepo -g %s %s' % (self.comps_file, self.repo_path)

        try:
            p = subprocess.Popen(cmd,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except: 
            raise CommandFailedToRun, 'createrepo failed'

        if retcode:
            raise RepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

    def verify(self):
        pass

