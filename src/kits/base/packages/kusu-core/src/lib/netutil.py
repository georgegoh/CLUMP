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
import subprocess
from primitive.system.software.dispatcher import Dispatcher
from primitive.system.software.probe import OS
from primitive.support.osfamily import getOSNames
from primitive.system.hardware.net import Net

def findGateway():
    cmd = subprocess.Popen("route -n | grep '^0.0.0.0' | awk '{print $2}'",
                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    gateway, err = cmd.communicate()
    return gateway

def getRHNic(cfgfilename, gateway=None):
    device = ''
    mac = ''
    ip = ''
    netmask = ''
    bootproto = ''
    bEnableOnBoot = ''

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
        elif key == 'NETMASK':
            netmask = string.rstrip(val)
        elif key == 'BOOTPROTO':
            bootproto = string.rstrip(val)
        elif key == 'ONBOOT':
            bEnableOnBoot = (string.rstrip(val) == 'yes')

    return device, mac, ip, netmask, bootproto, bEnableOnBoot

def getSLESNic(cfgfilename, gateway=None, device=''):
    mac = ''
    ip = ''
    netmask = ''
    bootproto = ''
    bEnableOnBoot = ''

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

        if key == 'BOOTPROTO':
            bootproto = val.rstrip().strip("'")
        elif key == 'STARTMODE':
            bEnableOnBoot = (val.rstrip().strip("'") == 'onboot')

    if device:
        net = Net(device)
        ip = net.ip
        netmask = net.netmask
        mac = net.mac

    return device, mac, ip, netmask, bootproto, bEnableOnBoot

def getNicSettings(cfgfilename, gateway=None, device=''):
    network = ''
    dev_gateway = ''
    dhcp = False
    nic = {}

    osname, osver, osarch = OS()

    if osname.lower() in getOSNames('rhelfamily'):
        device, mac, ip, netmask, bootproto, bEnableOnBoot = getRHNic(cfgfilename, gateway=gateway)

    elif osname.lower() in ['suse', 'opensuse', 'sles']:
        device, mac, ip, netmask, bootproto, bEnableOnBoot = getSLESNic(cfgfilename, gateway=gateway, device=device)

    if ip and netmask:
        network = kusu.ipfun.getNetwork(ip, netmask)

    if ip and gateway and netmask:
        if kusu.ipfun.onNetwork(ip, netmask, gateway):
            dev_gateway = gateway

    dhcp = (bootproto == 'dhcp')

    if bootproto or ip:
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

    pattern = Dispatcher.get('network_config_files')
    flist = glob.glob(pattern)

    if len(flist) == 0:
        # Fatal error
        print "ERROR: Unable to locate NICS in: %s\n" % (pattern)
        sys.exit(-1)

    for file in flist:
        osname, osver, osarch = OS()

        if osname.lower() in getOSNames('rhelfamily'):
            nicname = os.path.basename(file)[6:]
            if nicname == 'lo':
                continue

        elif osname.lower() in ['suse', 'opensuse', 'sles']:
            nicdev = os.path.basename(file)[6:]
            cmd = subprocess.Popen("getcfg-interface %s" % nicdev, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            out, err = cmd.communicate()
            nicname = out.strip()

        if nicname:
            nics[nicname] = getNicSettings(file, gateway, device=nicname)

    return nics

def getMacAddrForNIC(nic):
    import subprocess
    import re

    cmd = 'ifconfig %s | grep -i hwaddr' % (nic)
        
    try:    
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    except OSError, e:
        return None
        
    buf = p.stdout.readlines()

    retval = p.wait()
        
    if retval != 0 or not buf:
        return None
        
    r = re.compile(".*HWaddr.(.*).*").match(buf[0])
    if not r:
        return None
        
    return r.group(1).rstrip()

def main():
    gateway = findGateway()

    nics = findNics(gateway)

    for devname, values in nics.iteritems():
        print devname, values

    return 0

if __name__ == "__main__":
    sys.exit(main())
