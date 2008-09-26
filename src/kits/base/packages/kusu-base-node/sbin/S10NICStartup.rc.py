#!/usr/bin/env python
# $Id: S10NICstartup.rc.py 469 2008-01-24 22:32:44Z mblack $
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

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name    = 'nicstart'
        self.desc    = 'Initializing other NIC interfaces'
        self.ngtypes = ['compute']
        self.delete  = False
        self.nics    = {}   # Dictionary of all the NIC info

    def run(self):
        """Creating config files for all devices.
        The data comes from the profile.nii and looks like:
           # NIC Definitions Device:IP:Subnet:Network:suffix:gateway:dhcp:options
           export NII_NICDEF0="eth2|10.10.0.1|255.255.0.0|10.10.0.0|-eth2:10.10.0.1|0|"
           export NII_NICDEF1="eth1|172.25.243.23|255.255.255.0|172.25.243.0|-eth1|172.25.243.2|0|"
        """
        
        profile = '/etc/profile.nii'
        if not os.path.exists(profile):
            return False

        fp = open(profile, 'r')
        lines = fp.readlines()
        fp.close()

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
                dev,ip,sn,net,suf,gw,dhcp,opts = string.split(val, '|', 7)
            except:
                continue
            
            if dhcp != '0' and dhcp != '1':
                # Bad data
                continue

            if dev != 'bmc':
                # It's a normal NIC
                ifcfg = '/etc/sysconfig/network-scripts/ifcfg-%s' % dev
                if os.path.exists(ifcfg):
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
                cmd = '/etc/sysconfig/network-scripts/ifup %s' % dev
                os.system(cmd)
                
            else:
                # Put the code to configure BMC here
                rcfile = '/etc/rc.kusu.d/S99DellBMCSetup'
                if os.path.exists(rcfile):
                    os.system("%s %s %s %s" % (rcfile, ip, gw, sn))
                os.unlink(rcfile)

        return True
