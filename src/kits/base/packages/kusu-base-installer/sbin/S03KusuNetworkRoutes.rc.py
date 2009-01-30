#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
from kusu.core import rcplugin
import kusu.core.database as db
import os

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'network_routes'
        self.desc = 'Setting up network routes'
        self.ngtypes = ['installer']
        self.delete = False # needs to run every time the master boots up

    def run(self):
        self.setupMcastStaticRoute()
        return True

    def setupMcastStaticRoute(self):
        """
        Adds a static route for the multicast network
        on the first master nic on the 'provision' network.
        Needed for apps like ganglia v3.1.1 to work properly 
        when it tries to send out multicast UDP packets.
        """
        device = self.getFirstProvisionDevice()

        if device:
            self.runCommand('/sbin/route add -net 239.0.0.0 netmask 255.0.0.0 %s' % device)

    def getFirstProvisionDevice(self):
        """Get from kusudb the first device on the provision network."""
        master_name = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue

        master = self.dbs.Nodes.selectfirst_by(name=master_name)
        for nic in master.nics:
            if nic.network.type == 'provision':
                return nic.network.device
        
        return None

