#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
from primitive.system.software.dispatcher import Dispatcher

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'yumrepo'
        self.desc = 'Setting client yum repos'
        self.ngtypes = ['compute', 'compute-imaged', 'compute-diskless', 'other']
        self.delete = False

        # Bypass this rc script for sles
        if self.os_name in ['sles', 'opensuse', 'suse']:
            self.disable = True

    def run(self):
        """ Disable all other repos. """
        etcyumeposd = path('/etc/yum.repos.d')

        """ Set up kusu.repo """
        kusurepo = path(etcyumeposd / 'kusu-%s.repo' % self.ngtypes[0])

        if not kusurepo.exists():
            kusurepo.touch()

        for repo in etcyumeposd.files('*.repo'):
            if repo.basename() == kusurepo.basename():
                continue

            newFile = path(etcyumeposd / '%s.disable' % repo.basename())
            if newFile.exists(): newFile.remove()
            repo.move(newFile)

        dirname = Dispatcher.get('yum_repo_subdir', 'Server')

        header = "[kusu-%s]\n" % self.ngtypes[0]
        name = "name=Kusu %s %s %s %s\n" % (self.ngtypes[0], self.os_name, self.os_version, self.os_arch)
        enabled = "enabled=1\n"
        gpgcheck = "gpgcheck=0\n"
        gpgkey = "gpgkey=http://%s/repos/%s/RPM-GPG-KEY-kusu-release\n" % (self.niihost[0], self.repoid)

        try:
            fh = open(kusurepo, 'w')
            if self.os_name == "rhel" and self.os_version == "5":
                for dtype in ['Server', 'Cluster', 'ClusterStorage', 'VT']:
                    header = "[kusu-%s-%s]\n" % (self.ngtypes[0], dtype)
                    baseurl = "baseurl=http://%s/repos/%s/%s\n" % (self.niihost[0], self.repoid, dtype)
                    fh.write(header)
                    fh.write(name)
                    fh.write(baseurl)
                    fh.write(enabled)
                    fh.write(gpgcheck)
                    fh.write(gpgkey+"\n")
            else:
                baseurl = "baseurl=http://%s/repos/%s%s\n" % (self.niihost[0], self.repoid, dirname)
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
