#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
# This file is derived from S91KusuAutomountCFM.rc.py and is implemented
# as a workaround for an autofs bug.
#

from path import path
from kusu.core import rcplugin
import sys
import kusu.ipfun as ipfun

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'setup-fstab'
        self.desc = 'Setting up fstab for home directories'
        self.ngtypes = ['installer']
        self.delete = False

        # Set the following to true if reverting to the autofs functionality
        self.disable = False

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
            # Do not manage auto.home on nodes in the 'unmanaged' nodegroup
            # or installers.
            if ng.ngname == 'unmanaged' or ng.type == 'installer':
                continue

            entries = []
            bFound = False
            for network in ng.networks:
                for key, ip in masternics.iteritems():
                    if ipfun.onNetwork(network.network, network.subnet, ip):
                        # Only one entry for the fstab
                        entries.append("%s:%s /home nfs defaults 0 0\n" % (
                            ip, sharedhomedir ))
                        bFound = True
                        break

                if bFound:
                    break

            # If there's nothing to add to auto.home, do not create the file
            # at all nor create auto.master since currently the only entry
            # it references is auto.home.
            if not entries:
                continue

            # Use CFM append mechanism to append the entry for the home
            # NFS mount
            fstab_append = path('/etc/cfm/%s/etc/fstab.append' % ng.ngname)

            f = open(fstab_append, 'w')
            f.writelines(entries)
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

