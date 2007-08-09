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

from kusu.util import rpmtool
from kusu.repoman.rhn import RHN
from kusu.repoman.yum import YumRepo
from kusu.repoman.tools import getFile, getConfig
from kusu.util.errors import *

try:
    import subprocess
except:
    from popen5 import subprocess

class BaseUpdate:
    def __init__(self, os_name, os_version, os_arch, prefix, db):
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch
        
        self.prefix = prefix
        self.db = db
        self.configFile = None

    def getLatestRPM(self, dirs=[]):
        """Returns a list of the latest rpms"""
        return rpmtool.getLatestRPM(dirs, ignoreErrors=True)

    def getUpdates(self):
        """Gets the updates and writes them into the destination dir"""
        raise NotImplementedError

    def makeUpdateKit(self, pkgs):
        """Makes the update kit"""

        kitName = '%s-updates' % self.os_name 
        kitRelease = self.getNextRelease(kitName)
        kitVersion = '%s_r%s' % (self.os_version, kitRelease)
        kitArch = self.os_arch

        if self.prefix:
            tempkitdir = path(tempfile.mkdtemp(prefix='repoman_buildkit', dir=self.prefix))
            kitdir = path(tempfile.mkdtemp(prefix='repoman_kit', dir=self.prefix))
        else:
            tempkitdir = path(tempfile.mkdtemp(prefix='repoman_buildkit', dir=os.environ.get('KUSU_TMP', '/tmp/kusu')))
            kitdir = path(tempfile.mkdtemp(prefix='repoman_kit', dir=os.environ.get('KUSU_TMP', '/tmp/kusu')))

        self.prepKit(tempkitdir, kitName)
        self.makeKitScript(tempkitdir, kitName, kitVersion, kitRelease)

        for p in pkgs:
            file = p.getFilename()
            dest = tempkitdir / kitName / 'packages' / file.basename()

            # Use abs symlink. Relative links does not work
            # when buildkit prepares temp new directory for
            # making kit
            file.symlink(dest) 
        
        self.makeKit(tempkitdir, kitdir, kitName)

        return (kitdir, kitName, kitVersion, kitRelease, kitArch)

    def getNextRelease(self, kitName):
        # Find max version
        kits = [kit.version for kit in self.db.Kits.select_by(rname = kitName)]
        if kits:
            maxRelease = 0

            for kitversion in kits:
                c = re.compile('r[\d]+') 
                matches = c.findall(kitversion)
                if matches:
                    # Takw away rXXX
                    release = int(matches[0][1:])
                    if release > maxRelease:
                        maxRelease = release
        else:
            maxRelease = 0

        return maxRelease + 1

    def makeTFTP(self, rpm, updateRelease):

        ostype = '%s-%s-%s' % (self.os_name,self.os_version,self.os_arch)

        tftpbootDir = path(self.prefix / 'tftpboot' / 'kusu')
        if not tftpbootDir.exists():
            raise DirDoesNotExistError, '%s not found' % (tftpbootDir)

        tempdir = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ.get('KUSU_TMP', '/tmp/kusu')))
             
        if rpm.extract(tempdir):
            raise UnableToExtractKernel, rpm.getFilename()

        if self.os_name in ['fedora', 'rhel', 'centos']:
            vmlinuz = path(tempdir / 'boot').listdir('vmlinuz*')[0]

        newVmlinuz = None
        if vmlinuz.exists():
            newVmlinuz = path(tftpbootDir / 'kernel-%s.%s' % (ostype, updateRelease))
            vmlinuz.copy(newVmlinuz)
       
        initrd = path(tftpbootDir / 'initrd-%s.img' % (ostype))
        newInitrd = None
        if initrd.exists():
            newInitrd = path(tftpbootDir / 'initrd-%s.%s.img' % (ostype, updateRelease))
            # pack and unpack 
            # image.unpack() 
            initrd.copy(newInitrd)
        
        try:
            tempdir.rmtree()
        except: pass

        return (newVmlinuz.basename(), newInitrd.basename())

    def updateKernelInfo(self, repoid, vmlinuz, initrd):
        ngs = self.db.NodeGroups.select_by(repoid = repoid)

        for ng in ngs:
            ng.kernel = vmlinuz
            ng.initrd = initrd
            ng.save()
            ng.flush()

    def addUpdateKit(self, kitdir):
        from kusu.kitops import kitops

        ko = kitops.KitOps()
        ko.setDB(self.db) 
        ko.setKitMedia(kitdir)
        kits = ko.addKitPrepare()
        ko.addKit(kits[0])
   
        return kits[0]
 
    def makeKitScript(self, tempkitdir, kitName, kitVersion, kitRelease):

        compclass = {'rhel' : {'5': 'RHEL5Component()'},
                     'centos' : {'5': 'Centos5Component()'},
                     'fedora' : {'6': 'Fedora6Component()'}}
 
        dest = tempkitdir / kitName / 'build.kit'

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        template = kusu_root / 'etc' / 'repoman-templates' / 'update.kit.tmpl'

        ns = {}
        ns['kitname'] = kitName
        ns['kitver'] = kitVersion
        ns['kitrel'] = kitRelease
        ns['kitarch'] = self.os_arch
        ns['kitdesc'] = 'Updates for %s %s %s on %s' % \
                        (self.os_name, self.os_version, self.os_arch, time.asctime())
        ns['compclass'] = compclass[self.os_name][self.os_version]
        
        t = Template(file=str(template), searchList=[ns])  
        f = open(dest, 'w')
        f.write(str(t))
        f.close()
    
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
            raise UnableToPrepUpdateKit, err

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
            return True
        else:
            raise UnableToMakeUpdateKit, err

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
    
        dir = path(self.prefix) / 'depot' / 'updates' / self.os_name / self.os_version / self.os_arch
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
                    rpmtool.RPM(dest)
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

        if rpmPkgs.has_key('kernel'):
            if self.os_arch == 'x86_64':
                # We want to use x64 kernel
                kernelRPM = rpmPkgs['kernel']['x86_64'][0]
            elif self.os_arch == 'i386':
                # Take the lowest arch
                if rpmPkgs['kernel'].has_key('i386'):
                    kernelRPM = rpmPkgs['kernel']['i386'][0]
                elif rpmPkgs['kernel'].has_key('i486'):
                    kernelRPM = rpmPkgs['kernel']['i486'][0]
                elif rpmPkgs['kernel'].has_key('i586'):
                    kernelRPM = rpmPkgs['kernel']['i586'][0]
                elif rpmPkgs['kernel'].has_key('i686'):
                    kernelRPM = rpmPkgs['kernel']['i686'][0]
        else:
            kernelRPM = None

        return (rpmPkgs.getList(), kernelRPM)

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
        BaseUpdate.__init__(self, 'rhel', self.getOSMajorVersion(os_version), os_arch, prefix, db)
        self.rhn = None

    def getOSMajorVersion(self, os_version):
        """Returns the major number"""
        return os_version.split('.')[0]

    def getRHN(self):
        if self.configFile:
            cfg = self.getConfig(self.configFile)['rhel']
            username = cfg['username']
            password = cfg['password']
            url = cfg['url']
            return RHN(username, password, url)

        else:
            raise rhnNoAccountInformationProvidedError

    def getUpdates(self):
        """Gets the updates and writes them into the destination dir"""

        dir = path(self.prefix) / 'depot' / 'updates' / \
              self.os_name / self.getOSMajorVersion(self.os_version) / self.os_arch
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
      
        if not self.rhn: 
            self.rhn = self.getRHN()
        
        self.rhn.login()
        channels = self.rhn.getChannels(self.rhn.getServerID())

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
                        rpmtool.RPM(dest)
                        continue
                    except:
                        # corrupted/incomplete/etc
                        dest.remove()

                content = self.rhn.getPackage(filename, channel)
                if content:
                    f = open(dest, 'w')
                    f.write(content)
                    f.close()

        try:
            self.rhn.logout()
        except: pass

        rpmPkgs = rpmtool.getLatestRPM([dir], True)

        if rpmPkgs.has_key('kernel'):
            if self.os_arch == 'x86_64':
                # We want to use x64 kernel
                kernelRPM = rpmPkgs['kernel']['x86_64'][0]
            elif self.os_arch == 'i386':
                # Take the lowest arch
                if rpmPkgs['kernel'].has_key('i386'):
                    kernelRPM = rpmPkgs['kernel']['i386'][0]
                elif rpmPkgs['kernel'].has_key('i486'):
                    kernelRPM = rpmPkgs['kernel']['i486'][0]
                elif rpmPkgs['kernel'].has_key('i586'):
                    kernelRPM = rpmPkgs['kernel']['i586'][0]
                elif rpmPkgs['kernel'].has_key('i686'):
                    kernelRPM = rpmPkgs['kernel']['i686'][0]
        else:
            kernelRPM = None

        return (rpmPkgs.getList(), kernelRPM)
