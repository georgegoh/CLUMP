#!/usr/bin/env python
#
# Copyright (C) 2007 Platform Computing Inc.

# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

"""
This script is used to update the network configuration during first boot 
using the kusu-net-tool script

It will be invoked by S02KusuFirstBootConfig.rc.py
"""

from primitive.system.hardware.net import getPhysicalInterfaces
from primitive.support.util import pollCommand
from socket import gethostname
from kusu.core import netutil
import subprocess
import sys
from kusu.core.db import KusuDB

import primitive.support.log as primitivelog
primitivelog.setLoggerClass()
pl = primitivelog.getPrimitiveLog()
pl.addFileHandler('/var/log/kusu/kusurc.log')

def getPrimaryInstallerNgId():
    """
    Returns the node group ID of the primary installer
    """
    
    ocsHostname = db.getAppglobals('PrimaryInstaller')
    sql = "select ngid from nodes where name='%s'" % (ocsHostname)    
    db.execute(sql)
    row = db.fetchone()
    
    return row[0] or None

def validateDeviceInUse(interfaceName):
    """
    Returns True if the specified interface name is in use
    """
    
    sql = ("select networks.type from "
           "networks, nodegroups, ng_has_net, nics "
           "where networks.device='%s' and nics.netid = networks.netid and "
           "ng_has_net.netid=networks.netid and "
           "ng_has_net.ngid=nodegroups.ngid and "
           "nodegroups.ngid=%d" % (interfaceName, getPrimaryInstallerNgId()))
    db.execute(sql)

    return (db.rowcount > 0, db.fetchone())

def updateHostname():
    """
    Updates the hostname
    """
    pl.info('Firstboot: update hostname')
    print 'Primary Installer Hostname [%s]: ' % gethostname(),
    hostname = raw_input()
    
    if hostname:
        pollCommand("/opt/kusu/sbin/kusu-net-tool hostname %s" % hostname)
        pl.info('Firstboot: Use hostname: %s', hostname)
    else:
        print 'Using current hostname.'

def updateInterfaces():
    """
    Updates the network interfaces that had been configured for this host
    """
    pl.info('Firstboot: Network Interfaces Configuration.')
    systemConfiguration = getPhysicalInterfaces()
    interfaces = sorted(systemConfiguration)
    
    for interface in interfaces:
        (inUse, interfaceType) = validateDeviceInUse(interface)
        if not inUse or interfaceType[0] == 'provision':
            continue
        while True:
            print 'Would you like to configure public network %s [n/y]?' % interface,
            if raw_input() in [ 'y', 'Y' ]:
                print 'IP address [%s]:' % systemConfiguration[interface]['ip'],
                ipAddress = raw_input() or systemConfiguration[interface]['ip']
                pl.info('Firstboot: IP Address: %s ', ipAddress)
                print 'Netmask [%s]:' % systemConfiguration[interface]['netmask'],
                netmask = raw_input() or systemConfiguration[interface]['netmask']
                pl.info('Firstboot: Netmask: %s ', netmask)
                print 'Mac Addr [%s]:' % systemConfiguration[interface]['hwaddr'],
                macAddress = raw_input() or systemConfiguration[interface]['hwaddr']
                pl.info('Firstboot: Mac Address: %s ', macAddress)
                print 'Gateway [%s]:' % netutil.findGateway(),
                gateway = raw_input() or netutil.findGateway()
                pl.info('Firstboot: Gateway: %s ', gateway)
                print 'Description:',
                description = raw_input()
                pl.info('Firstboot: Description: %s ', description)
                (stdOutdata, stdErrData) = pollCommand("/opt/kusu/sbin/kusu-net-tool "\
                                                       "updinstnic "\
                                                       "%s "\
                                                       "--ip-address '%s' "\
                                                       "--netmask '%s' "\
                                                       "--macaddr '%s' "\
                                                       "--gateway '%s' "\
                                                       "--start-ip '' "\
                                                       "--desc '%s' "\
                                                       "--public" % (interface,
                                                                 ipAddress,
                                                                 netmask,
                                                                 macAddress,
                                                                 gateway,
                                                                 description))
                if ''.join(stdOutdata).find("Network settings updated successfully!") >= 0:
                    break
                else:
                    print 'The update failed. ',
            else:
                print 'Skipping configuration of %s.' % interface
                pl.info('Firstboot: Skip network interface configuration.')
                break

def updateDns():
    """
    Updates the DNS configuration
    """
    pl.info('Firstboot: Update DNS configuration')
    for server in range(1,4):
        while True:
            print 'Please provide the IP for DNS server %i (skip with \'Enter\'):' % server,
            dnsIp = raw_input()
            if dnsIp:
                (stdOutdata, stdErrData) = pollCommand("/opt/kusu/sbin/kusu-net-tool dns set dns%i %s" % (server, dnsIp))
                if ''.join(stdOutdata).find("Setting for dns%i updated successfully." % server) >= 0:
                    pl.info("Firstboot: Setup DNS server %i with IP '%s' is successful."% (server, dnsIp)) 
                    break
                else:
                    pl.error("Firstboot: Setup DNS server %i with IP '%s'is unsuccessful."% (server, dnsIp)) 
                    print 'The update failed. ',
            else:
                break
    
    for dnsType in ['public', 'private']:
        while True:    
            print 'Please provide the %s DNS domain (skip with \'Enter\'):' % dnsType,
            dnsDomain = raw_input()
            if dnsDomain:
                (stdOutdata, stdErrData) = pollCommand("/opt/kusu/sbin/kusu-net-tool dns domain %s %s" % (dnsType, dnsDomain))
                if ''.join(stdOutdata).find("Error:") < 0:
                    pl.info('Firstboot: DNS domain %s update is successful.', dnsType)
                    break
                else:
                    pl.error('Firstboot: DNS domain %s update not successful.', dnsType)
            else:
                break


def main(argv=None):
    """
    Updates the network configuration using kusu-net-tool
    """
    pl.info('Firstboot: Update network configuration using kusu-net-tool.')
    print '\nWould you like to configure networking now [n/y]?',
    
    if raw_input() in ['y', 'Y']:
        updateHostname()
        updateInterfaces()
        updateDns()
        print '\nRestarting the network ...'
        pollCommand("service network restart")
        print '\nRunning "kusu-addhost -u" ...'
        pollCommand("kusu-addhost -u")
        print '\nRunning "kusu-cfmsync -f" ...'
        pollCommand("kusu-cfmsync -f")
        print '\nNetwork configuration completed.'
    else:
        pl.info('Firstboot: skipping network configuration.')
        print 'Skipping network configuration.'

    return 0

if __name__ == '__main__':
    db = KusuDB()
    db.connect('kusudb', 'apache')
    status = main()
    sys.exit(status)
