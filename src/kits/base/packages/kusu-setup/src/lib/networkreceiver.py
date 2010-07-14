#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import sys
try:
    import subprocess
except ImportError:
    from popen5 import subprocess

import os
from path import path
from operator import itemgetter
from setup_errors import KusuProbePluginError
from primitive.support import osfamily
from primitive.system.hardware import probe
import kusu.ipfun as ipfun
from primitive.support.util import runCommand

RHELFAMILY_NETWORKFILE_PATH = '/etc/sysconfig/network-scripts/'
SLESFAMILY_NETWORKFILE_PATH = '/etc/sysconfig/network/'

class NetworkReceiver(object):

    def __init__(self, distroName):
        super(NetworkReceiver, self).__init__()
        self._distro = distroName
        self.servingDhcp = None
        self.intf = None
        self.intf_property = None

    def get_provisioning_interface(self):
        """ Interface to expose the provisioning interface selected by the user.
            This method should ideally be called after the run method. """
        return self.intf, self.intf_property

    def get_dhcp_status(self):
        """ Returns True if Installer is serving DHCP. """
        return self.servingDhcp

    def hasRPM(self, rpmName):
        outStr, errStr = runCommand("rpm -qai %s" % rpmName)
        if outStr.find(rpmName) >= 0 :
            return True
        else:
            return False

    def is_static(self, interface, properties, distro):
        if distro.lower() in osfamily.getOSNames('rhelfamily') + ['fedora']:
            network_file = RHELFAMILY_NETWORKFILE_PATH + 'ifcfg-%s' % interface
            if path(network_file).exists():
                return self._get_boot_protocol(network_file)

        elif distro.lower() in ['sles', 'opensuse', 'suse']:
            network_file = SLESFAMILY_NETWORKFILE_PATH + 'ifcfg-%s' % interface
            if path(network_file).exists():
                return self._get_boot_protocol(network_file)
            else:
                network_file = SLESFAMILY_NETWORKFILE_PATH + 'ifcfg-eth-id-%s' % properties[interface]['hwaddr']
                if path(network_file).exists():
                    return self._get_boot_protocol(network_file)

        return False

    def _get_boot_protocol(self, file):
       fp = open(file, 'r')
       value = None
       for line in fp.readlines():
           line.strip()
           if line.startswith('#'):
               continue
           if line.startswith('BOOTPROTO'):
               value = line.split('=')[1].rstrip()
               break

       fp.close()
       if value and value.lower() != 'dhcp':
           return True
       else:
           return False

    def is_dhcp_installed(self):
        """
            Testing for the package install is sufficient
        """
        return self.hasRPM('dhcp')

    def is_dns_installed(self):
        return self.hasRPM('bind')

    def _get_physical_interfaces(self):
        sel_intfs = []
        sel_interfaces = {}
        interfaces = probe.getPhysicalInterfaces()
        intfs = sorted(interfaces)
        for intf in intfs:
            if self.is_static(intf, interfaces[intf], self._distro):
                sel_intfs.append(intf)
                sel_interfaces[intf] = interfaces[intf]

        return sel_intfs, sel_interfaces


    def _get_nameservers(self):
        nslist = []
        if os.path.exists('/etc/resolv.conf'):
            file = open('/etc/resolv.conf')
            for line in file.readlines():
                if line.find('nameserver') >= 0:
                    lst = line.split()
                    if len(lst) >= 2 and ipfun.validIP(lst[1]):    #add ip validation
                        nslist.append(lst[1])

        return nslist

    #physicalInterfacesAndProperties property exposes a tuple : (interfaces, properties)
    physicalInterfacesAndProperties = property(_get_physical_interfaces)

    #nameservers property is a list of (ns,ip) tuples
    nameservers = property(_get_nameservers)


if __name__ == '__main__':
    networkReceiver = NetworkReceiver()
    intf, properties = networkReceiver.physicalInterfacesAndProperties
