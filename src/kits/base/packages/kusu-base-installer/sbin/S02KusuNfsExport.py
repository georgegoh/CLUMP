#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core.plugin import Plugin

class KusuRC(Plugin):
    def __init__(self):
        Plugin.__init__(self)
        self.name = 'shared-home-export'
        self.desc = 'Setting up shared home nfs export'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setup /etc/exports"""
        etcexports = path('/etc/exports')
        sharedhomedir = path('/home')
        etcnodeautomaster = path('/etc/node.auto.master')
        etcnodeautohome = path('/etc/node.auto.home')

        if not etcnodeautomaster.exists():
            etcnodeautomaster.touch()

        if not etcnodeautohome.exists():
            etcnodeautohome.touch()

        myname = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue
        nics = self.dbs.Nodes.selectfirst_by(name=myname).nics

        privatenic = None
        for nic in nics:
            if nic.network.type == 'provision':
                privatenic = nic

        if not privatenic == None:
            newline = "%s %s/%s(rw,async)\n" % (sharedhomedir, privatenic.network.network, privatenic.network.subnet)

            f = open(etcexports, 'a')
            f.writelines(newline)
            f.close()
            
            retcode, out, err = self.runCommand('/sbin/chkconfig nfs on')
            retcode, out, err = self.runCommand('/etc/init.d/nfs restart')

            if retcode != 0:
                return False

            # set up automount maps for nodes
            newline = "/home\t/etc/auto.home"

            f = open(etcnodeautomaster, 'a')
            f.writelines(newline)
            f.close()

            newline = "* %s:%s/&" % (privatenic.ip, sharedhomedir)

            f = open(etcnodeautohome, 'a')
            f.writelines(newline)
            f.close()

            # place automount maps in web root
            webdir = path('/var/www/html')

            if not webdir.exists():
                webdir.makedirs()

            # copy automount maps to webdir
            (etcnodeautomaster).copy(webdir / 'auto.master')
            (etcnodeautohome).copy(webdir / 'auto.home')

            retcode, out, err = self.runCommand('/etc/init.d/autofs restart')

            if retcode != 0:
                return False

        return True

