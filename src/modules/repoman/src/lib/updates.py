#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path

from kusu.util import rpmtool
from kusu.repoman.rhn import RHN
from kusu.util.errors import NotImplementedError

class BaseUpdate:
    def __init__(self, os_name, os_version, os_arch):
        self.os_name = os_name
        self.os_version = os_version
        self.os_arch = os_arch

    def getLatestRPM(self, dirs=[]):
        """Returns a dictionary of the latest rpms"""

        rpmPkgs = {}
        for dir in dirs:
            for r in dir.files():
                if r.ext == 'rpm' and r.basename() != 'TRANS.TBL':
                    r = rpmtool.RPM(str(r))
                    name = r.getName()
                    arch = r.getArch()

                    if rpmPkgs.has_key(name):
                        if rpmPkgs[name].has_key(arch):
                            if r > Pkgs[name][arch]:
                                rpmPkgs[name][arch] = r
                            else:
                                pass # Do nothing
                        else:    
                            rpmPkgs[name][arch] = r
                    else:
                        rpmPkgs[name] = {}
                        rpmPkgs[name][arch] = r

        return rpmPkgs

    def getUpdates(self, dir):
        """Gets the updates and writes them into the destination dir"""
        raise NotImplementedError

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

        rpmPkgs = self.getLatestRPM([path('/mnt/Server/')])
        
        self.rhn.login()
        channels = self.rhn.getChannels(self.rhn.getServerID())

        downloadPkgs = [] 
        for r in self.rhn.getLatestPackages(channels[0]['channel_label']):
            name = r.getName()
            arch = r.getArch()

            # There's a newer rpm, so download it
            if rpmPkgs.has_key(name) and \
               rpmPkgs[name].has_key(arch) and \
               r > rpmPkgs[name][arch]:
                downloadPkgs.append(r)

            # No such existing rpm, so download it
            if not rpmPkgs.has_key(name) or \
               (rpmPkgs.has_key(name) and not rpmPkgs[name].has_key(arch)):
                downloadPkgs.append(r)

        for r in downloadPkgs:
            filename = r.getFilename().basename()
            f = open(dir / filename, 'w')
            f.write(self.rhn.getPackage(filename, channels[0]['channel_label']))
            f.close()

        self.rhn.logout()


