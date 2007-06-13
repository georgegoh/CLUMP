#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.util.errors import *
from path import path
import sqlalchemy as sa

try:
    import subprocess
except:
    from popen5 import subprocess


def getOS(db, key):
    """Returns OS (rname, name, version, arch) tuple from database 
       based on the repoid or nodegroup name"""

    # Do not depend on os type in repo
    session = db.createSession()
    
    # repoid
    if type(key) in [int, long]: # float/complex not included 
        kit = session.query(db.kits).select_by \
                            (db.repos_have_kits.c.kid == db.kits.c.kid, \
                             db.repos_have_kits.c.repoid == key, \
                             db.kits.c.isOS)

    # nodegroup name
    elif type(key) == str:
        AND = sa.and_(db.nodegroups.c.ngid == db.ng_has_comp.c.ngid, \
                      db.ng_has_comp.c.cid == db.components.c.cid, \
                      db.components.c.kid == db.kits.c.kid, \
                      db.kits.c.isOS == True, \
                      db.nodegroups.c.ngname == key)

        kit = sa.select([db.kits.c.rname, db.kits.c.version, db.kits.c.arch], \
                        AND).execute().fetchall()

    else:
        session.close()
        raise TypeError, 'Invalid type for key: %s' % key

    session.close()

    # There should only 1 be os kit for a repo. 
    if len(kit) > 1:
        raise RepoOSKitError, 'repoid \'%s\' has more than 1 OS Kit' % repoid 
    else:
        kit = kit[0]
   
    return (kit.rname, kit.version, kit.arch)

class BaseRepo(object):

    ngname = None

    def __init__(self, os_version, os_arch, prefix, db):
        self.os_version = os_version
        self.os_arch = os_arch
        self.prefix = prefix
        self.db = db

    def getOSPath(self):
        """Get the OS path for the repository"""

        os_name, os_version, os_arch = getOS(self.db, self.repoid)
        return self.getKitPath(os_name, os_version, os_arch)

    def getKitPath(self, name, version, arch):
        """Get the kit path given the name and version"""

        return self.prefix / 'depot' / 'kits' / name / version / arch
        
    def getRepoPath(self, repoid):
        """Returns the repository path"""

        return self.prefix / 'depot' / 'repos' / str(repoid)

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

    def make(self, ngname, reponame):
        """makes the repository"""

        self.ngname = ngname
        self.reponame = reponame

        self.UpdateDatabase(reponame)
        self.os_path = self.getOSPath()
        self.makeRepoDirs()
        self.copyOSKit()
        self.copyKitsPackages()
        self.copyRamDisk()
        self.makeComps()
        self.makeMetaInfo()
        self.verify()

        return self

    def refresh(self):
        """refresh the repository"""

        #self.clean()
        #self.makeRepoDirs()
        #self.copyOSKit()
        #self.copyKitsPackages()
        #self.copyRamDisk()
        #self.makeComps()
        #self.makeMetaInfo()
        #self.verify()

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

    def makeRepoDirs(self):
        """creates the necessary repository directories"""
        raise NotImplementedError

class RedhatRepo(object):
    """Base Redhat repository class"""

    def __init__(self):
        pass

    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        repodatadir = self.repo_path / self.dirlayout['repodatadir']
        self.comps_file = repodatadir / 'comps.xml'

        (self.os_path / self.dirlayout['repodatadir'] / 'comps.xml').symlink \
         (self.comps_file)
        
    def makeMetaInfo(self):
        """Creates a yum repoistory"""

        cmd = 'createrepo -g %s %s' % (self.comps_file, self.repo_path)

        try:
            p = subprocess.Popen(cmd,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except: 
            raise CommandFailedToRunError, 'createrepo failed'

        if retcode:
            raise RepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

class FedoraRepo(BaseRepo, RedhatRepo):
    def __init__(self, os_version, os_arch, prefix, db):
        BaseRepo.__init__(self, os_version, os_arch, prefix, db)
        RedhatRepo.__init__(self)
        
        # Need to use a common lib later, maybe boot-media-tool
        self.dirlayout = {}
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Fedora/RPMS'
        self.dirlayout['basedir'] = 'Fedora/base'

    def copyKitsPackages(self):
        session = self.db.createSession()

        # Need a better method for this
        kits = session.query(self.db.kits).select_by \
                             (self.db.repos_have_kits.c.repoid==self.repoid, \
                              self.db.repos_have_kits.c.kid == self.db.kits.c.kid,
                              self.db.kits.c.isOS==False)

        for kit in kits:
            pkgdir = self.getKitPath(kit.rname, kit.version, kit.arch)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir():
                if file.basename() != 'TRANS.TBL':
                    dest = self.repo_path / self.dirlayout['rpmsdir'] / file.basename()

                    if dest.exists():
                       raise FileAlreadyExistError, '%s already exists' % dest

                    file.symlink(dest)

        session.close()

    def copyOSKit(self):
        for key, dir in self.dirlayout.items():
            if key != 'repodatadir':
                for file in (self.os_path / dir).listdir():
                    if file.basename() != 'TRANS.TBL':
                        file.symlink(self.repo_path / dir / file.basename())

    def makeRepoDirs(self):
        # Need to move/use a common lib 
        for dir in self.dirlayout.values():
            (self.repo_path / dir).makedirs()

    def copyRamDisk(self):
        pass
        
    def verify(self):
        pass

class CentosRepo(BaseRepo, RedhatRepo):
    def __init__(self, os_version, os_arch, prefix, db):
        BaseRepo.__init__(self, os_version, os_arch, prefix, db)
        RedhatRepo.__init__(self)
        
        # Need to use a common lib later, maybe boot-media-tool
        self.dirlayout = {}
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Centos/RPMS'
        self.dirlayout['basedir'] = 'Centos/base'

    def copyKitsPackages(self):
        session = self.db.createSession()

        # Need a better method for this
        kits = session.query(self.db.kits).select_by \
                             (self.db.repos_have_kits.c.repoid==self.repoid, \
                              self.db.repos_have_kits.c.kid == self.db.kits.c.kid,
                              self.db.kits.c.isOS==False)

        for kit in kits:
            pkgdir = self.getKitPath(kit.rname, kit.version, kit.arch)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir():
                if file.basename() != 'TRANS.TBL':
                    dest = self.repo_path / self.dirlayout['rpmsdir'] / file.basename()

                    if dest.exists():
                       raise FileAlreadyExistError, '%s already exists' % dest

                    file.symlink(dest)

        session.close()

    def copyOSKit(self):
        for key, dir in self.dirlayout.items():
            if key != 'repodatadir':
                for file in (self.os_path / dir).listdir():
                    if file.basename() != 'TRANS.TBL':
                        file.symlink(self.repo_path / dir / file.basename())

    def makeRepoDirs(self):
        # Need to move/use a common lib 
        for dir in self.dirlayout.values():
            (self.repo_path / dir).makedirs()

    def copyRamDisk(self):
        pass
        
    def verify(self):
        pass


