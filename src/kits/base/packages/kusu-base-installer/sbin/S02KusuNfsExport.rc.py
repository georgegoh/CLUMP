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
        rcplugin.Plugin.__init__(self)
        self.name = 'shared-home-export'
        self.desc = 'Setting up shared home nfs export'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setup /etc/exports"""
        etcexports = path('/etc/exports')
        path('/opt/software').makedirs()
        sharedhomedirs = [path('/home'), path('/opt/software')]

        myname = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue
        nics = self.dbs.Nodes.selectfirst_by(name=myname).nics

        f = open(etcexports, 'a')
        for sharedhomedir in sharedhomedirs:
            newline = "%s " % sharedhomedir
            f.writelines(newline)
            for nic in nics:
                if nic.network.type == 'provision':
                    netname = nic.network.netname
                    newline = "%s/%s(rw,async)\n" % (nic.network.network, nic.network.subnet)
                    f.writelines(newline)

        f.close()

        retcode, out, err = self.runCommand('/sbin/chkconfig nfs on')
        retcode, out, err = self.runCommand('/etc/init.d/nfs restart')

        if retcode != 0:
            return False

        return True

