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
        kitArch = self.os_arch

        if self.prefix:
            tempkitdir = path(tempfile.mkdtemp(prefix='repoman_buildkit', dir=self.prefix))
            kitdir = path(tempfile.mkdtemp(prefix='repoman_kit', dir=self.prefix))
        else:
            tempkitdir = path(tempfile.mkdtemp(prefix='repoman_buildkit', dir=os.environ.get('KUSU_TMP', '/tmp/kusu')))
            kitdir = path(tempfile.mkdtemp(prefix='repoman_kit', dir=os.environ.get('KUSU_TMP', '/tmp/kusu')))

        self.prepKit(tempkitdir, kitName)
        self.makeKitScript(tempkitdir, kitName, kitRelease)

        for p in pkgs:
            file = p.getFilename()
            dest = tempkitdir / kitName / 'packages' / file.basename()

            # Use abs symlink. Relative links does not work
            # when buildkit prepares temp new directory for
            # making kit
            file.symlink(dest) 
        
        self.makeKit(tempkitdir, kitdir, kitName)

        return kitdir

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

        if not (self.prefix / 'tftpboot' / 'kusu').exists():
            raise DirDoesNotExistError, '%s not found' % (self.prefix /  'tftpboot' / 'kusu')

        tempdir = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ.get('KUSU_TMP', '/tmp/kusu')))
             
        if rpm.extract(tempdir):
            raise Exception

        if self.os_name in ['fedora', 'rhel', 'centos']:
            vmlinuz = (tempdir / 'boot').listdir('vmlinuz*')[0]

        newVmlinuz = self.prefix / 'tftpboot' / 'kusu' / \
                     'kernel-%s-%s-%s.%s' % (self.os_name,self.os_version,self.os_arch,updateRelease)
        vmlinuz.copy(newVmlinuz)
        
        try:
            tempdir.rmtree()
        except: pass

        return (newVmlinuz, None)

    def makeKitScript(self, tempkitdir, kitName, kitRelease):

        dest = tempkitdir / kitName / 'build.kit'
        out = open(dest, 'w')

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        template = kusu_root / 'etc' / 'repoman-templates' / 'update.kit.tmpl'

        ns = {}
        ns['kitname'] = kitName
        ns['kitver'] = '%s_r%s' % (self.os_version, kitRelease)
        ns['kitrel'] = kitRelease
        ns['kitarch'] = self.os_arch
        ns['kitdesc'] = ''
        
        t = Template(file=str(template), searchList=[ns])  
        out.write(str(t))
        out.close()
    
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

        # Donwload the packages
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

        return rpmtool.getLatestRPM([dir], True).getList()

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
    def __init__(self, os_version, os_arch, cfg, prefix, db):
        BaseUpdate.__init__(self, 'rhel', self.getOSMajorVersion(os_version), os_arch, prefix, db)

        if cfg.has_key('url'):
            url = cfg['url']
        else:
            url = None

        username = cfg['username']
        password = cfg['password']

        self.rhn = RHN(username, password, url)
        
    def getOSMajorVersion(self, os_version):
        """Returns the major number"""
        return os_version.split('.')[0]

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

        return rpmtool.getLatestRPM([dir], True).getList()
