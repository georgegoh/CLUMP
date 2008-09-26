#!/usr/bin/env python

#
#  Copyright (C) 2008 Platform Computing
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

import sys
import os
import string
import glob
import kusu.ipfun

NETWORK='/etc/sysconfig/network'

def findGateway(netsyscfgfile=NETWORK):
    gateway = ''

    if not os.path.exists(netsyscfgfile):
        return gateway

    fin = open(netsyscfgfile, 'r')
    lines = fin.readlines()
    fin.close()
    for line in lines:
        if line[0] == "#":
            continue
        try:
            key,val = string.split(line, '=', 1)
        except:
            continue

        if key == 'GATEWAY':
             gateway = string.rstrip(val)

    return gateway

def getNicSettings(cfgfilename, gateway=None):
    mac     = ''
    ip      = ''
    device  = ''
    netmask = ''
    network = ''
    dev_gateway = ''
    dhcp    = False
    bEnableOnBoot = False
    validNic = 0
    nic = {}

    fin = open(cfgfilename, 'r')
    lines = fin.readlines()
    fin.close()
    for line in lines:
        if line[0] == "#":
            continue
        try:
            key,val = string.split(line, '=', 1)
            val = val.rstrip()
        except:
            continue
        if key == 'DEVICE':
            device = string.rstrip(val)
        elif key == 'HWADDR':
            mac = string.rstrip(val)
        elif key == 'IPADDR':
            ip = string.rstrip(val)
            validNic = 1
        elif key == 'NETMASK':
            netmask = string.rstrip(val)
        elif key == 'BOOTPROTO':
            validNic = 1
            dhcp = (string.rstrip(val) == 'dhcp')
        elif key == 'ONBOOT':
            bEnableOnBoot = (string.rstrip(val) == 'yes')

        if ip and netmask:
            network = kusu.ipfun.getNetwork(ip, netmask)

        if ip and gateway and netmask:
            if kusu.ipfun.onNetwork(ip, netmask, gateway):
                dev_gateway = gateway

        if validNic:
            nic = { 'device'  : device,
                    'ip'      : ip,
                    'subnet'  : netmask,
                    'network' : network,
                    'mac'     : mac,
                    'gateway' : dev_gateway,
                    'dhcp'    : dhcp,
                    'boot'    : 1,
                    'provision': False,
                    'enabled' : bEnableOnBoot }

    return nic

def findNics(gateway=None):
    nics = {}
    nicfiles = []

    pattern = '/etc/sysconfig/network-scripts/ifcfg-*'
    flist = glob.glob(pattern)

    if len(flist) == 0:
        # Fatal error
        print "ERROR: Unable to locate NICS in: %s\n" % (pattern)
        sys.exit(-1)

    for file in flist:
        nicname = os.path.basename(file)[6:]
        if nicname == 'lo':
            continue

        nics[nicname] = getNicSettings(file, gateway)

    return nics

def main():
    gateway = findGateway()

    nics = findNics(gateway)

    for devname, values in nics.iteritems():
        print devname, values

    return 0

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python

#
#  Copyright (C) 2008 Platform Computing
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

import sys
import os
import string
import glob
import kusu.ipfun

NETWORK='/etc/sysconfig/network'

def findGateway(netsyscfgfile=NETWORK):
    gateway = ''

    if not os.path.exists(netsyscfgfile):
        return gateway

    fin = open(netsyscfgfile, 'r')
    lines = fin.readlines()
    fin.close()
    for line in lines:
        if line[0] == "#":
            continue
        try:
            key,val = string.split(line, '=', 1)
        except:
            continue

        if key == 'GATEWAY':
             gateway = string.rstrip(val)

    return gateway

def getNicSettings(cfgfilename, gateway=None):
    mac     = ''
    ip      = ''
    device  = ''
    netmask = ''
    network = ''
    dev_gateway = ''
    dhcp    = False
    bEnableOnBoot = False
    validNic = 0
    nic = {}

    fin = open(cfgfilename, 'r')
    lines = fin.readlines()
    fin.close()
    for line in lines:
        if line[0] == "#":
            continue
        try:
            key,val = string.split(line, '=', 1)
            val = val.rstrip()
        except:
            continue
        if key == 'DEVICE':
            device = string.rstrip(val)
        elif key == 'HWADDR':
            mac = string.rstrip(val)
        elif key == 'IPADDR':
            ip = string.rstrip(val)
            validNic = 1
        elif key == 'NETMASK':
            netmask = string.rstrip(val)
        elif key == 'BOOTPROTO':
            validNic = 1
            dhcp = (string.rstrip(val) == 'dhcp')
        elif key == 'ONBOOT':
            bEnableOnBoot = (string.rstrip(val) == 'yes')

        if ip and netmask:
            network = kusu.ipfun.getNetwork(ip, netmask)

        if ip and gateway and netmask:
            if kusu.ipfun.onNetwork(ip, netmask, gateway):
                dev_gateway = gateway

        if validNic:
            nic = { 'device'  : device,
                    'ip'      : ip,
                    'subnet'  : netmask,
                    'network' : network,
                    'mac'     : mac,
                    'gateway' : dev_gateway,
                    'dhcp'    : dhcp,
                    'boot'    : 1,
                    'provision': False,
                    'enabled' : bEnableOnBoot }

    return nic

def findNics(gateway=None):
    nics = {}
    nicfiles = []

    pattern = '/etc/sysconfig/network-scripts/ifcfg-*'
    flist = glob.glob(pattern)

    if len(flist) == 0:
        # Fatal error
        print "ERROR: Unable to locate NICS in: %s\n" % (pattern)
        sys.exit(-1)

    for file in flist:
        nicname = os.path.basename(file)[6:]
        if nicname == 'lo':
            continue

        nics[nicname] = getNicSettings(file, gateway)

    return nics

def main():
    gateway = findGateway()

    nics = findNics(gateway)

    for devname, values in nics.iteritems():
        print devname, values

    return 0

if __name__ == "__main__":
    sys.exit(main())
