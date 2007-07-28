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
from kusu.repoman.tools import getFile
from kusu.util.errors import NotImplementedError, InvalidRPMHeader

class BaseUpdate:
    def __init__(self, os_name, os_version, os_arch, debug=False):
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch
        self.debug = debug
        
    def getLatestRPM(self, dirs=[]):
        """Returns a list of the latest rpms"""
        return rpmtool.getLatestRPM(dirs, ignoreErrors=True)

    def getUpdates(self, dir):
        """Gets the updates and writes them into the destination dir"""
        raise NotImplementedError

    def getOSPath(self):
        """Return the path of the oldest OS"""
        raise NotImplementedError

class YumUpdate(BaseUpdate):
    def __init__(self, dbs, os_name, os_version, os_arch, uri = [], prefix=None):
        BaseUpdate.__init__(self, os_name, os_version, os_arch)
        self.dbs = dbs
        self.uri = uri

    def getOSPath(self):
        return path(os.path.join('/depot', 'kits', self.os_name, self.os_version, self.os_arch))
       
    def getUpdates(self, dir):
        """Gets the updates and writes them into the destination dir"""
     
        if not dir:
            dir = path('/depot/updates') / self.os_name / self.os_version / self.os_arch

            if not dir.exists():
                dir.makedirs()
        else:
            dir = path(dir)

        # Check whether the OS kit has been added
        osPath = self.getOSPath()
        if osPath.exists():
            # Look into the OS and updates dir
            rpmPkgs = rpmtool.getLatestRPM([osPath, dir])
        else:    
            # Just look at the updates dir
            rpmPkgs = rpmtool.getLatestRPM([dir])
        
        primarys = {}
        for u in self.uri:
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

        latest = []        
        for val in c.values():
            for listing in val.values():
                latest.append(listing[0])

        return latest
 
class RHNUpdate(BaseUpdate):
    def __init__(self, dbs, os_version, os_arch, username, password, prefix=None):
        BaseUpdate.__init__(self, 'rhel', self.getOSMajorVersion(os_version), os_arch)
        self.dbs = dbs
        self.rhn = RHN(username, password)

    def getOSMajorVersion(self, os_version):
        """Returns the major number"""
        return os_version.split('.')[0]

    def getOSPath(self):
        kits = self.dbs.Kits.select_by(rname=self.os_name,
                                       arch=self.os_arch)

        min_version = self.os_version
        for kit in kits:
            if self.getOSMajorVersion(kit.version) < min_version:
                min_version = kit.version

        return path(os.path.join('/depot', 'kits', self.os_name, min_version, self.os_arch))

    def getUpdates(self, dir=None):
        """Gets the updates and writes them into the destination dir"""

        if not dir:
            dir = path('/depot/updates') / self.os_name / self.getOSMajorVersion(self.os_version) / self.os_arch

            if not dir.exists():
                dir.makedirs()
        else:
            dir = path(dir)

        # Check whether the OS kit has been added
        osPath = self.getOSPath()
        if osPath.exists():
            # Look into the OS and updates dir
            rpmPkgs = rpmtool.getLatestRPM([osPath, dir])
        else:    
            # Just look at the updates dir
            rpmPkgs = rpmtool.getLatestRPM([dir])
        
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


