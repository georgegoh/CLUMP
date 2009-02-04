#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.util.errors import *
from kusu.repoman import tools
from kusu.repoman.updates import YumUpdate, RHNUpdate, YouUpdate
from kusu.util import rpmtool
from primitive.repo.yast import YastRepo
from path import path
from Cheetah.Template import Template
import os

try:
    import subprocess
except:
    from popen5 import subprocess

class BaseRepo(object):

    ngname = None
    dirlayout = {}
    repo_path = None
    os_path = None
    repoid = None
    test = False
    ostype = None
    
    def __init__(self, prefix, db, repos_root = '/depot/repos', kits_root = '/depot/kits', contrib_root='/depot/contrib'):
        self.prefix = prefix
        self.db = db
        self.provision = 'KUSU'
        self.repos_root = repos_root
        self.kits_root = kits_root 
        self.contrib_root = contrib_root

        row = self.db.AppGlobals.select_by(kname = 'DEPOT_REPOS_ROOT')
        if row: self.repos_root =  row[0].kvalue
        
        row = self.db.AppGlobals.select_by(kname = 'DEPOT_KITS_ROOT')
        if row: self.kits_root =  row[0].kvalue

        row = self.db.AppGlobals.select_by(kname = 'DEPOT_CONTRIB_ROOT')
        if row: self.contrib_root =  row[0].kvalue

        if self.repos_root[0] == '/': self.repos_root = self.repos_root[1:]
        if self.kits_root[0] == '/': self.kits_root = self.kits_root[1:]
        if self.contrib_root[0] == '/': self.contrib_root = self.contrib_root[1:]

        row = self.db.AppGlobals.select_by(kname = 'PROVISION')
        if row: self.provision =  row[0].kvalue

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

    def getKits(self, ngname):
        """Returns a list of kits for a nodegroup"""
        return tools.getKits(self.db, ngname)

    def getOSPath(self):
        """Get the OS path for the repository"""
    
        repo = self.db.Repos.select_by(repoid = self.repoid)[0]
        return self.getKitPath(repo.oskit.kid)

    def getRepoCachePath(self, repoid = None):
        """Returns the repository cache path"""

        if repoid:
            return self.prefix / 'depot' / 'repos' / '.repocache' / str(repoid)
        else:
            return self.prefix / 'depot' / 'repos' / '.repocache' / str(self.repoid)

    def getContribPath(self):
        """Get the contrib path for the repository"""

        repo = self.db.Repos.select_by(repoid = self.repoid)[0]
        os_name = repo.os.name
        os_major = repo.os.major
        os_arch = repo.os.arch
        
        return self.prefix / self.contrib_root / os_name / os_major / os_arch

    def getKitPath(self, kid):
        """Get the kit path given the name, version and arch"""

        return self.prefix / self.kits_root / str(kid)
       
    def getRepoPath(self, repoid = None):
        """Returns the repository path"""

        if repoid:
            return self.prefix / self.repos_root / str(repoid)
        else:
            return self.prefix / self.repos_root / str(self.repoid)

    def getRepoCachePath(self, repoid = None):
        """Returns the repository cache path"""
        
        if repoid:
            return self.prefix / self.repos_root / '.repocache' / str(repoid)
        else:
            return self.prefix / self.repos_root / '.repocache' / str(self.repoid)

    def getInstallerIP(self):
        """Returns a list of installer ips"""

        row = self.db.AppGlobals.select_by(kname = 'PrimaryInstaller')[0]
        masterNode = self.db.Nodes.select_by(name=row.kvalue)[0]

        return [nic.ip for nic in masterNode.nics if nic.ip]
   
    def UpdateDatabase(self, ngname):

        """Update the database with the new repository""" 
       
        ng = self.db.NodeGroups.select_by(ngname=ngname)[0]
 
        # Add new repo into table      
        repo = self.db.Repos()
        repo.kits = self.getKits(ngname)
        repo.ostype = self.ostype
        repo.installers = ';'.join(self.getInstallerIP())
        repo.save()
        repo.flush()
        
        repo.repository='/' + self.repos_root  + '/%s' % repo.repoid
        repo.save()
        repo.flush()
 
        self.repoid = repo.repoid

        # Update nodegroup with the new repoid
        ng.repoid = repo.repoid
        ng.save_or_update()
        ng.flush()

        self.repo_path = self.getRepoPath(self.repoid)

    def flushCache(self, repoid_or_reponame=None):
        """Remove the repository cache from local disk"""
        
        cache_path = None
        if not self.repo_path:
            repoid = self.getRepoID(repoid_or_reponame)
            
            if not repoid:
                raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame
            else:
                cache_path = self.getRepoCachePath(repoid)
        
        if not self.repo_path.exists():
            raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame
        else:
            cache_path = self.getRepoCachePath()
        
        if cache_path.exists(): cache_path.rmtree()

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

        if not self.repo_path:
            repoid = self.getRepoID(repoid_or_reponame)
        else:
            repoid = self.repoid

        if not repoid:
            raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame

        repo_path = self.getRepoPath(repoid)
        cache_path = self.getRepoCachePath(repoid)

        # Removes files
        if repo_path.exists(): repo_path.rmtree()
        if cache_path.exists(): cache_path.rmtree()

        # clean up database: repos and repos_have_kit table
        repos_have_kits = self.db.ReposHaveKits.select_by(repoid=repoid)
        repo = self.db.Repos.get(repoid)

        for obj in repos_have_kits + [repo]:
            obj.delete()
            obj.flush()

        self.repoid = None
        self.repo_path = None

    def makeAutoInstallScript(self):
        """Make the autoinstall script for the repository"""
        raise NotImplementedError
 
    def verify(self):
        """verify the repository"""
        raise NotImplementedError

    def copyKitsPackages(self):
        """copy the kits packages to the repository"""
        raise NotImplementedError
    
    def copyOSKit(self):
        """copy the OS kits packages to the repository"""
        raise NotImplementedError

    def copyContribPackages(self):
        """copy the contrib packages to the repository"""
        raise NotImplementedError

    def copyRamDisk(self):
        """copy the initrd/kernel/stage2.img/etc to the repository"""
        raise NotImplementedError

    def copyKusuNodeInstaller(self):
        """copy the kusu installer to the repository"""
        NotImplementedError

    def makeRepoDirs(self):
        """creates the necessary repository directories"""
        raise NotImplementedError

    def getPackageFilePath(self, packagename):
        """get the path to a package"""
        raise NotImplementedError
        
    def getKernelPackages(self):
        """get a list of kernel packages"""
        raise NotImplementedError

        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        kpkgs = []

        try:
            root = path(srcPath)
            li = [f for f in root.walkfiles('kernel*rpm')]
            kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    def getPackagesDir(self):
        """get the list of path of packages directories"""
        raise NotImplementedError

    def isInInstaller(self):
    
        flag = self.prefix / 'var' / 'lock' / 'subsys' /  'kusu-installer'
        return flag.exists()

    def hasBaseKit(self):

        repo = self.db.Repos.get(self.repoid)

        if repo:
            for kit in repo.kits:
                if kit.rname == 'base':
                    return True

        return False

    def makeNodeInstallerImage(self):

        cmd = 'genupdatesimg -r %s' % self.repoid
        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except: 
            raise CommandFailedToRunError, 'genupdatesimg failed'

        if retcode:
            raise UpdatesImgNotCreatedError, 'Unable to create updates.img'

        
class SuseYastRepo(BaseRepo):
    """Base yast repository class"""

    def __init__(self, os_name, os_version, os_arch, prefix, db):
        BaseRepo.__init__(self, prefix, db)
    
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch
 
        self.ostype = '%s-%s-%s' % (os_name, os_version, os_arch)

    def getPackagesDir(self):
        
        packagesDir = []
        for k, p in self.dirlayout.iteritems():
            if k.startswith('packagesdir'):
                packagesDir.append(self.repo_path / p)

        return packagesDir

    def copyKitsPackages(self):
        # Need a better method for this
        kits = self.db.Kits.select_by(self.db.ReposHaveKits.c.repoid==self.repoid,
                                      self.db.ReposHaveKits.c.kid == self.db.Kits.c.kid,
                                      self.db.Kits.c.isOS==False)


        rpmPkgs = []
        for d in self.getPackagesDir():
            rpmPkgs.append(rpmtool.getLatestRPM([d]))

        for kit in kits:
            pkgdir = self.getKitPath(kit.kid)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir():
                if file.isfile() and file.basename() not in ['TRANS.TBL', 'kitinfo']:

                    rpm = rpmtool.RPM(str(file))

                    name = rpm.getName()
                    r_arch = rpm.getArch()

                    # We will be replacing the package from the os kit when 
                    # it is provided by a kit
                    for rpmPkg in rpmPkgs:
                        if rpmPkg.has_key(name):
                            if r_arch in ['i386', 'i486', 'i586', 'i686']:
                                for arch in ['i386', 'i486', 'i586', 'i686']:
                                    if rpmPkg[name].has_key(arch):
                                        osFile = rpmPkg[name][arch][0].getFilename()
                                        if osFile.exists(): osFile.remove()

                            else:
                                if rpmPkg[name].has_key(r_arch):
                                    osFile = rpmPkg[name][r_arch][0].getFilename()
                                    if osFile.exists(): osFile.remove()

                    if not (self.repo_path / self.dirlayout['packagesdir.' + r_arch]).exists():
                        (self.repo_path / self.dirlayout['packagesdir.' + r_arch]).makedirs()

                    dest = self.repo_path / self.dirlayout['packagesdir.' + r_arch] / file.basename()

                    if dest.exists(): dest.remove()

                    (dest.parent.relpathto(file)).symlink(dest)

    def copyOSKit(self):

        self.os_path = self.getOSPath()
        
        # Validate OS layout
        for dir in self.dirlayout.values():
            dir = self.os_path / dir
            
            if self.os_arch == 'i386' and (dir.endswith('suse/i386') or dir.endswith('suse/i486')):
                    continue #default suse repo does not have these dir            
            elif self.os_arch == 'x86_64' and (dir.endswith('suse/i386') or dir.endswith('suse/i486') or dir.endswith('suse/i686')):
                    continue #default suse repo does not have these dir

            elif not dir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % dir
             
        for key, dir in self.dirlayout.items():
            if self.os_arch == 'i386' and (dir.endswith('suse/i386') or dir.endswith('suse/i486')):
                continue #default suse repo does not have these dir            
            elif self.os_arch == 'x86_64' and (dir.endswith('suse/i386') or dir.endswith('suse/i486') or dir.endswith('suse/i686')):
                continue #default suse repo does not have these dir            

            for file in (self.os_path / dir).listdir():
                if not file.isdir() and file.basename() not in ['TRANS.TBL', 'kitinfo']:
                        dest = self.repo_path / dir / file.basename()
                        (dest.parent.relpathto(file)).symlink(dest)

        for file in ['content', 'content.asc', 'content.key', 'control.xml', 'directory.yast']:
            file = self.os_path / file
    
            if file.exists(): 
                dest = self.repo_path / file.basename()
                file.copy(dest)
       
        for file in ['root']:
            file = self.os_path / self.dirlayout['imagesdir'] / file

            if file.exists(): 
                dest = self.repo_path / self.dirlayout['imagesdir'] / file.basename()

                if dest.exists():
                    dest.remove()

                file.copy(dest)
 
        for file in (self.os_path / self.dirlayout['descrdir']).glob('packages*'):
            dest = self.repo_path / self.dirlayout['descrdir'] / file.basename()

            if dest.exists():
                dest.remove()

            file.copy(dest)

        for file in self.os_path.glob('gpg-pubkey-*'):
            dest = self.repo_path / file.basename()
            (dest.parent.relpathto(file)).symlink(dest)

        for file in ['media']:
            file = self.os_path / 'media.1' / file
    
            if file.exists(): 
                dest = self.repo_path / 'media.1' / file.basename()

                if dest.exists():
                    dest.remove()

                file.copy(dest)
 
    def copyContribPackages(self):

        if not self.getContribPath().exists():
            return

        contribFiles = self.getContribPath().listdir()

        if not contribFiles:
            return

        rpmPkgs = []
        for d in self.getPackagesDir():
            rpmPkgs.append(rpmtool.getLatestRPM([d]))

        for file in contribFiles:
            if file.basename() not in ['TRANS.TBL', 'kitinfo']:

                rpm = rpmtool.RPM(str(file))

                name = rpm.getName()
                r_arch = rpm.getArch()

                # We will be replacing the package from the os kit when 
                # it is provided by a kit
                for rpmPkg in rpmPkgs:
                    if rpmPkg.has_key(name):
                        if r_arch in ['i386', 'i486', 'i586', 'i686']:
                            for arch in ['i386', 'i486', 'i586', 'i686']:
                                if rpmPkg[name].has_key(arch):
                                    osFile = rpmPkg[name][arch][0].getFilename()
                                    if osFile.exists(): osFile.remove()

                        else:
                            if rpmPkg[name].has_key(r_arch):
                                osFile = rpmPkg[name][r_arch][0].getFilename()
                                if osFile.exists(): osFile.remove()


                if not (self.repo_path / self.dirlayout['packagesdir.' + r_arch]).exists():
                    (self.repo_path / self.dirlayout['packagesdir.' + r_arch]).makedirs()
                   
                dest = self.repo_path / self.dirlayout['packagesdir.' + r_arch] / file.basename()
                (dest.parent.relpathto(file)).symlink(dest)


    def makeRepoDirs(self):
        for dir in self.dirlayout.values():
            try:
                (self.repo_path / dir).makedirs()
            except: pass

    def make(self, ngname):
        """makes the repository"""

        try:
            self.UpdateDatabase(ngname)
            self.makeRepoDirs()
            self.copyOSKit()
            self.copyKitsPackages()
            self.copyContribPackages()
            self.makeMetaInfo()
            self.copyKusuNodeInstaller()
            self.verify()
        except Exception, e:
            # Don't use self.delete(), since is unsure state

            if self.repoid: #repo have been inserted into database
                repos_have_kits = self.db.ReposHaveKits.select_by(repoid = self.repoid)
                repo = self.db.Repos.get(self.repoid)
                
                for obj in repos_have_kits + [repo]:
                    obj.delete()
                    obj.flush()         

            if self.repo_path and self.repo_path.exists():
                self.repo_path.rmtree()

            raise e

        return self

    def refresh(self, repoid_or_reponame):
        """refresh the repository"""

        self.repoid = self.getRepoID(repoid_or_reponame)
        if not self.repoid:
            raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame
       
        try:
            self.clean(self.repoid)
            self.makeRepoDirs()
            self.copyOSKit()
            self.copyKitsPackages()
            self.copyContribPackages()
            self.makeMetaInfo()
            self.copyKusuNodeInstaller()
            self.verify()
        except Exception, e:
            raise e

        return self

    def makeMetaInfo(self):
        
        for p in [self.dirlayout['descrdir']]:
            md5sum = self.repo_path / p / 'MD5SUMS'
            if md5sum.exists():
                md5sum.remove()

        yastRepo = YastRepo(self.repo_path)
        yastRepo.make()
        
        os_name, os_version, os_arch = tools.getOS(self.db, self.repoid)
        yastRepo.writeMedia(vendor='Kusu %s-%s-%s repository' % (os_name, os_version, os_arch))

    def verify(self):
        return True

    def copyKusuNodeInstaller(self):
        """copy the kusu installer to the repository"""

        if self.isInInstaller():
            return

        if self.provision != 'KUSU':
            return

        kusu_root = os.environ.get('KUSU_ROOT', None)

        if not kusu_root:
            # path(/) / path('/opt/kusu') results in path('/opt/kusu'), 
            # since /opt/kusu is absolute
            kusu_root = 'opt/kusu' 

        # Testing mode
        if self.test:
            # ignore $KUSU_ROOT, since prefix is some random temp dir 
            # during testing and updates.img will not be present.
            src = self.prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / \
                  self.os_name / self.os_version / self.os_arch / 'updates.img'
        else:
            src = self.prefix / kusu_root / 'lib' / 'nodeinstaller' / \
                  self.os_name / self.os_version / self.os_arch / 'updates.img'

        if self.hasBaseKit():
            if not src.exists():
                self.makeNodeInstallerImage()
            yastRepo = YastRepo(self.repo_path)
            yastRepo.handleUpdates('file://' + src)
     
    def getKernelPackages(self):
        """get a list of kernel packages"""
        
        pat = re.compile(r'kernel-default[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        kpkgs = []
        try:
            li = [f for f in self.repo_path.walkfiles('kernel*rpm')]
            kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs


class RedhatYumRepo(BaseRepo):
    """Base Redhat repository class"""

    def __init__(self, os_name, os_version, os_arch, prefix, db):
        BaseRepo.__init__(self, prefix, db)
        
        self.yum_dirs = {'default' : ''}
        
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch
 
        self.ostype = '%s-%s-%s' % (os_name, os_version, os_arch)

    def copyKitsPackages(self):
        # Need a better method for this
        kits = self.db.Kits.select_by(self.db.ReposHaveKits.c.repoid==self.repoid,
                                      self.db.ReposHaveKits.c.kid == self.db.Kits.c.kid,
                                      self.db.Kits.c.isOS==False)

        rpmPkgs = rpmtool.getLatestRPM([self.repo_path / self.dirlayout['rpmsdir']])

        for kit in kits:
            pkgdir = self.getKitPath(kit.kid)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir():
                if file.isfile() and file.basename() not in ['TRANS.TBL', 'kitinfo']:
                    rpm = rpmtool.RPM(str(file))

                    name = rpm.getName()
                    arch = rpm.getArch()

                    # We will be replacing the package from the os kit when 
                    # it is provided by a kit
                    if rpmPkgs.has_key(name):
                        if arch in ['i386', 'i486', 'i586', 'i686']:
                            for arch in ['i386', 'i486', 'i586', 'i686']:
                                if rpmPkgs[name].has_key(arch):
                                    osFile = rpmPkgs[name][arch][0].getFilename()
                                    if osFile.exists(): osFile.remove()

                        else:
                            if rpmPkgs[name].has_key(arch):
                                osFile = rpmPkgs[name][arch][0].getFilename()
                                if osFile.exists(): osFile.remove()
                        
                    dest = self.repo_path / self.dirlayout['rpmsdir'] / file.basename()

                    if dest.exists(): dest.remove()
    
                    (dest.parent.relpathto(file)).symlink(dest)

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
                    if not file.isdir() and file.basename() not in ['TRANS.TBL', 'kitinfo']:
                        dest = self.repo_path / dir / file.basename()
                        (dest.parent.relpathto(file)).symlink(dest)


        discinfo = self.os_path / '.discinfo'
        if discinfo.exists():
            dest = self.repo_path / '.discinfo' 
            (dest.parent.relpathto(discinfo)).symlink(dest)

    def copyContribPackages(self):

        if not self.getContribPath().exists():
            return

        contribFiles = self.getContribPath().listdir()

        if not contribFiles:
            return

        rpmPkgs = rpmtool.getLatestRPM([self.repo_path / self.dirlayout['rpmsdir']])

        for file in contribFiles:
            rpm = rpmtool.RPM(str(file))

            name = rpm.getName()
            arch = rpm.getArch()

            # We will be replacing the package from the os kit when 
            # it is provided by a kit
            if rpmPkgs.has_key(name):
                if arch in ['i386', 'i486', 'i586', 'i686']:
                    for arch in ['i386', 'i486', 'i586', 'i686']:
                        if rpmPkgs[name].has_key(arch):
                            osFile = rpmPkgs[name][arch][0].getFilename()
                            if osFile.exists(): osFile.remove()

                else:
                    if rpmPkgs[name].has_key(arch):
                        osFile = rpmPkgs[name][arch][0].getFilename()
                        if osFile.exists(): osFile.remove()
                
            dest = self.repo_path / self.dirlayout['rpmsdir'] / file.basename()

            if dest.exists(): dest.remove()

            (dest.parent.relpathto(file)).symlink(dest)

    def makeRepoDirs(self):
        for dir in self.dirlayout.values():
            try:
                (self.repo_path / dir).makedirs()
            except: pass

    def copyRamDisk(self):
        pass
        
    def copyKusuNodeInstaller(self):
        """copy the kusu installer to the repository"""

        if self.isInInstaller():
            return

        if self.provision != 'KUSU':
            return

        kusu_root = os.environ.get('KUSU_ROOT', None)

        if not kusu_root:
            # path(/) / path('/opt/kusu') results in path('/opt/kusu'), 
            # since /opt/kusu is absolute
            kusu_root = 'opt/kusu' 

        # Testing mode
        if self.test:
            # ignore $KUSU_ROOT, since prefix is some random temp dir 
            # during testing and updates.img will not be present.
            src = self.prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / \
                  self.os_name / self.os_version / self.os_arch / 'updates.img'
        else:
            src = self.prefix / kusu_root / 'lib' / 'nodeinstaller' / \
                  self.os_name / self.os_version / self.os_arch / 'updates.img'
    
        dest = self.repo_path / self.dirlayout['imagesdir'] / 'updates.img'

        if self.hasBaseKit():
            if not src.exists():
                self.makeNodeInstallerImage()
            if not dest.exists():
                (dest.realpath().parent.relpathto(src)).symlink(dest)

    def makeAutoInstallScript(self):

        if self.provision != 'KUSU':
            return

        # kickstart
        kusu_root = os.environ.get('KUSU_ROOT', None)

        if not kusu_root:
            kusu_root = 'opt/kusu' 

        # Testing mode
        if self.test:
            src = self.prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / \
                  self.os_name / self.os_version / self.os_arch / 'ks.cfg.tmpl'
        else:
            src = self.prefix / kusu_root / 'lib' / 'nodeinstaller' / \
                  self.os_name / self.os_version / self.os_arch / 'ks.cfg.tmpl'
 
        if not src.exists():
            return

        row = self.db.AppGlobals.select_by(kname = 'PrimaryInstaller')
        row = row[0]
        masterNode = self.db.Nodes.select_by(name=row.kvalue)[0]
        
        for nic in masterNode.nics:
            # Ignore any unconfigured nic
            if not nic.ip:
                continue

            dest = self.repo_path / 'ks.cfg.' + nic.ip
            if not dest.exists():

                niihost = 'http://' + nic.ip

                # web server root is different: /repos/<repoid>
                f = open(dest, 'w')
                try:
                    t = Template(file=str(src), searchList=[{'niihost': niihost, 'repodir': 'repos/' + str(self.repoid)}])  
                except:
                    f.close()
                    raise UnableToGenerateFileFromTemplateError, 'Cannot create \'%s\'' % dest

                f.write(str(t))
                f.close()

    def verify(self):
        return True

    def make(self, ngname):
        """makes the repository"""

        try:
            self.UpdateDatabase(ngname)
            self.makeRepoDirs()
            self.copyOSKit()
            self.copyKitsPackages()
            self.copyContribPackages()
            self.copyRamDisk()
            self.makeComps()
            self.makeMetaInfo()
            self.copyKusuNodeInstaller()
            self.makeAutoInstallScript()
            self.verify()
        except Exception, e:
            # Don't use self.delete(), since is unsure state

            if self.repoid: #repo have been inserted into database
                repos_have_kits = self.db.ReposHaveKits.select_by(repoid = self.repoid)
                repo = self.db.Repos.get(self.repoid)
                
                for obj in repos_have_kits + [repo]:
                    obj.delete()
                    obj.flush()         

            if self.repo_path and self.repo_path.exists():
                self.repo_path.rmtree()

            raise e

        return self

    def refresh(self, repoid_or_reponame):
        """refresh the repository"""

        self.repoid = self.getRepoID(repoid_or_reponame)
        if not self.repoid:
            raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame
       
        try:
            self.clean(self.repoid)
            self.makeRepoDirs()
            self.copyOSKit()
            self.copyKitsPackages()
            self.copyContribPackages()
            self.copyRamDisk()
            self.makeComps()
            self.makeMetaInfo()
            self.copyKusuNodeInstaller()
            self.makeAutoInstallScript()
            self.verify()
        except Exception, e:
            raise e

        return self

    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        src = self.os_path / self.dirlayout['repodatadir'] / 'comps.xml'
        dest = self.repo_path / self.dirlayout['repodatadir'] / 'comps.xml'

        (dest.parent.relpathto(src)).symlink(dest)

        self.comps_file = dest

    def makeMetaInfo(self):
        """Creates a yum repoistory"""

        repocache_path = self.getRepoCachePath()
        if (not repocache_path.exists()):
            repocache_path.makedirs()
        cmd = 'createrepo -c %s -g %s %s' % (repocache_path, self.comps_file, self.repo_path)

        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except: 
            if repocache_path.exists(): repocache_path.rmtree()
            
            raise CommandFailedToRunError, 'createrepo failed'

        if retcode:
            if repocache_path.exists(): repocache_path.rmtree()
 
            raise YumRepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

    def getKernelPackages(self):
        """get a list of kernel packages"""
        
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        kpkgs = []
        try:
            li = [f for f in self.repo_path.walkfiles('kernel*rpm')]
            kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    def getBaseYumDir(self, dir_name='default'):
        return self.repo_path / self.yum_dirs[dir_name.lower()]

class Fedora6Repo(RedhatYumRepo, YumUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'fedora', '6', os_arch, prefix, db)
        YumUpdate.__init__(self, 'fedora', '6', os_arch, prefix, db)

        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Fedora/RPMS'
        self.dirlayout['basedir'] = 'Fedora/base'

    def getSources(self):
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      version=self.os_version,
                                      arch=self.os_arch)

        if kits:
            return [self.getKitsPath(kits[0].kid) /  self.dirlayout['rpmsdir']]
        else:
            return []

    def getURI(self):
        if not self.configFile:
            baseurl = path('http://download.fedora.redhat.com/pub/fedora/linux/')
        else:
            cfg = self.getConfig(self.configFile)
            if cfg.has_key('fedora'):
                baseurl = path(cfg['fedora']['url'])
            else:
                baseurl = path('http://download.fedora.redhat.com/pub/fedora/linux/')

        core = str(baseurl / 'core' / '6' / self.os_arch / 'os')
        updates = str(baseurl / 'core' / 'updates' / '6' / self.os_arch )

        return [updates]
    
    def getPackageFilePath(self, packagename):
        p = (self.repo_path / self.dirlayout['rpmsdir'] / packagename)

        if p.exists():
            return p
        else:
            return None

    def getPackagesDir(self):
        return [self.repo_path / self.dirlayout['rpmsdir']]
 
class Centos5Repo(RedhatYumRepo, YumUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'centos', '5', os_arch, prefix, db)
        YumUpdate.__init__(self, 'centos', '5', os_arch, prefix, db)
        
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'CentOS'

    def getSources(self):

        kits = self.db.Kits.select_by(rname=self.os_name,
                                      arch=self.os_arch)
        
        if not kits:
            return []

        min_version = '0'

        for kit in kits:
            if kit.isOS and kit.os.major == '5' and kit.os.minor > min_version:
                min_version = kit.os.minor
                kid = kit.kid

        return [self.getKitPath(kid) / self.dirlayout['rpmsdir']]

    def getURI(self):
        if not self.configFile:
            baseurl = path('http://mirror.centos.org/centos')
        else:
            cfg = self.getConfig(self.configFile)
            if cfg.has_key('centos'):
                baseurl = path(cfg['centos']['url'])
            else:
                baseurl = path('http://mirror.centos.org/centos')

        os = str(baseurl / '5' / 'os' / self.os_arch)
        updates = str(baseurl / '5' / 'updates' / self.os_arch)
        
        return [os,updates]
    
    def getPackageFilePath(self, packagename):
        p = (self.repo_path / self.dirlayout['rpmsdir'] / packagename)

        if p.exists():
            return p
        else:
            return None

    def getPackagesDir(self):
        return [self.repo_path / self.dirlayout['rpmsdir']]
 
class Fedora7Repo(RedhatYumRepo, YumUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'fedora', '7', os_arch, prefix, db)
        YumUpdate.__init__(self, 'fedora', '7', os_arch, prefix, db)
        
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Fedora'

    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        src = self.os_path / self.dirlayout['repodatadir'] / 'comps-f7.xml'
        dest = self.repo_path / self.dirlayout['repodatadir'] / 'comps-f7.xml'

        (dest.parent.relpathto(src)).symlink(dest)

        self.comps_file = dest

    def getSources(self):
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      version=self.os_version,
                                      arch=self.os_arch)

        if kits:
            return [self.getKitsPath(kits[0].kid) /  self.dirlayout['rpmsdir']]
        else:
            return []

    def getURI(self):
        if not self.configFile:
            baseurl = path('http://download.fedora.redhat.com/pub/fedora/linux/')
        else:
            cfg = self.getConfig(self.configFile)
            if cfg.has_key('fedora'):
                baseurl = path(cfg['fedora']['url'])
            else:
                baseurl = path('http://download.fedora.redhat.com/pub/fedora/linux/')

        core = str(baseurl / 'releases' / '7' / 'Fedora' / self.os_arch / 'os')
        updates = str(baseurl / 'updates' / '7' / self.os_arch )

        return [updates]
    
    def getPackageFilePath(self, packagename):
        p = (self.repo_path / self.dirlayout['rpmsdir'] / packagename)

        if p.exists():
            return p
        else:
            return None

    def getPackagesDir(self):
        return [self.repo_path / self.dirlayout['rpmsdir']]
 
class Redhat5Repo(RedhatYumRepo, RHNUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'rhel', '5', os_arch, prefix, db)
        RHNUpdate.__init__(self, '5', os_arch, prefix, db)
        
        self.yum_dirs['default'] = 'Server'
        self.yum_dirs['server'] = 'Server'
        self.yum_dirs['cluster'] = 'Cluster'
        self.yum_dirs['clusterstorage'] = 'ClusterStorage'
        
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

    def getSources(self):
        
        # FIXME: does not work correctly because of kit name changes
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      arch=self.os_arch)

        if not kits:
            return []

        min_version = '0'

        for kit in kits:
            if kit.isOS and kit.os.major == '5' and kit.os.minor > min_version:
                min_version = kit.os.minor
                kid = kit.kid

        return [self.getKitsPath(kid) / p 
                for p in [self.dirlayout['server.rpmsdir'],
                          self.dirlayout['cluster.rpmsdir'],
                          self.dirlayout['clusterstorage.rpmsdir'],
                          self.dirlayout['vt.rpmsdir']]]

    def copyKitsPackages(self):
        # Need a better method for this
        kits = self.db.Kits.select_by(self.db.ReposHaveKits.c.repoid==self.repoid,
                                      self.db.ReposHaveKits.c.kid == self.db.Kits.c.kid,
                                      self.db.Kits.c.isOS==False)

        rpmPkgs = [rpmtool.getLatestRPM([self.repo_path / self.dirlayout['server.rpmsdir']]),
                   rpmtool.getLatestRPM([self.repo_path / self.dirlayout['cluster.rpmsdir']]),
                   rpmtool.getLatestRPM([self.repo_path / self.dirlayout['clusterstorage.rpmsdir']]),
                   rpmtool.getLatestRPM([self.repo_path / self.dirlayout['vt.rpmsdir']])]

        for kit in kits:
            pkgdir = self.getKitPath(kit.kid)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir():
                if file.isfile() and file.basename() not in ['TRANS.TBL', 'kitinfo']:

                    rpm = rpmtool.RPM(str(file))

                    name = rpm.getName()
                    arch = rpm.getArch()

                    # We will be replacing the package from the os kit when 
                    # it is provided by a kit
                    for rpmPkg in rpmPkgs:
                        if rpmPkg.has_key(name):
                            if arch in ['i386', 'i486', 'i586', 'i686']:
                                for arch in ['i386', 'i486', 'i586', 'i686']:
                                    if rpmPkg[name].has_key(arch):
                                        osFile = rpmPkg[name][arch][0].getFilename()
                                        if osFile.exists(): osFile.remove()

                            else:
                                if rpmPkg[name].has_key(arch):
                                    osFile = rpmPkg[name][arch][0].getFilename()
                                    if osFile.exists(): osFile.remove()

                    dest = self.repo_path / self.dirlayout['server.rpmsdir'] / file.basename()

                    if dest.exists(): dest.remove()

                    (dest.parent.relpathto(file)).symlink(dest)

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
                    if not file.isdir() and file.basename() not in ['TRANS.TBL', 'kitinfo']:
                        dest = self.repo_path / dir / file.basename()
                        (dest.parent.relpathto(file)).symlink(dest)

        discinfo = self.os_path / '.discinfo'
        if discinfo.exists():
            dest = self.repo_path / '.discinfo' 
            (dest.parent.relpathto(discinfo)).symlink(dest)

    def copyContribPackages(self):

        if not self.getContribPath().exists():
            return

        contribFiles = self.getContribPath().listdir()

        if not contribFiles:
            return

        rpmPkgs = [rpmtool.getLatestRPM([self.repo_path / self.dirlayout['server.rpmsdir']]),
                   rpmtool.getLatestRPM([self.repo_path / self.dirlayout['cluster.rpmsdir']]),
                   rpmtool.getLatestRPM([self.repo_path / self.dirlayout['clusterstorage.rpmsdir']]),
                   rpmtool.getLatestRPM([self.repo_path / self.dirlayout['vt.rpmsdir']])]


        for file in contribFiles:
            if file.basename() not in ['TRANS.TBL', 'kitinfo']:

                rpm = rpmtool.RPM(str(file))

                name = rpm.getName()
                arch = rpm.getArch()

                # We will be replacing the package from the os kit when 
                # it is provided by a kit
                for rpmPkg in rpmPkgs:
                    if rpmPkg.has_key(name):
                        if arch in ['i386', 'i486', 'i586', 'i686']:
                            for arch in ['i386', 'i486', 'i586', 'i686']:
                                if rpmPkg[name].has_key(arch):
                                    osFile = rpmPkg[name][arch][0].getFilename()
                                    if osFile.exists(): osFile.remove()

                        else:
                            if rpmPkg[name].has_key(arch):
                                osFile = rpmPkg[name][arch][0].getFilename()
                                if osFile.exists(): osFile.remove()

                dest = self.repo_path / self.dirlayout['server.rpmsdir'] / file.basename()

                if dest.exists(): dest.remove()

                (dest.parent.relpathto(file)).symlink(dest)



    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        src = self.os_path / self.dirlayout['server.repodatadir'] / 'comps-rhel5-server-core.xml'
        dest = self.repo_path / self.dirlayout['server.repodatadir'] / 'comps-rhel5-server-core.xml'

        (dest.parent.relpathto(src)).symlink(dest)

        self.comps_file = dest

    def makeMetaInfo(self):
        """Creates a yum repoistory"""

        repocache_path = self.getRepoCachePath()
        if (not repocache_path.exists()):
            repocache_path.makedirs()
        cmd = 'createrepo -c %s  -g %s %s' % (repocache_path, self.comps_file, self.repo_path / 'Server')

        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except:
            if repocache_path.exists(): repocache_path.rmtree()
 
            raise CommandFailedToRunError, 'createrepo failed'

        if retcode:
            if repocache_path.exists(): repocache_path.rmtree()
 
            raise YumRepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path
    
    def getPackageFilePath(self, packagename):

        for dirlayout in [self.dirlayout['server.rpmsdir'],
                           self.dirlayout['cluster.rpmsdir'],
                           self.dirlayout['clusterstorage.rpmsdir'],
                           self.dirlayout['vt.rpmsdir']]:
            p = (self.repo_path / dirlayout / packagename)

            if p.exists():
                return p
 
        return None 

    def getPackagesDir(self):
        return [self.repo_path / self.dirlayout['server.rpmsdir']]
 
class SLES10Repo(SuseYastRepo, YouUpdate):
    def __init__(self, os_arch, prefix, db):
        SuseYastRepo.__init__(self, 'sles', '10', os_arch, prefix, db)
        YouUpdate.__init__(self, '10', os_arch, prefix, db)
            
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['bootdir'] = 'boot'
        self.dirlayout['imagesdir'] = 'boot/%s'  % self.os_arch
        self.dirlayout['mediadir'] = 'media.1' 
        self.dirlayout['isolinuxdir'] = 'boot/%s/loader' % self.os_arch
        self.dirlayout['descrdir'] = 'suse/setup/descr' 
        self.dirlayout['patchesdir'] = 'patches/repodata'
        self.dirlayout['docdudir'] = 'docu'
        
        self.dirlayout['packagesdir.noarch'] = 'suse/noarch' 
        self.dirlayout['packagesdir.i386'] = 'suse/i386';
        self.dirlayout['packagesdir.i486'] = 'suse/i486';
        self.dirlayout['packagesdir.i586'] = 'suse/i586';
        self.dirlayout['packagesdir.i686'] = 'suse/i686';
        if os_arch == 'x86_64':
            self.dirlayout['packagesdir.x86_64'] = 'suse/x86_64';

    def getSources(self):
        
        return [self.getRepoPath()]

    def getPackageFilePath(self, packagename):

        for dirlayout in self.getPackagesDir():
            p = (self.repo_path / dirlayout / packagename)

            if p.exists():
                return p

        return None
    
    def makeAutoInstallScript(self):
        """Make the autoinstall script for the repository"""
        pass #SLES nodeinstaller does not require fake autoinst.xml

class OpenSUSE103Repo(SuseYastRepo):
    def __init__(self, os_arch, prefix, db):
        SuseYastRepo.__init__(self, 'opensuse', '10.3', os_arch, prefix, db)
            
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['imagesdir'] = 'boot/%s'  % self.os_arch
        self.dirlayout['mediadir'] = 'media.1' 
        self.dirlayout['isolinuxdir'] = 'boot/%s/loader' % self.os_arch
        self.dirlayout['descrdir'] = 'suse/setup/descr' 
        self.dirlayout['docdudir'] = 'docu'
        
        self.dirlayout['packagesdir.noarch'] = 'suse/noarch' 
        self.dirlayout['packagesdir.i386'] = 'suse/i386';
        self.dirlayout['packagesdir.i486'] = 'suse/i486';
        self.dirlayout['packagesdir.i586'] = 'suse/i586';
        self.dirlayout['packagesdir.i686'] = 'suse/i686';

        if os_arch == 'x86_64':
            self.dirlayout['packagesdir.x86_64'] = 'suse/x86_64';

    def getPackageFilePath(self, packagename):

        for dirlayout in self.getPackagesDir():
            p = (self.repo_path / dirlayout / packagename)

            if p.exists():
                return p

        return None 

    def makeMetaInfo(self):
        
        for p in [self.dirlayout['descrdir']]:
            md5sum = self.repo_path / p / 'MD5SUMS'
            if md5sum.exists():
                md5sum.remove()

        yastRepo = YastRepo(self.repo_path)
        yastRepo.make()


        for file in ['content.asc', 'content.key']:
            file = self.os_path / file
    
            if file.exists(): 
                dest = self.repo_path / file.basename()
                file.copy(dest)

    def makeAutoInstallScript(self):
        """Make the autoinstall script for the repository"""
        pass #openSUSE nodeinstaller does not require fake autoinst.xml


