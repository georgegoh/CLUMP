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


def getOS(db, key):
    """Returns OS (rname, name, version, arch) tuple from database 
       based on the repoid or nodegroup name"""

    # Do not depend on os type in repo
    # repoid
    if type(key) in [int, long]: # float/complex not included 
        kit = db.Kits.select_by(db.ReposHaveKits.c.kid == db.Kits.c.kid,
                                db.ReposHaveKits.c.repoid == key,
                                db.Kits.c.isOS)

    # nodegroup name
    elif type(key) == str:
        AND = sa.and_(db.NodeGroups.c.ngid == db.NGHasComp.c.ngid, \
                      db.NGHasComp.c.cid == db.Components.c.cid, \
                      db.Components.c.kid == db.Kits.c.kid, \
                      db.Kits.c.isOS == True, \
                      db.NodeGroups.c.ngname == key)

        kit = sa.select([db.Kits.c.rname, db.Kits.c.version, db.Kits.c.arch], \
                        AND).execute().fetchall()

    else:
        raise TypeError, 'Invalid type for key: %s' % key

    # There should only 1 be os kit for a repo. 
    if len(kit) != 1:
        raise RepoOSKitError, 'repoid \'%s\' has more than 1 OS Kit' % repoid 
    else:
        kit = kit[0]
   
    return (kit.rname, kit.version, kit.arch)

class BaseRepo(object):

    ngname = None
    dirlayout = {}
    repo_path = None
    os_path = None
    repoid = None

    def __init__(self, os_version, os_arch, prefix, db):
        self.os_version = os_version
        self.os_arch = os_arch
        self.prefix = prefix
        self.db = db

    def getRepoID(self, repoid_or_reponame):
        """Get the repoid for the repository"""

        if type(repoid_or_reponame) in [int, long]:
            repo = self.db.Repos.get(repoid_or_reponame)
    
        elif type(repoid_or_reponame) == str:
            repo = self.db.Repos.select_by(reponame=repoid_or_reponame)[0]

        if repo:
            self.repoid = repo.repoid
            return self.repoid
        else:
            return None

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

        ng = self.db.NodeGroups.select_by(ngname=self.ngname)[0]

        kits = {} 
        for component in ng.components:
            # Store all the kits, uniq them via dictionary
            kits[component.kit.kid] = component.kit

        # Add new repo into table      
        repo = self.db.Repos(reponame=reponame)
        repo.kits = kits.values()
        repo.save()
        repo.flush()
        self.repoid = repo.repoid
        
        # Update nodegroup with the new repoid
        ng.repoid = repo.repoid
        ng.save_or_update()
        ng.flush()

        self.repo_path = self.getRepoPath(self.repoid)

    def clean(self, repoid_or_reponame):
        """Remove the repository from local disk"""
        
        if not self.repo_path:
            repoid = self.getRepoID(repoid_or_reponame)

            if not repoid:
                raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame
            else:
                self.repo_path = self.getRepoPath(repoid)
         
        if not self.repo_path.exists():
            raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame
        else:
            self.repo_path.rmtree()

    def make(self, ngname, reponame):
        """makes the repository"""
        raise NotImplementedError

    def refresh(self, repoid_or_reponame):
        """refresh the repository"""
        raise NotImplementedError

    def delete(self, repoid_or_reponame=None):
        """delete the repository from disk and database"""

        repoid = self.getRepoID(repoid_or_reponame)
        if not repoid:
            raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame

        repo_path = self.getRepoPath(repoid)

        # Removes files
        if repo_path.exists():
            repo_path.rmtree()

        # clean up database: repos and repos_have_kit table
        repos_have_kits = self.db.ReposHaveKits.select_by(repoid=repoid)
        repo = self.db.Repos.get(repoid)
        for obj in repos_have_kits + [repo]:
            obj.delete()
            obj.flush()         

    def verify(self):
        """verify the repository"""
        raise NotImplementedError

    def copyKitsPackages(self):
        """copy the kits packages to the repository"""
        raise NotImplementedError
    
    def copyOSKit(self):
        """copy the OS kits packages to the repository"""
        raise NotImplementedError

    def copyRamDisk(self):
        """copy the initrd/kernel/stage2.img/etc to the repository"""
        raise NotImplementedError

    def makeRepoDirs(self):
        """creates the necessary repository directories"""
        raise NotImplementedError

class RedhatYumRepo(BaseRepo):
    """Base Redhat repository class"""

    def __init__(self, os_version, os_arch, prefix, db):
        BaseRepo.__init__(self, os_version, os_arch, prefix, db)
    
    def copyKitsPackages(self):
        # Need a better method for this
        kits = self.db.Kits.select_by(self.db.repos_have_kits.c.repoid==self.repoid,
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

    def copyOSKit(self):

        self.os_path = self.getOSPath()
        
        # Validate OS layout
        for dir in self.dirlayout.values():
            dir = self.os_path / dir
            if not dir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % dir
             
        for key, dir in self.dirlayout.items():
            if key != 'repodatadir':
               for file in (self.os_path / dir).listdir():
                    if not file.isdir() and file.basename() != 'TRANS.TBL':
                        file.symlink(self.repo_path / dir / file.basename())

        discinfo = self.os_path / '.discinfo'
        if discinfo.exists():
            discinfo.symlink(self.repo_path / '.discinfo')

    def makeRepoDirs(self):
        for dir in self.dirlayout.values():
            try:
                (self.repo_path / dir).makedirs()
            except: pass

    def copyRamDisk(self):
        pass
        
    def verify(self):
        pass

    def make(self, ngname, reponame):
        """makes the repository"""

        self.ngname = ngname
        self.reponame = reponame

        self.UpdateDatabase(reponame)
        self.makeRepoDirs()
        self.copyOSKit()
        self.copyKitsPackages()
        self.copyRamDisk()
        self.makeComps()
        self.makeMetaInfo()
        self.verify()

        try:
            self.UpdateDatabase(reponame)
            self.makeRepoDirs()
            self.copyOSKit()
            self.copyKitsPackages()
            self.copyRamDisk()
            self.makeComps()
            self.makeMetaInfo()
            self.verify()
        except Exception, e:
            # Don't use self.delete(), since is unsure state

            if self.repoid: #repo have been inserted into database
                repos_have_kits = self.db.ReposHaveKits.select_by(repoid = self.repoid)
                repo = self.db.Repos.get(self.repoid)
                
                for obj in repos_have_kits + [repo]:
                    obj.delete()
                    obj.flush()         

            if not self.repo_path and self.repo_path.exists():
                self.repo_path.rmtree()

            raise e

        return self

    def refresh(self, repoid_or_reponame):
        """refresh the repository"""

        try:
            self.repoid = self.getRepoID(repoid_or_reponame)
            if not self.repoid:
                raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame

            self.clean(self.repoid)
            self.makeRepoDirs()
            self.copyOSKit()
            self.copyKitsPackages()
            self.copyRamDisk()
            self.makeComps()
            self.makeMetaInfo()
            self.verify()
        except KusuError, e:
            raise e

        return self

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
            raise YumRepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

class Fedora6Repo(RedhatYumRepo):
    def __init__(self, os_version, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, os_version, os_arch, prefix, db)
        
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Fedora/RPMS'
        self.dirlayout['basedir'] = 'Fedora/base'
       
class Centos5Repo(RedhatYumRepo):
    def __init__(self, os_version, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, os_version, os_arch, prefix, db)
        
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'CentOS'
 
class Redhat5Repo(RedhatYumRepo):
    def __init__(self, os_version, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, os_version, os_arch, prefix, db)
        
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['server.rpmsdir'] = 'Server'
        self.dirlayout['cluster.rpmsdir'] = 'Cluster'
        self.dirlayout['clusterstorage.rpmsdir'] = 'ClusterStorage'
        self.dirlayout['vt.rpmsdir'] = 'VT'
        self.dirlayout['server.repodatadir'] = 'Server/repodata'
        self.dirlayout['cluster.repodatadir'] = 'Cluster/repodata'
        self.dirlayout['clusterstorage.repodatadir'] = 'ClusterStorage/repodata'
        self.dirlayout['vt.repodatadir'] = 'VT/repodata'

    def copyKitsPackages(self):
        # Need a better method for this
        kits = self.db.Kits.select_by(self.db.repos_have_kits.c.repoid==self.repoid,
                                      self.db.repos_have_kits.c.kid == self.db.kits.c.kid,
                                      self.db.kits.c.isOS==False)

        for kit in kits:
            pkgdir = self.getKitPath(kit.rname, kit.version, kit.arch)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir():
                if file.basename() != 'TRANS.TBL':
                    dest = self.repo_path / self.dirlayout['server.rpmsdir'] / file.basename()

                    if dest.exists():
                       raise FileAlreadyExistError, '%s already exists' % dest

                    file.symlink(dest)

    def copyOSKit(self):

        self.os_path = self.getOSPath()
        
        # Validate OS layout
        for dir in self.dirlayout.values():
            dir = self.os_path / dir
            if not dir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % dir
             
        for key, dir in self.dirlayout.items():
            if key != 'server.repodatadir':
                for file in (self.os_path / dir).listdir():
                    if not file.isdir() and file.basename() != 'TRANS.TBL':
                        file.symlink(self.repo_path / dir / file.basename())

        discinfo = self.os_path / '.discinfo'
        if discinfo.exists():
            discinfo.symlink(self.repo_path / '.discinfo')

    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        repodatadir = self.repo_path / self.dirlayout['server.repodatadir']
        self.comps_file = repodatadir / 'comps-rhel5-server-core.xml'

        (self.os_path / self.dirlayout['server.repodatadir'] / \
         'comps-rhel5-server-core.xml').symlink(self.comps_file)

    def makeMetaInfo(self):
        """Creates a yum repoistory"""

        cmd = 'createrepo -g %s %s' % (self.comps_file, self.repo_path / 'Server')

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
            raise YumRepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path


  
