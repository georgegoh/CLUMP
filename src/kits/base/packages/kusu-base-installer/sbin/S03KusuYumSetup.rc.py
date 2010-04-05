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
from primitive.system.software.probe import OS

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'yumrepo'
        self.desc = 'Setting up yum repos'
        self.ngtypes = ['installer']
        self.delete = True

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

        # """ Remove yum-rhn-plugin if exists. """
        # retcode, out, err = self.runCommand('rpm -qa | grep yum-rhn-plugin')
        # if retcode == 0 and len(out) > 0:
        #   retcode, out, err = self.runCommand("rpm -ev " + out)

        header = "[kusu-%s]\n" % self.ngtypes[0]
        name = "name=Kusu %s %s %s %s\n" % (self.ngtypes[0], self.os_name, self.os_version, self.os_arch)
        enabled = "enabled=1\n"
        gpgcheck = "gpgcheck=0\n"
        gpgkey = "gpgkey=http://%s/repos/%s/RPM-GPG-KEY-KUSU\n" % (self.niihost[0], self.repoid)

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
                dirname = Dispatcher.get('yum_repo_subdir', 'Server')
                baseurl = "baseurl=http://%s/repos/%s%s\n" % (self.niihost[0], self.repoid, dirname)
                fh = open(kusurepo, 'w')
                fh.write(header)
                fh.write(name)
                fh.write(baseurl)
                fh.write(enabled)
                fh.write(gpgcheck)
                fh.write(gpgkey)
            fh.close()
        except:
            return False

        self.runCommand('/bin/rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-KUSU')

        gpgKeyFile = Dispatcher.get('rpm_gpg_key', '', OS())
        if gpgKeyFile:
            self.runCommand('/bin/rpm --import %s' % gpgKeyFile)

        return True
