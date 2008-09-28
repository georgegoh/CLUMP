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

        # Remove the following line once the autofs bug is fixed
        self.disable = True

    def run(self):
        sharedhomedir = path('/home')

        myname = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue
        nics = self.dbs.Nodes.selectfirst_by(name=myname).nics

        # Get all interfaces with type 'provision'
        masternics = {}
        for nic in nics:
            if nic.network.type == 'provision':
                key = "%s/%s" % (nic.network.network,nic.network.subnet)
                masternics[key] = nic.ip

        ngs = self.dbs.NodeGroups.select()
        for ng in ngs:
            cfmautomaster = path('/etc/cfm/%s/etc/auto.master' % ng.ngname)
            if cfmautomaster.exists():
                cfmautomaster.unlink()

            cfmautohome = path('/etc/cfm/%s/etc/auto.home' % ng.ngname)
            if cfmautohome.exists():
                cfmautohome.unlink()

            # Do not manage auto.home on nodes in the 'unmanaged' nodegroup
            # or installers.
            if ng.ngname == 'unmanaged' or ng.type == 'installer':
                continue

            entries = []
            for network in ng.networks:
                key = "%s/%s" % (network.network,network.subnet)
                if key in masternics:
                    entries.append("* %s:%s/&\n" % (masternics[key], sharedhomedir))

            # If there's nothing to add to auto.home, do not create the file
            # at all nor create auto.master since currently the only entry
            # it references is auto.home.
            if not entries:
                continue

            fheader = "# THIS FILE IS GENERATED BY KUSU.  ANY CHANGES WILL BE OVERWRITTEN.\n\n"

            # auto.home
            f1 = open(cfmautohome,'w')
            entries.insert(0, fheader)
            f1.writelines(entries)
            f1.close()

            # auto.master
            f = open(cfmautomaster, 'w')
            f.writelines([ fheader, "/home\t/etc/auto.home\n" ])
            f.close()

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
