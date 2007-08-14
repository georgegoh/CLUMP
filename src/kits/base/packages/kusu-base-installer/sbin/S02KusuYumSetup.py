#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        Plugin.__init__(self)
        self.name = 'yumrepo'
        self.desc = 'Setting yum repos'
        self.ngtypes = ['installer']
        self.delete = False

    def run(self):
        """ Disable all other repos. """
        etcyumeposd = path('/etc/yum.repos.d')

        for repo in etcyumeposd.files('*.repo'):
            fh = open(repo, 'r')
            lines = fh.read().splitlines()
            fh.close()

            fh = open(repo, 'w')
            for line in lines:
                if line.find('enabled=')>=0:
                    fh.write('enabled=0\n')
                else:
                    fh.write(line+"\n")
            fh.close()

        """ Set up kusu.repo """
        kusurepo = path(etcyumeposd / 'kusu-%s.repo' % self.ngtypes[0])

        if not kusurepo.exists():
            kusurepo.touch()

        header = "[kusu-%s]\n" % self.ngtypes[0]
        name = "name=Kusu %s %s %s %s\n" % (self.ngtypes[0], self.os_name, self.os_version, self.os_arch)
        baseurl = "baseurl=http://%s/repos/%s\n" % (self.niihost[0], self.repoid)
        enabled = "enabled=1\n"
        gpgcheck = "gpgcheck=0\n"
        gpgkey = "gpgkey=http://%s/repos/%s/RPM-GPG-KEY-kusu-release\n" % (self.niihost[0], self.repoid)

        try:
            fh = open(kusurepo, 'w')
            fh.write(header)
            fh.write(name)
            fh.write(baseurl)
            fh.write(enabled)
            fh.write(gpgcheck)
            fh.write(gpgkey)
            fh.close()
            return True
        except:
            return False
