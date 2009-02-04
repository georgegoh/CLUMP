#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import re
import tempfile
import time
from path import path
from Cheetah.Template import Template

from kusu.repoman.rhn import RHN
from kusu.repoman.yum import YumRepo
from kusu.repoman.tools import getFile, getConfig
from kusu.driverpatch import DriverPatchController
from kusu.util import tools as utiltools
from kusu.util.errors import *

from primitive.updatetool.commands import YouUpdateCommand
from primitive.fetchtool.commands import FetchCommand
from primitive.support import rpmtool

try:
    import subprocess
except:
    from popen5 import subprocess

class BaseUpdate:

    compclass = {'rhel' : {'5': 'RHEL5Component()'},
                 'centos' : {'5': 'Centos5Component()'},
                 'sles' : {'10': 'SLES10Component()'},
                 'fedora' : {'6': 'Fedora6Component()'}}

    def __init__(self, os_name, os_version, os_arch, prefix, db, updates_root = '/depot/updates'):
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch
        
        self.prefix = prefix
        self.db = db
        self.configFile = None

        self.updates_root = updates_root 
        row = self.db.AppGlobals.select_by(kname = 'DEPOT_UPDATES_ROOT')
        if row: self.updates_root = row[0].kvalue
        if self.updates_root[0] == '/': self.updates_root = self.updates_root[1:]

    def getLatestRPM(self, dirs=[]):
        """Returns a list of the latest rpms"""
        return rpmtool.getLatestRPM(dirs, ignoreErrors=True)

    def getUpdates(self):
        """Gets the updates and writes them into the destination dir"""
        raise NotImplementedError

    def getKernelPackagesList(self, srcPath, pattern=r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?'):
        pat = re.compile(pattern)

        kpkgs = []

        try:
            root = path(srcPath)
            li = [f for f in root.walkfiles('kernel*rpm')]
            kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    def makeUpdateKit(self, pkgs):
        """Makes the update kit"""

        kitName = '%s-updates' % self.os_name 
        kitVersion = self.os_version
        kitRelease = self.getNextRelease(kitName, kitVerson, self.os_arch)
        kitArch = 'noarch'

        # Buildkit's kit src
        tempkitdir = path(tempfile.mkdtemp(prefix='repopatch_buildkit', dir=os.environ.get('KUSU_TMP', '/tmp')))
        # Used by kitops to add the kit from
        kitdir = path(tempfile.mkdtemp(prefix='repopatch_kit', dir=os.environ.get('KUSU_TMP', '/tmp')))

        self.prepKit(tempkitdir, kitName)

        for p in pkgs:
            file = p.getFilename()
            dest = tempkitdir / kitName / 'sources' / file.basename()

            # Use abs symlink. Relative links does not work
            # when buildkit prepares temp new directory for
            # making kit
            file.symlink(dest) 
    
        kernelPkgs = self.makeKitScript(tempkitdir, kitName, kitVersion, kitRelease)
        self.makeKit(tempkitdir, kitdir, kitName)
        
        return (kitdir, kitName, kitVersion, kitRelease, kitArch, kernelPkgs)

    def getNextRelease(self, kitName, kitVersion, kitArch):

        # Find max version
        kits = self.db.Kits.select_by(rname = kitName, version=kitVersion, arch=kitArch)
       
        maxRelease = 0
        for kit in kits:
            if kit.release > maxRelease:
                maxRelease = kit.release

        return maxRelease + 1

    def updateInitrdVmlinuz(self, kitVersion, repo, kernelPkgs):
        
        if not kernelPkgs:
            return

        controller = DriverPatchController(self.db)

        tftpbootdir = path(self.prefix / 'tftpboot' / 'kusu')
        if not tftpbootdir.exists():
            raise DirDoesNotExistError, '%s not found' % (tftpbootdir)

        ngs = self.db.NodeGroups.select_by(repoid = repo.repoid)
        for ng in ngs:
            if ng.installtype == 'package':
                nginitrd = ng.initrd
                if not nginitrd:
                    raise InvalidInitrd, 'initrd not found for nodegroup: %s' % ng.ngname
                
                else:    
                    initrdpath = tftpbootdir / nginitrd
                    if not initrdpath.exists():
                        raise InvalidInitrd, 'initrd: %s does not exists' % initrdpath
     
                newinitrd = 'initrd-%s-%s-%s.%s.img' % (self.os_name, kitVersion, self.os_arch, ng.ngid)
                newkernel = 'kernel-%s-%s-%s.%s' % (self.os_name, kitVersion, self.os_arch, ng.ngid)
                
                cmd = 'driverpatch -u nodegroup id=%s initrd=%s kernel=%s' % (ng.ngid, newinitrd, newkernel)
                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()
                retcode = p.returncode

                if retcode:
                    raise UnableToUpdateInitrdKernel, 'driverpatch failed to run'

            elif ng.installtype in ['disked', 'diskless']:
                cmd = 'buildinitrd -n "%s"' % ng.ngname
                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()
                retcode = p.returncode
   
                if retcode:
                    raise UnableToUpdateInitrdKernel, 'buildinitrd failed to run'
 
            # calls boothost to refresh pxe conf
            p = subprocess.Popen('boothost -t "%s"' % ng.ngname,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode
            
            if retcode:
                raise UnableToUpdateInitrdKernel, 'boothost failed to run'

    def addUpdateKit(self, kitdir):
        from kusu.kitops import kitops

        ko = kitops.KitOps()
        ko.setDB(self.db) 
        ko.setKitMedia(kitdir)
        kits = ko.addKitPrepare()

        for kit in kits:
            
            kitName = '%s-updates' % self.os_name
            if kit[1]['name'] == kitName:
                kid = ko.addKit(kit)
                
                if kitdir.exists():
                    kitdir.rmtree()

                updateKit = self.db.Kits.get(kid)
                updateKit.arch = self.os_arch
                updateKit.save_or_update()
                updateKit.flush()
        
                return updateKit
    
        raise UnrecognizedKitMediaError, "Update kit cannot be found"    

    def makeKitScript(self, tempkitdir, kitName, kitVersion, kitRelease):

        dest = tempkitdir / kitName / 'build.kit'

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        template = kusu_root / 'etc' / 'templates' / 'update.kit.tmpl'

        ns = {}
        ns['kitname'] = kitName
        ns['kitver'] = kitVersion
        ns['kitrel'] = kitRelease
        if self.os_arch in ['i386', 'i486', 'i586', 'i686']:
            ns['kitarch'] = 'x86'
        else:
            ns['kitarch'] = self.os_arch

            
        ns['kitarch'] = 'noarch'
        ns['kitdesc'] = 'Updates for %s %s %s on %s' % \
                        (self.os_name, self.os_version, self.os_arch, time.asctime())

        ns['compclass'] = self.compclass[self.os_name][self.os_version]

        kpkgs = self.getKernelPackagesList(tempkitdir)
        ns['kernels'] = []
        for kpkg in kpkgs:
            kpkg = rpmtool.RPM(str(kpkg))            
            filename = kpkg.getFilename().basename() 
            desc = ' %s for %s' % (kpkg.summary,kpkg.arch)
            ns['kernels'].append({'name':kpkg.name, 'version':kpkg.version, \
                                  'release':kpkg.release, 'filename':filename})
 
        t = Template(file=str(template), searchList=[ns])  
        f = open(dest, 'w')
        f.write(str(t))
        f.close()
   
        return kpkgs 

    def prepKit(self, workingDir, kitName):
        cmd = 'buildkit new kit=%s' % kitName
        p = subprocess.Popen(cmd,
                             cwd=workingDir,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        retcode = p.returncode

        if retcode == 0:
            return True
        else:
            raise UnableToPrepUpdateKit, out
    
    def makeKit(self, workingDir, destDir, kitName):
        cmd = 'buildkit make kit=%s dir=%s' % (kitName, destDir)
        p = subprocess.Popen(cmd,
                             cwd=workingDir,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        retcode = p.returncode

        if retcode == 0:
            # Fix pathing
            for file in (destDir / kitName).listdir():
                if file.islink():
                    realPath = file.realpath()
                    file.remove()
                    realPath.symlink(file)

            # Do not use symlink for component
            comp = (destDir / kitName).listdir('component-%s*.rpm' % kitName)
            if comp and comp[0].islink():
                comp = comp[0]
                realComp = comp.realpath()
                comp.remove()
                realComp.copy(comp)

            # Do not use symlink for kit
            kit = (destDir / kitName).listdir('kit-%s*.rpm' % kitName)
            if kit and kit[0].islink():
                kit = kit[0]
                realKit = kit.realpath()
                kit.remove()
                realKit.copy(kit)

            if workingDir.exists():
                workingDir.rmtree()
            return True
        else:
            raise UnableToMakeUpdateKit, out

    def getSources(self):
        """Return the path of sources to compare against mirror"""
        raise NotImplementedError

    def getConfig(self, configFile):
        """Returns the configuration"""
        return getConfig(configFile)

    def setConfig(self, configFile):
        """Sets the configuration"""
        self.configFile = configFile

class YumUpdate(BaseUpdate):
    def __init__(self, os_name, os_version, os_arch, prefix, db):
        BaseUpdate.__init__(self, os_name, os_version, os_arch, prefix, db)

    def getURI(self):
        """Returns the relavant uri of yum repos"""
        raise NotImplementedError
        
    def getUpdates(self):
        """Gets the updates and writes them into the destination dir"""
    
        dir = path(self.prefix) / self.updates_root / self.os_name / self.os_version / self.os_arch
        if not dir.exists():
            dir.makedirs()

        # Get the latest list of rpms from os kits and the
        # updates dir
        searchPaths = []
        for p in self.getSources():
            if path(p).exists():
                searchPaths.append(p)
        searchPaths.append(dir)
        rpmPkgs = rpmtool.getLatestRPM(searchPaths, True)

        # Merge the necessary update(s) dir
        # into a single dictionary with all the rpms info
        primarys = {}
        for u in self.getURI():
            primarys[u] = YumRepo(u).getPrimary()

        # Filter out the packages that are newer and
        # needs to be downloaded
        downloadPkgs = []
        for r in self.getLatestRPM(primarys):
            name = r.getName()
            arch = r.getArch()

            if rpmPkgs.RPMExists(name, arch):
                # There's a newer rpm, so download it
                if r > rpmPkgs[name][arch][0]:
                    downloadPkgs.append(r)
            else:
                # No such existing rpm, so download it
                downloadPkgs.append(r)
                            
        # Download the packages
        for r in downloadPkgs:
            filename = r.getFilename()
            dest = path(dir / filename.basename())
            
            if dest.exists():
                try:
                    rpmtool.RPM(str(dest))
                    continue
                except:
                    # corrupted/incomplete/etc
                    dest.remove()

            content = getFile(filename)
            if content:
                f = open(dest, 'w')
                f.write(content)
                f.close()

        rpmPkgs = rpmtool.getLatestRPM([dir], True)
        pkgs = rpmPkgs.getList()
        
        newKernels = rpmtool.RPMCollection()
        for pkg in pkgs:
            if pkg.getName().startswith('kernel'):
                newKernelPkg = rpmtool.RPM(name = pkg.getName(),
                                           version = pkg.getVersion(),
                                           release = pkg.getRelease(),
                                           arch = pkg.getArch(),
                                           epoch = pkg.getEpoch())
                newKernelPkg.filename = dir / pkg.getFilename().basename()
                newKernels.add(newKernelPkg)

        return (pkgs, newKernels)

    def getLatestRPM(self, primarys):
        """Return the latested rpms from yum repos"""

        c = rpmtool.RPMCollection()
        for uri, pri in primarys.items():
            for name, value in pri.items():
                for arch, rpms in value.items():
                    for r in rpms:
                        name = r.getName()
                        arch = r.getArch()

                        if c.RPMExists(name, arch):
                            if r > c[name][arch][0]:
                                c[name][arch][0] = r 
                        else:
                            c.add(r)

        c.sort()
        return c.getList()

class RHNUpdate(BaseUpdate):
    def __init__(self, os_version, os_arch, prefix, db):
        BaseUpdate.__init__(self, 'rhel', os_version, os_arch, prefix, db)
        self.rhn = None

    def getRHN(self):
        if self.configFile:
            cfg = self.getConfig(self.configFile)['rhel']
            username = cfg['username']
            password = cfg['password']
            url = cfg['url']
            yumrhn = cfg['yumrhn']

            # new key in kusu 1.2
            if not self.getConfig(self.configFile).has_key('rhel-%s-%s' % (self.os_version, self.os_arch)):
               raise rhnNoAccountInformationProvidedError, 'Missing section in /opt/kusu/etc/updates.conf'

            cfg = self.getConfig(self.configFile)['rhel-%s-%s' % (self.os_version, self.os_arch)]
            serverid = cfg['serverid']

            if not (username and password and url and yumrhn and serverid):
               raise rhnNoAccountInformationProvidedError, 'Please configure /opt/kusu/etc/updates.conf'

            return RHN(username, password, yumrhn, url, int(serverid))

        else:
            raise rhnNoAccountInformationProvidedError, 'No config file provided'

    def getUpdates(self):
        """Gets the updates and writes them into the destination dir"""

        dir = path(self.prefix) / self.updates_root / self.os_name / self.os_version / self.os_arch
        if not dir.exists():
            dir.makedirs()

        if not self.rhn: 
            self.rhn = self.getRHN()
        self.rhn.login()
        channels = self.rhn.getChannels(self.rhn.getServerID())

        # 'rhel-x86_64-server-5'
        # 'rhel-x86_64-server-hpc-5'
        # 'rhel-x86_64-server-5-mrg-grid-1'
        for channel in channels:
            if not re.compile('^rhel-%s-(.*)-%s(.*)' % (self.os_arch, self.os_version)).match(channel['channel_label']):
                raise rhnInvalidServerID, 'Invalid Server ID given. Please check /opt/kusu/etc/updates.conf'

        # Get the latest list of rpms from os kits and the
        # updates dir
        searchPaths = []
        for p in self.getSources():
            if path(p).exists():
                searchPaths.append(p)
        searchPaths.append(dir)
        rpmPkgs = rpmtool.getLatestRPM(searchPaths, True)
      
        downloadPkgs={}
        for channel in channels:
            downloadPkgs[channel['channel_label']] = []
        
        for channel in downloadPkgs.keys():
            for r in self.rhn.getLatestPackages(channel):
                name = r.getName()
                arch = r.getArch()

                if rpmPkgs.RPMExists(name, arch):
                    # There's a newer rpm, so download it
                    if r > rpmPkgs[name][arch][0]:
                        downloadPkgs[channel].append(r)
                else:
                    # No such existing rpm, so download it
                    downloadPkgs[channel].append(r)

        for channel, pkgs in downloadPkgs.items():
            for r in pkgs:
                filename = r.getFilename().basename()
                dest = path(dir / filename)
                
                if dest.exists():
                    try:
                        rpmtool.RPM(str(dest))
                        continue
                    except:
                        # corrupted/incomplete/etc
                        dest.remove()

                
                if self.rhn.getPackage(filename, channel, dest):
                    # Success
                    pass

        try:
            self.rhn.logout()
        except: pass

        rpmPkgs = rpmtool.getLatestRPM([dir], True)
        pkgs = rpmPkgs.getList()
        
        newKernels = rpmtool.RPMCollection()
        for pkg in pkgs:
            if pkg.getName().startswith('kernel'):
                newKernelPkg = rpmtool.RPM(name = pkg.getName(),
                                           version = pkg.getVersion(),
                                           release = pkg.getRelease(),
                                           arch = pkg.getArch(),
                                           epoch = pkg.getEpoch())
                newKernelPkg.filename = dir / pkg.getFilename().basename()
                newKernels.add(newKernelPkg)

        return (pkgs, newKernels)

class YouUpdate(BaseUpdate):
    def __init__(self, os_version, os_arch, prefix, db):
        BaseUpdate.__init__(self, 'sles', os_version, os_arch, prefix, db)

        
    def getYouCred(self):
        if self.configFile:
            cfg = self.getConfig(self.configFile)['sles']
            username = cfg['username']
            password = cfg['password']

            if not (username and password):
               raise youNoAccountInformationProvidedError, 'Please configure /opt/kusu/etc/updates.conf'
        else:
            raise youNoAccountInformationProvidedError, 'No config file provided'

        return (username, password)

    def getChannel(self):

        channels = {'10.0': 'SLES10-Updates',
                    '10.1': 'SLES10-SP1-Updates',
                    '10.2': 'SLES10-SP2-Updates',
                    '10.3': 'SLES10-SP3-Updates' }

        return channels[self.os_version_full]

    def getUpdates(self):
        """Gets the updates and writes them into the destination dir"""
   
        repo = self.db.Repos.get(self.repoid)        
        major = repo.os.major
        minor = repo.os.minor

        self.os_version_full = '%s.%s' % (major,minor)

        dir = path(self.prefix) / self.updates_root / self.os_name / self.os_version_full / self.os_arch
        if not dir.exists():
            dir.makedirs()

        username, password = self.getYouCred()

        if self.os_arch == 'i386':
            os_arch = 'i586'
        else:    
            os_arch = self.os_arch

        c = YouUpdateCommand(username = username, password = password,
                             channel=self.getChannel(), arch=os_arch,
                             repopath=self.getSources()[0])

        downloadPkgs = c.execute()

        # Download the packages
        for r in downloadPkgs:
            filename = r.getFilename()
            dest = path(dir / filename.basename())
        
            if dest.exists():
                try:
                    rpmtool.RPM(str(dest))
                    continue
                except:
                    # corrupted/incomplete/etc
                    dest.remove()

            fc = FetchCommand(uri=filename,
                             fetchdir=False,
                             destdir=dir,
                             overwrite=False)
            status , dest = fc.execute()
 
        rpmPkgs = rpmtool.getLatestRPM([dir], True)
        pkgs = rpmPkgs.getList()
        
        newKernels = rpmtool.RPMCollection()
        for pkg in pkgs:
            if pkg.getName().startswith('kernel'):
                newKernelPkg = rpmtool.RPM(name = pkg.getName(),
                                           version = pkg.getVersion(),
                                           release = pkg.getRelease(),
                                           arch = pkg.getArch(),
                                           epoch = pkg.getEpoch())
                newKernelPkg.filename = dir / pkg.getFilename().basename()
                newKernels.add(newKernelPkg)

        return (pkgs, newKernels)
    
    def makeUpdateKit(self, pkgs):
        """Makes the update kit"""

        kitName = '%s-updates' % self.os_name 
        kitVersion = self.os_version_full
        kitRelease = self.getNextRelease(kitName, kitVersion, self.os_arch)
        kitArch = 'noarch'

        # Buildkit's kit src
        tempkitdir = path(tempfile.mkdtemp(prefix='repopatch_buildkit', dir=os.environ.get('KUSU_TMP', '/tmp')))
        # Used by kitops to add the kit from
        kitdir = path(tempfile.mkdtemp(prefix='repopatch_kit', dir=os.environ.get('KUSU_TMP', '/tmp')))

        self.prepKit(tempkitdir, kitName)

        for p in pkgs:
            file = p.getFilename()
            dest = tempkitdir / kitName / 'sources' / file.basename()

            # Use abs symlink. Relative links does not work
            # when buildkit prepares temp new directory for
            # making kit
            file.symlink(dest) 
    
        kernelPkgs = self.makeKitScript(tempkitdir, kitName, kitVersion, kitRelease)
        self.makeKit(tempkitdir, kitdir, kitName)
        
        return (kitdir, kitName, kitVersion, kitRelease, kitArch, kernelPkgs)

    def makeKitScript(self, tempkitdir, kitName, kitVersion, kitRelease):

        dest = tempkitdir / kitName / 'build.kit'

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        template = kusu_root / 'etc' / 'templates' / 'update.kit.tmpl'

        ns = {}
        ns['kitname'] = kitName
        ns['kitver'] = kitVersion
        ns['kitrel'] = kitRelease
        if self.os_arch in ['i386', 'i486', 'i586', 'i686']:
            ns['kitarch'] = 'x86'
        else:
            ns['kitarch'] = self.os_arch

        ns['kitarch'] = 'noarch'
        ns['kitdesc'] = 'Updates for %s %s %s on %s' % \
                        (self.os_name, self.os_version_full, self.os_arch, time.asctime())

        ns['compclass'] = self.compclass[self.os_name][self.os_version]

        kpkgs = self.getKernelPackagesList(tempkitdir, r'kernel-default-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')
        ns['kernels'] = []
        for kpkg in kpkgs:
            kpkg = rpmtool.RPM(str(kpkg))            
            filename = kpkg.getFilename().basename() 
            desc = ' %s for %s' % (kpkg.summary,kpkg.arch)
            ns['kernels'].append({'name':kpkg.name, 'version':kpkg.version, \
                                  'release':kpkg.release, 'filename':filename})
 
        t = Template(file=str(template), searchList=[ns])  
        f = open(dest, 'w')
        f.write(str(t))
        f.close()
   
        return kpkgs 


