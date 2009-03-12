#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

from kusu.core import rcplugin 
import os
import string

from path import path
from primitive.system.software.dispatcher import Dispatcher
from primitive.support import osfamily
from kusu.util.errors import UnsupportedOS

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name    = 'nicstart'
        self.desc    = 'Initializing other NIC interfaces'
        self.ngtypes = ['compute', 'compute-imaged', 'compute-diskless']
        self.delete  = False
        self.nics    = {}   # Dictionary of all the NIC info

    def run(self):
        """Creating config files for all devices.
        The data comes from the profile.nii and looks like:
           # NIC Definitions Device:IP:Subnet:Network:suffix:gateway:dhcp:options:mac:type
           export NII_NICDEF0="eth2|10.10.0.1|255.255.0.0|10.10.0.0|-eth2|10.10.0.1|0||00:0C:29:5A:48:AD|public"
           export NII_NICDEF1="eth1|172.25.243.23|255.255.255.0|172.25.243.0|-eth1|172.25.243.2|0||08:00:27:f0:59:9a|provision"
        """
        
        profile = '/etc/profile.nii'
        if not os.path.exists(profile):
            return False

        fp = open(profile, 'r')
        lines = fp.readlines()
        fp.close()

        mcast_static_route_added = False

        for line in lines:
            if line[0] == "#" or line.isspace():
                continue

            try:
                key,val = string.split(line, '=', 1)
            except:
                continue
            
            if key[:17] != 'export NII_NICDEF':
                continue

            try:
                val = val.rstrip()
                val = val.strip('"')
                dev,ip,sn,net,suf,gw,dhcp,opts,mac,network_type = string.split(val, '|', 9)
            except:
                continue
            
            if dhcp != '0' and dhcp != '1':
                # Bad data
                continue

            if dev != 'bmc':
                # It's a normal NIC

                if network_type == 'provision' and not mcast_static_route_added:
                    if not self.setupMcastStaticRoute(dev):
                        return False
                    mcast_static_route_added = True
                
                network_path = path(Dispatcher.get('networkscripts_path'))

                if dev.startswith('ib'):
                    ifcfg = path(network_path / 'ifcfg-%s' % dev)
                else:
                    if self.os_name in ['rhel', 'centos', 'scientificlinux', 'fedora', 'opensuse']:
                        ifcfg = path(network_path / 'ifcfg-%s' % dev)
                    elif self.os_name in ['suse', 'sles']:
                        ifcfg = path(network_path / 'ifcfg-eth-id-%s' % mac)

                if ifcfg.exists():
                    print "\n      Configuration for %s already exists!  Skipping.\n" % dev
                    continue

                fp = open(ifcfg, 'w')
                fp.write('# Added by Kusu\n')
                fp.write('DEVICE=%s\n' % dev)
                fp.write('ONBOOT=yes\n')
                if dhcp == '0':
                    fp.write('BOOTPROTO=static\n')
                    fp.write('IPADDR=%s\n' % ip)
                    fp.write('NETWORK=%s\n' % net)
                    fp.write('NETMASK=%s\n' % sn)
                    # No support for HWADDR yet...
                    # Don't think BROADCAST is needed
                else:
                    fp.write('BOOTPROTO=dhcp\n')

                fp.close()

                # Bring up NIC
                ifup_path = path(Dispatcher.get('ifup_path'))
                cmd = '%s %s' % (ifup_path / 'ifup', dev)
                os.system(cmd)

            else:
                # Put the code to configure BMC here
                rcfile = '/etc/rc.kusu.d/S99DellBMCSetup'
                if os.path.exists(rcfile):
                    os.system("%s %s %s %s" % (rcfile, ip, gw, sn))
                os.unlink(rcfile)

        return True

    def setupMcastStaticRoute(self, dev=None):
        """
        Adds a static route for the multicast network
        on the first nic on the 'provision' network.
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

