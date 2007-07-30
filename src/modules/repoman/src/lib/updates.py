#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from path import path

from kusu.util import rpmtool
from kusu.repoman.rhn import RHN
from kusu.repoman.yum import YumRepo
from kusu.repoman.tools import getFile, getConfig
from kusu.util.errors import NotImplementedError, InvalidRPMHeader

class BaseUpdate:
    def __init__(self, os_name, os_version, os_arch, prefix):
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch
        
        self.prefix = prefix

    def getLatestRPM(self, dirs=[]):
        """Returns a list of the latest rpms"""
        return rpmtool.getLatestRPM(dirs, ignoreErrors=True)

    def getUpdates(self):
        """Gets the updates and writes them into the destination dir"""
        raise NotImplementedError

    def getSources(self):
        """Return the path of sources to compare against mirror"""
        raise NotImplementedError

    def getConfig(self, configFile):
        """Returns the configuration"""
        return getConfig(configFile)

class YumUpdate(BaseUpdate):
    def __init__(self,os_name, os_version, os_arch, prefix):
        BaseUpdate.__init__(self, os_name, os_version, os_arch, prefix)

    def getURI(self):
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
    
        primarys = {}
        for u in self.getURI():
            primarys[u] = YumRepo(u).getPrimary()

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

    def getLatestRPM(self, primarys):

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
    def __init__(self, os_version, os_arch, username, password, prefix):
        BaseUpdate.__init__(self, 'rhel', self.getOSMajorVersion(os_version), os_arch, prefix)
        self.rhn = RHN(username, password)
        
        # read config or something self.rhn =  
    def getOSMajorVersion(self, os_version):
        """Returns the major number"""
        return os_version.split('.')[0]

    def getUpdates(self):
        """Gets the updates and writes them into the destination dir"""

        dir = path(self.prefix) / 'depot' / 'updates' / self.os_name / self.getOSMajorVersion(self.os_version) / self.os_arch
        if not dir.exists():
            dir.makedirs()

        # Check whether the OS kit has been added
        osPath = self.getOSPath()
        if osPath.exists():
            # Look into the OS and updates dir
            rpmPkgs = rpmtool.getLatestRPM([osPath, dir], True)
        else:    
            # Just look at the updates dir
            rpmPkgs = rpmtool.getLatestRPM([dir], True)
        
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


