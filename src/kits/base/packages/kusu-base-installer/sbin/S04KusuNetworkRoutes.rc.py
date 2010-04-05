#!/usr/bin/env python
# $Id: S04KusuNetworkRoutes.rc.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
from kusu.core import rcplugin
import kusu.core.database as db
from kusu.util.errors import UnsupportedOS
from path import path
from primitive.support import osfamily

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'network_routes'
        self.desc = 'Setting up network routes'
        self.ngtypes = ['installer']
        self.delete = False # needs to run every time the master boots up

    def run(self):
        dev = self.getFirstProvisionDevice()
        return self.setupMcastStaticRoute(dev)

    def setupMcastStaticRoute(self, dev=None):
        """
        Adds a static route for the multicast network
        on the first master nic on the 'provision' network.
        Needed for apps like ganglia v3.1.1 to work properly 
        when it tries to send out multicast UDP packets.
        Returns False if this is not a supported OS.
        Returns True otherwise.
        """
        if dev:
            self.runCommand('/sbin/route add -net 239.0.0.0 netmask 255.0.0.0 %s' % dev)

            try:
                self.addMcastStaticRouteConfig(self.os_name, dev)
            except UnsupportedOS:
                return False

        return True

    def getFirstProvisionDevice(self):
        """Get from kusudb the first device on the provision network."""
        master_name = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue

        master = self.dbs.Nodes.selectfirst_by(name=master_name)
        for nic in master.nics:
            if nic.network.type == 'provision':
                return nic.network.device
        
        return None

    def addMcastStaticRouteConfig(self, os_name=None, dev=None):
        """
        Set up static route in config files so that it
        survives a 'service network restart'.
        """
        if os_name and dev:
            if os_name in ['sles', 'opensuse', 'suse']:
                line = '239.0.0.0       0.0.0.0         255.0.0.0       %s' % dev
                routes_file = path('/etc/sysconfig/network/routes')
            elif os_name in osfamily.getOSNames('rhelfamily'):
                line = '239.0.0.0/8 dev %s' % dev
                routes_file = path('/etc/sysconfig/network-scripts/route-%s' % dev)
            else:
                raise UnsupportedOS
            if not routes_file.exists():
                routes_file.touch()
            if not routes_file.text().find(line) > -1:
                routes_file.write_lines([line], append=True)

