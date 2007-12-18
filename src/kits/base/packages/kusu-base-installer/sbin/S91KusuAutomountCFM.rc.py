#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
import sys

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'setup-cfm-automount-maps'
        self.desc = 'Setting up automount maps for cfm'
        self.ngtypes = ['installer']
        self.delete = False

    def run(self):
        sharedhomedir = path('/home')

        myname = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue
        nics = self.dbs.Nodes.selectfirst_by(name=myname).nics

        masternics = {}

        for nic in nics:
            if nic.network.type == 'provision':
                key = "%s/%s" % (nic.network.network,nic.network.subnet)
                masternics[key] = nic.ip

        ngs = self.dbs.NodeGroups.select()
        for ng in ngs:
            if ng.ngname == 'unmanaged':
                continue
            cfmautomaster = path('/etc/cfm/%s/etc/auto.master' % ng.ngname)
            if cfmautomaster.exists():
                cfmautomaster.unlink()
            cfmautomaster.touch()
            newline = "/home\t/etc/auto.home\n"
            f = open(cfmautomaster, 'a')
            f.writelines(newline)
            f.close()
            
            cfmautohome = path('/etc/cfm/%s/etc/auto.home' % ng.ngname)
            if cfmautohome.exists():
                cfmautohome.unlink()
            cfmautohome.touch()
            f1 = open(cfmautohome,'a')
            networks = ng.networks
            for network in networks:
                if nic.network.type == 'provision':
                    key = "%s/%s" % (network.network,network.subnet)
                    if key in masternics:
                        newline = "* %s:%s/&\n" % (masternics[key], sharedhomedir)
                        f1.writelines(newline)
            f1.close()
        
        # Redirect all stdout, stderr
        oldOut = sys.stdout
        oldErr = sys.stderr
        f = open('/dev/null', 'w')
        sys.stdout = f
        sys.stderr = f

        # Update the cfm files
        from kusu.cfms import PackBuilder
        from kusu.core import app
        kApp = app.KusuApp()
        _ = kApp.langinit()
        pb = PackBuilder(kApp.errorMessage, kApp.stdoutMessage)
        size = pb.updateCFMdir()
        pb.genFileList()

        # Restore stdout and stderr
        sys.stdout = oldOut
        sys.stderr = oldErr

        return True

