#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.util.errors import *
from kusu.core import database as db
from kusu.repoman import tools
from kusu.repoman.updates import YumUpdate, RHNUpdate
from kusu.util import rpmtool
from path import path
from Cheetah.Template import Template
import sqlalchemy as sa
import os

import kusu.util.log as kusulog
kl = kusulog.getKusuLog()

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

    def __init__(self, prefix, db):
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

    def getKits(self, ngname):
        """Returns a list of kits for a nodegroup"""
        return tools.getKits(self.db, ngname)

    def getOSPath(self):
        """Get the OS path for the repository"""

        os_name, os_version, os_arch = tools.getOS(self.db, self.repoid)
        return self.getKitPath(os_name, os_version, os_arch)

    def getContribPath(self):
        """Get the contrib path for the repository"""

        os_name, os_version, os_arch = tools.getOS(self.db, self.repoid)
        

        return [self.prefix / 'depot' / 'contrib' / os_name / os_version / os_arch, \
                self.prefix / 'depot' / 'local' / os_name / os_version / os_arch]
              
        
    def getKitPath(self, name, version, arch):
        """Get the kit path given the name, version and arch"""

        return self.prefix / 'depot' / 'kits' / name / version / arch
       
    def getRepoPath(self, repoid = None):
        """Returns the repository path"""

        if repoid:
            return self.prefix / 'depot' / 'repos' / str(repoid)
        else:
            return self.prefix / 'depot' / 'repos' / str(self.repoid)


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
        
        repo.repository='/depot/repos/%s' % repo.repoid
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
                kl.error('Repo: \'%s\' not created' % repoid_or_reponame)
                raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame
            else:
                self.repo_path = self.getRepoPath(repoid)
         
        if not self.repo_path.exists():
            kl.error('Repo: \'%s\' not created' % repoid_or_reponame)
            raise RepoNotCreatedError, 'Repo: \'%s\' not created' % repoid_or_reponame
        else:
            kl.info('Deleted Repo: %s' % self.repo_path)
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

        self.repoid = None
        self.repo_path = None

        kl.info('Delete repo: %s', repo_path)

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
        
        for dir in self.dirlayout.values():
            try:
                (self.repo_path / dir).makedirs()
                kl.info('Made repo dir: %s' % (self.repo_path / dir))
            except: pass


class RedhatRepo(BaseRepo):

    comps_file = None

    def __init__(self, prefix, db):
        BaseRepo.__init__(self, prefix, db)
 

    def copyKitsPackages(self):
        # Need a better method for this
        kits = self.db.Kits.select_by(self.db.ReposHaveKits.c.repoid==self.repoid,
                                      self.db.ReposHaveKits.c.kid == self.db.Kits.c.kid,
                                      self.db.Kits.c.isOS==False)

        rpmPkgs = rpmtool.getLatestRPM([self.repo_path / self.dirlayout['rpmsdir']])

        for kit in kits:

            kl.info('Copying Kit: %s %s %s' % (kit.rname, kit.version, kit.arch))

            pkgdir = self.getKitPath(kit.rname, kit.version, kit.arch)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir():
                if file.basename() not in ['TRANS.TBL', 'kitinfo']:
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
        
        kl.info('Copying OS Kit: %s' % self.os_path)
        
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

        for contribPath in  self.getContribPath():

            if not contribPath.exists():
                kl.warn('Contrib path: %s does not exists. Skipping' % contribPath)
                continue

            contribFiles = contribPath.listdir()

            if not contribFiles:
                kl.warn('No packages in contrib path: %s. Skipping' % contribPath)
                continue

            rpmPkgs = rpmtool.getLatestRPM([self.repo_path / self.dirlayout['rpmsdir']])

            kl.info('Copying contrib packages: %s' % contribPath)

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
                                File = rpmPkgs[name][arch][0].getFilename()
                                if osFile.exists(): osFile.remove()

                    else:
                        if rpmPkgs[name].has_key(arch):
                            osFile = rpmPkgs[name][arch][0].getFilename()
                            if osFile.exists(): osFile.remove()
                    
                dest = self.repo_path / self.dirlayout['rpmsdir'] / file.basename()

                if dest.exists(): dest.remove()

                (dest.parent.relpathto(file)).symlink(dest)

    def copyKusuNodeInstaller(self):
        """copy the kusu installer to the repository"""

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

        if src.exists() and not dest.exists():
            kl.info('Copy Node Installer image: %s' % src)
            (dest.realpath().parent.relpathto(src)).symlink(dest)

    def makeAutoInstallScript(self):
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
                index = self.repo_path.splitall().index('repos')
                repodir = os.path.sep.join(self.repo_path.splitall()[index:])

                f = open(dest, 'w')
                try:
                    t = Template(file=str(src), searchList=[{'niihost': niihost, 'repodir': repodir}])  
                except:
                    f.close()
                    raise UnableToGenerateFileFromTemplateError, 'Cannot create \'%s\'' % dest

                f.write(str(t))
                f.close()

                kl.info('Wrote dummy ks.cfg: %s', dest)

    def make(self, ngname):
        """makes the repository"""

        try:
            self.UpdateDatabase(ngname)
            self.makeRepoDirs()
            self.copyOSKit()
            self.copyKitsPackages()
            self.copyContribPackages()
            self.copyRamDisk()
            self.copyKusuNodeInstaller()
            self.makeComps()
            self.makeMetaInfo()
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
            self.copyKusuNodeInstaller()
            self.makeComps()
            self.makeMetaInfo()
            self.makeAutoInstallScript()
            self.verify()
        except Exception, e:
            raise e

        return self

    def makeMetaInfo(self):
        self.makeYumMetaData()

    def makeYumMetaData(self):
        """Creates a yum repoistory"""

        dotrepodata = self.repo_path / '.repodata'
        cmd = 'createrepo -g %s %s' % (self.comps_file, self.repo_path)

        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except: 
            if dotrepodata.exists():
                dotrepodata.rmtree()
            
            raise CommandFailedToRunError, 'createrepo failed'

        if retcode:
            if dotrepodata.exists():
                dotrepodata.rmtree()
 
            kl.error('Unable to create repo at: %s Reason: %s' % (self.repo_path, err))
            raise YumRepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

        kl.info('Made yum repo: %s' % self.repo_path)


class Redhat4Repo(RedhatRepo, RHNUpdate):
    
    def __init__(self, os_arch, prefix, db):    
        RedhatRepo.__init__(self, prefix, db)
        RHNUpdate.__init__(self, '4', os_arch, prefix, db)
 
        self.os_name = 'rhel'
        self.os_version = '4'
        self.os_arch = os_arch
 
        self.ostype = '%s-%s-%s' % (self.os_name, self.os_version, self.os_arch)

        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'RedHat/RPMS'
        self.dirlayout['basedir'] = 'RedHat/base'

    def copyRamDisk(self):
        pass

    
    def makeComps(self):
        """Makes the necessary comps xml file"""

        self.comps_file = self.os_path / self.dirlayout['basedir'] / 'comps.xml'

    def verify(self):
        return True

    def copyOSKit(self):

        self.os_path = self.getOSPath()
        
        kl.info('Copying OS Kit: %s' % self.os_path)
        
        # Validate OS layout
        for dir in self.dirlayout.values():
            if dir == 'repodata': # does not exist in rhel4 kit
                continue

            dir = self.os_path / dir
            if not dir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % dir
             
        for key, dir in self.dirlayout.items():
            if key != 'repodatadir':
               for file in (self.os_path / dir).listdir():
                    if not file.isdir() and file.basename() not in ['TRANS.TBL', 'kitinfo']:
                        dest = self.repo_path / dir / file.basename()
                        (dest.parent.relpathto(file)).symlink(dest)

        file = self.os_path / self.dirlayout['basedir'] / 'stage2.img'
        dest = self.repo_path / self.dirlayout['basedir'] / 'netstg2.img'
        if dest.exists(): dest.remove()
        (dest.parent.relpathto(file)).symlink(dest)

        discinfo = self.os_path / '.discinfo'
        if discinfo.exists():
            dest = self.repo_path / '.discinfo' 
            (dest.parent.relpathto(discinfo)).symlink(dest)

 
    def makeMetaInfo(self):
        """Creates a hdlist repository"""

        pkgorder = self.repo_path / 'pkgorder'

        cmd = 'genhdlist --withnumbers --productpath RedHat %s && ' % self.repo_path
        cmd = cmd + 'classic-anaconda-runner pkgorder %s %s RedHat > %s && ' % (self.repo_path, self.os_arch, pkgorder)
        cmd = cmd + 'genhdlist --fileorder %s --withnumbers --productpath RedHat %s' % (pkgorder, self.repo_path)

        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except: 
            raise CommandFailedToRunError, 'genhdlist/pkgorder failed'

        if retcode:
            kl.error('Unable to create repo at: %s Reason: %s' % (self.repo_path, err))
            raise RepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

        if pkgorder.exists(): pkgorder.remove()

        kl.info('Made repo: %s' % self.repo_path)
        
        self.makeYumMetaData()

    def copyKusuNodeInstaller(self):
        """copy the kusu installer to the repository"""

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
    
        dest = self.repo_path / self.dirlayout['basedir'] / 'updates.img'

        if src.exists() and not dest.exists():
            kl.info('Copy Node Installer image: %s' % src)
            (dest.realpath().parent.relpathto(src)).symlink(dest)

    def getSources(self):
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      arch=self.os_arch)

        if not kits:
            return []

        if len(kits) == 1:
            min_version = kits[0].version
        else:
            min_version = '4.999'

            for kit in kits:
                if self.getOSMajorVersion(kit.version) == '4' and kit.version < min_version:
                    min_version = kit.version

        return [path(os.path.join(self.prefix / 'depot', 'kits', self.os_name, min_version, self.os_arch, p))
                for p in [self.dirlayout['rpmsdir']]]


class Centos4Repo(RedhatRepo, YumUpdate):
    
    def __init__(self, os_arch, prefix, db):    
        RedhatRepo.__init__(self, prefix, db)
        YumUpdate.__init__(self, 'centos', '4', os_arch, prefix, db)
 
        self.os_name = 'centos'
        self.os_version = '4'
        self.os_arch = os_arch
 
        self.ostype = '%s-%s-%s' % (self.os_name, self.os_version, self.os_arch)

        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'CentOS/RPMS'
        self.dirlayout['basedir'] = 'CentOS/base'

    def copyRamDisk(self):
        pass

    def makeComps(self):
        """Makes the necessary comps xml file"""

        self.comps_file = self.os_path / self.dirlayout['basedir'] / 'comps.xml'

    def verify(self):
        return True

    def copyOSKit(self):

        self.os_path = self.getOSPath()
        
        kl.info('Copying OS Kit: %s' % self.os_path)
        
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

        file = self.os_path / self.dirlayout['basedir'] / 'stage2.img'
        dest = self.repo_path / self.dirlayout['basedir'] / 'netstg2.img'
        if dest.exists(): dest.remove()
        (dest.parent.relpathto(file)).symlink(dest)

        discinfo = self.os_path / '.discinfo'
        if discinfo.exists():
            dest = self.repo_path / '.discinfo' 
            (dest.parent.relpathto(discinfo)).symlink(dest)

 
    def makeMetaInfo(self):
        """Creates a hdlist repository"""

        pkgorder = self.repo_path / 'pkgorder'

        cmd = 'genhdlist --withnumbers --productpath CentOS %s && ' % self.repo_path
        cmd = cmd + 'classic-anaconda-runner pkgorder %s %s CentOS > %s && ' % (self.repo_path, self.os_arch, pkgorder)
        cmd = cmd + 'genhdlist --fileorder %s --withnumbers --productpath CentOS %s' % (pkgorder, self.repo_path)

        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except: 
            raise CommandFailedToRunError, 'genhdlist/pkgorder failed'

        if retcode:
            kl.error('Unable to create repo at: %s Reason: %s' % (self.repo_path, err))
            raise RepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

        if pkgorder.exists(): pkgorder.remove()

        kl.info('Made repo: %s' % self.repo_path)

        self.makeYumMetaData()

    def copyKusuNodeInstaller(self):
        """copy the kusu installer to the repository"""

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
    
        dest = self.repo_path / self.dirlayout['basedir'] / 'updates.img'

        if src.exists() and not dest.exists():
            kl.info('Copy Node Installer image: %s' % src)
            (dest.realpath().parent.relpathto(src)).symlink(dest)

    def getSources(self):
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      arch=self.os_arch)
        if not kits:
            return []

        if len(kits) == 1:
            min_version = kits[0].version
        else:
            min_version = '4.999'

            for kit in kits:
                if self.getOSMajorVersion(kit.version) == '4' and kit.version < min_version:
                    min_version = kit.version

        return [path(os.path.join(self.prefix, 'depot', 'kits', \
                                  self.os_name, min_version, self.os_arch, \
                                  self.dirlayout['rpmsdir']))]

    def getURI(self):
        if not self.configFile:
            baseurl = path('http://mirror.centos.org/centos')
        else:
            cfg = self.getConfig(self.configFile)
            if cfg.has_key('fedora'):
                baseurl = path(cfg['centos']['url'])
            else:
                baseurl = path('http://mirror.centos.org/centos')

        os = str(baseurl / '4' / 'os' / self.os_arch)
        updates = str(baseurl / '4' / 'updates' / self.os_arch)

        return [os,updates]

    def getPackageFilePath(self, packagename):
        p = (self.repo_path / self.dirlayout['rpmsdir'] / packagename)

        if p.exists():
            return p
        else:
            return None


class RedhatYumRepo(RedhatRepo):
    """Base Redhat repository class"""

    def __init__(self, os_name, os_version, os_arch, prefix, db):
        RedhatRepo.__init__(self, prefix, db)
    
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch
 
        self.ostype = '%s-%s-%s' % (os_name, os_version, os_arch)

    def copyRamDisk(self):
        pass
        
    def verify(self):
        return True

    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        src = self.os_path / self.dirlayout['repodatadir'] / 'comps.xml'
        dest = self.repo_path / self.dirlayout['repodatadir'] / 'comps.xml'

        (dest.parent.relpathto(src)).symlink(dest)

        self.comps_file = dest

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
            return [path(os.path.join(self.prefix, 'depot', 'kits', \
                                      self.os_name, self.os_version, self.os_arch, \
                                      self.dirlayout['rpmsdir']))]
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

class Centos5Repo(RedhatYumRepo, YumUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'centos', '5', os_arch, prefix, db)
        YumUpdate.__init__(self, 'centos', '5', os_arch, prefix, db)
        
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'CentOS'
 
    def getOSMajorVersion(self, os_version):
        """Returns the major number"""
        return os_version.split('.')[0]

    def getSources(self):
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      arch=self.os_arch)
        
        if not kits:
            return []

        if len(kits) == 1:
            min_version = kits[0].version 
        else:
            min_version = '5.999'

            for kit in kits:
                if self.getOSMajorVersion(kit.version) == '5' and kit.version < min_version:
                    min_version = kit.version

        return [path(os.path.join(self.prefix, 'depot', 'kits', \
                                  self.os_name, min_version, self.os_arch, \
                                  self.dirlayout['rpmsdir']))]

    def getURI(self):
        if not self.configFile:
            baseurl = path('http://mirror.centos.org/centos')
        else:
            cfg = self.getConfig(self.configFile)
            if cfg.has_key('fedora'):
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
            return [path(os.path.join(self.prefix, 'depot', 'kits', \
                                      self.os_name, self.os_version, self.os_arch, \
                                      self.dirlayout['rpmsdir']))]
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

        core = str(baseurl / 'releases' / '7' / 'Everything' / self.os_arch / 'os')
        updates = str(baseurl / 'updates' / '7' / self.os_arch )

        return [updates]
    
    def getPackageFilePath(self, packagename):
        p = (self.repo_path / self.dirlayout['rpmsdir'] / packagename)

        if p.exists():
            return p
        else:
            return None

class Fedora8Repo(RedhatYumRepo, YumUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'fedora', '8', os_arch, prefix, db)
        YumUpdate.__init__(self, 'fedora', '8', os_arch, prefix, db)

        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Packages'

    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        src = self.os_path / self.dirlayout['repodatadir'] / 'Fedora-8-comps.xml'
        dest = self.repo_path / self.dirlayout['repodatadir'] / 'Fedora-8-comps.xml'

        (dest.parent.relpathto(src)).symlink(dest)

        self.comps_file = dest

    def getSources(self):
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      version=self.os_version,
                                      arch=self.os_arch)

        if kits:
            return [path(os.path.join(self.prefix, 'depot', 'kits', \
                                      self.os_name, self.os_version, self.os_arch, \
                                      self.dirlayout['rpmsdir']))]
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

        core = str(baseurl / 'releases' / '8' / 'Everything' / self.os_arch / 'os')
        updates = str(baseurl / 'updates' / '8' / self.os_arch )

        return [updates]

    def getPackageFilePath(self, packagename):
        p = (self.repo_path / self.dirlayout['rpmsdir'] / packagename)

        if p.exists():
            return p
        else:
            return None

class Fedora9Repo(RedhatYumRepo, YumUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'fedora', '9', os_arch, prefix, db)
        YumUpdate.__init__(self, 'fedora', '9', os_arch, prefix, db)

        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Packages'

    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        src = self.os_path / self.dirlayout['repodatadir'] / 'Fedora-9-comps.xml'
        dest = self.repo_path / self.dirlayout['repodatadir'] / 'Fedora-9-comps.xml'

        (dest.parent.relpathto(src)).symlink(dest)

        self.comps_file = dest

    def getSources(self):
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      version=self.os_version,
                                      arch=self.os_arch)

        if kits:
            return [path(os.path.join(self.prefix, 'depot', 'kits', \
                                      self.os_name, self.os_version, self.os_arch, \
                                      self.dirlayout['rpmsdir']))]
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

        core = str(baseurl / 'releases' / '9' / 'Everything' / self.os_arch / 'os')
        updates = str(baseurl / 'updates' / '9' / self.os_arch )

        return [updates]

    def getPackageFilePath(self, packagename):
        p = (self.repo_path / self.dirlayout['rpmsdir'] / packagename)

        if p.exists():
            return p
        else:
            return None

class Redhat5Repo(RedhatYumRepo, RHNUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'rhel', '5', os_arch, prefix, db)
        RHNUpdate.__init__(self, '5', os_arch, prefix, db)
            
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
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      arch=self.os_arch)

        if not kits:
            return []

        if len(kits) == 1:
            min_version = kits[0].version 
        else:
            min_version = '5.999'

            for kit in kits:
                if self.getOSMajorVersion(kit.version) == '5' and kit.version < min_version:
                    min_version = kit.version

        return [path(os.path.join(self.prefix / 'depot', 'kits', self.os_name, min_version, self.os_arch, p))
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

            kl.info('Copying Kit: %s %s %s' % (kit.rname, kit.version, kit.arch))

            pkgdir = self.getKitPath(kit.rname, kit.version, kit.arch)

            if not pkgdir.exists():
                raise InvalidPathError, 'Path \'%s\' not found' % pkgdir
   
            for file in pkgdir.listdir():
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

    def copyOSKit(self):

        self.os_path = self.getOSPath()
        
        kl.info('Copying OS Kit: %s' % self.os_path)

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

        for contribPath in  self.getContribPath():

            if not contribPath.exists():
                kl.warn('Contrib path: %s does not exists. Skipping' % contribPath)
                continue

            contribFiles = contribPath.listdir()

            if not contribFiles:
                kl.warn('No pacakges in contrib path: %s. Skipping' % contribPath)
                continue

            kl.info('Copying contrib packages: %s' % contribPath)

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

        dotrepodata = self.repo_path / '.repodata'
        cmd = 'createrepo -g %s %s' % (self.comps_file, self.repo_path / 'Server')

        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except:
            if dotrepodata.exists():
                dotrepodata.rmtree()
 
            raise CommandFailedToRunError, 'createrepo failed'

        if retcode:
            if dotrepodata.exists():
                dotrepodata.rmtree()
 
            kl.error('Unable to create repo at: %s Reason: %s' % (self.repo_path, err))
            raise YumRepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

        kl.info('Made yum repo: %s' % self.repo_path)
    
    def getPackageFilePath(self, packagename):

        for dirlayout in [self.dirlayout['server.rpmsdir'],
                           self.dirlayout['cluster.rpmsdir'],
                           self.dirlayout['clusterstorage.rpmsdir'],
                           self.dirlayout['vt.rpmsdir']]:
            p = (self.repo_path / dirlayout / packagename)

            if p.exists():
                return p
 
        return None

class ScientificLinux5Repo(RedhatYumRepo, YumUpdate):
    def __init__(self, os_arch, prefix, db):
        RedhatYumRepo.__init__(self, 'scientificlinux', '5', os_arch, prefix, db)
        YumUpdate.__init__(self, 'scientificlinux', '5', os_arch, prefix, db)
        
        # FIXME: Need to use a common lib later, maybe boot-media-tool
        self.dirlayout['repodatadir'] = 'SL/repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'SL'
 
    def getOSMajorVersion(self, os_version):
        """Returns the major number"""
        return os_version.split('.')[0]

    def getSources(self):
        kits = self.db.Kits.select_by(rname=self.os_name,
                                      arch=self.os_arch)
        
        if not kits:
            return []

        if len(kits) == 1:
            min_version = kits[0].version 
        else:
            min_version = '5.999'

            for kit in kits:
                if self.getOSMajorVersion(kit.version) == '5' and kit.version < min_version:
                    min_version = kit.version

        return [path(os.path.join(self.prefix, 'depot', 'kits', \
                                  self.os_name, min_version, self.os_arch, \
                                  self.dirlayout['rpmsdir']))]

    def getURI(self):
        if not self.configFile:
            baseurl = path('http://ftp.scientificlinux.org/linux/scientific')
        else:
            cfg = self.getConfig(self.configFile)
            if cfg.has_key('scientificlinux'):
                baseurl = path(cfg['scientificlinux']['url'])
            else:
                baseurl = path('http://ftp.scientificlinux.org/linux/scientific')

        os = str(baseurl / '5x' / self.os_arch / 'SL')
        updates = str(baseurl / '5x' / self.os_arch / 'updates' / 'security')
        
        return [os,updates]
    
    def getPackageFilePath(self, packagename):
        p = (self.repo_path / self.dirlayout['rpmsdir'] / packagename)

        if p.exists():
            return p
        else:
            return None

    def makeComps(self):
        """Makes the necessary comps xml file"""

        # symlink comps.xml
        src = self.os_path / self.dirlayout['repodatadir'] / 'comps-sl.xml'
        dest = self.repo_path / self.dirlayout['repodatadir'] / 'comps-sl.xml'

        (dest.parent.relpathto(src)).symlink(dest)

        self.comps_file = dest

    def makeYumMetaData(self):
        """Creates a yum repoistory"""

        dotrepodata = self.repo_path / '.repodata'
        cmd = 'createrepo -g %s %s' % (self.comps_file, self.repo_path / 'SL')

        try:
            p = subprocess.Popen(cmd,
                                 cwd=self.repo_path,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except: 
            if dotrepodata.exists():
                dotrepodata.rmtree()
            
            raise CommandFailedToRunError, 'createrepo failed'

        if retcode:
            if dotrepodata.exists():
                dotrepodata.rmtree()
 
            kl.error('Unable to create repo at: %s Reason: %s' % (self.repo_path, err))
            raise YumRepoNotCreatedError, 'Unable to create repo at \'%s\'' % self.repo_path

        kl.info('Made yum repo: %s' % self.repo_path)

    def copyKusuNodeInstaller(self):
        """copy the kusu installer to the repository"""

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

        if dest.exists(): dest.remove()

        if src.exists():
            kl.info('Copy Node Installer image: %s' % src)
            (dest.realpath().parent.relpathto(src)).symlink(dest)
