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
from kusu.util.errors import NotImplementedError, InvalidRPMHeader

class BaseUpdate:
    def __init__(self, os_name, os_version, os_arch):
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch

    def getLatestRPM(self, dirs=[]):
        """Returns a dictionary of the latest rpms"""
        return rpmtool.getLatestRPM(dirs, ignoreErrors=True)

    def getUpdates(self, dir):
        """Gets the updates and writes them into the destination dir"""
        raise NotImplementedError

    def getOSPath(self):
        """Return the path of the OS"""
        return path(os.path.join('/depot', 'kits', self.os_name, self.os_version, self.os_arch))

class RHNUpdate(BaseUpdate):
    def __init__(self, os_version, os_arch, username, password):
        BaseUpdate.__init__(self, 'rhel', os_version, os_arch)

        self.rhn = RHN(username, password)
 
    def getUpdates(self, dir=None):
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
            rpmPkgs = self.getLatestRPM([osPath, dir])
        else:    
            # Just look at the updates dir
            rpmPkgs = self.getLatestRPM([dir])
        
        self.rhn.login()
        channels = self.rhn.getChannels(self.rhn.getServerID())

        downloadPkgs={}
        for channel in channels:
            downloadPkgs[channel['channel_label']] = []
        
        for channel in downloadPkgs.keys():
            for r in self.rhn.getLatestPackages(channel):
                name = r.getName()
                arch = r.getArch()

                # There's a newer rpm, so download it
                if rpmPkgs.has_key(name) and \
                   rpmPkgs[name].has_key(arch) and \
                   r > rpmPkgs[name][arch]:
                    downloadPkgs[channel].append(r)

                # No such existing rpm, so download it
                if not rpmPkgs.has_key(name) or \
                   (rpmPkgs.has_key(name) and not rpmPkgs[name].has_key(arch)):
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


