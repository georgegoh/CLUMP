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


from path import path
import tempfile
import os

import kusu.ipfun as ipfun
from kusu.core import netutil


class InitKusuDBReceiver(object):
    """
    This class initializes the sqlite kusudb.
    """
    def __init__(self, kusu_db):
        self._db = kusu_db

    def createDB(self, nicCheck, dhcpCheck, envCheck, systemSettings):

        if not nicCheck.singleNicInstall:
            public_nic, public_nic_props = nicCheck.publicInterfaceTuple

        provision_nic, provision_nic_props = nicCheck.provisionInterfaceTuple

        #insert basic data into DB
        # Insert into appglobals table

        # Get the hostname and PublicDNSZone from fqdn name.
        hostname = envCheck.pub_fqdn.split('.')[0]
        pub_domain = envCheck.pub_fqdn.split('.',1)[-1]

        # Get the private DNSZone from the prov_fqdn

        # update InstallerServeDHCP and InstallerServeDNS
        appglobals = self._db.AppGlobals.selectone_by(kname='InstallerServeDHCP')
        appglobals.kvalue = dhcpCheck.dhcpLocality
        appglobals = self._db.AppGlobals.selectone_by(kname='InstallerServeDNS')
        appglobals.kvalue = dhcpCheck.dhcpLocality

        #add in PrimaryInstaller, DNSZone and PublicDNSZone name to DB
        self._db.AppGlobals(kname='PrimaryInstaller', kvalue=hostname)
        self._db.AppGlobals(kname='DNSZone', kvalue=envCheck.prov_fqdn)
        self._db.AppGlobals(kname='PublicDNSZone', kvalue=pub_domain)
        self._db.AppGlobals(kname='Timezone_zone', kvalue=systemSettings.timezone['zone'].strip('"'))
        self._db.AppGlobals(kname='Timezone_utc', kvalue=systemSettings.timezone['utc'])
        self._db.AppGlobals(kname='Timezone_ntp_server', kvalue=systemSettings.timezone['ntp'])
        self._db.AppGlobals(kname='Keyboard', kvalue=systemSettings.keyboardLayout.strip('"'))
        self._db.AppGlobals(kname='Language', kvalue=systemSettings.language)
        self._db.AppGlobals(kname='SYSLOG_SERVER', kvalue=provision_nic_props['ip'])

        count = 1
        for nsip in systemSettings.nameservers:
            self._db.AppGlobals(kname='dns%s' % count, kvalue=nsip)
            count = count + 1

            if count == 3:
                break #we only support up to dns3

        self._db.flush()


# netid |  network   |    subnet     | device | suffix |   gateway    | options | netname |  startip   | inc |   type    | usingdhcp
#-------+------------+---------------+--------+--------+--------------+---------+---------+------------+-----+-----------+-----------
#     1 | 172.20.0.0 | 255.255.0.0   | eth0   | -eth0  | 172.20.0.1   |         | cluster | 172.20.0.1 |   1 | provision | f
#     2 | 10.10.0.0  | 255.255.240.0 | eth1   | -eth1  | 10.10.11.254 |         | public  | 10.10.0.1  |   1 | public    | f

        # Network
        #First we insert data for the public network
        if not nicCheck.singleNicInstall:
            public_network = self._db.Networks()
            public_network.network = ipfun.getNetwork(public_nic_props['ip'], public_nic_props['netmask'])
            public_network.subnet = public_nic_props['netmask']
            public_network.device = public_nic
            public_network.netname = 'public'
            public_network.gateway = netutil.findGateway()
            public_network.startip = public_nic_props['ip'] #FIXME? Is this always the first IP in the block ?
            public_network.suffix = "-%s" % public_nic
            public_network.type = 'public'
            public_network.save()
            public_network.flush()

        ## Now data for the provisioning network
        provision_network = self._db.Networks()
        provision_network.network = ipfun.getNetwork(provision_nic_props['ip'], provision_nic_props['netmask'])
        provision_network.subnet =  provision_nic_props['netmask']
        provision_network.device = provision_nic
        provision_network.suffix = "-%s" % provision_nic
        provision_network.netname = 'cluster'

        _default_gateway = netutil.findGateway()
        if nicCheck.singleNicInstall and _default_gateway:
            provision_network.gateway = _default_gateway
        else:
            provision_network.gateway = provision_nic_props['ip']

        provision_network.startip = provision_nic_props['ip']
        provision_network.type = 'provision'
        provision_network.save()
        provision_network.flush()

        if provision_network.device != 'eth0' and \
                provision_network.device.startswith('eth') or \
                provision_network.device.startswith('bond'):
            provision_network_copy = self._db.Networks()
            for col in provision_network.cols:
                setattr(provision_network_copy, col, getattr(provision_network, col))
            provision_network_copy.device = 'eth0'
            provision_network_copy.netname = provision_network.netname + '-eth0'
            provision_network_copy.suffix = '-eth0'
            provision_network_copy.save()
            provision_network_copy.flush()

        #Associate nodegroups with appropriate networks
        #public network with installer
        if not nicCheck.singleNicInstall:
            public_network.nodegroups.append(self._db.NodeGroups.selectone_by(ngname='installer'))
            public_network.save()
            public_network.flush()

        #provision network with everything
        provision_network.nodegroups.append(self._db.NodeGroups.selectone_by(ngname='installer'))
        provision_network.nodegroups.append(self._db.NodeGroups.selectone_by(ngname='unmanaged'))
        provision_network.nodegroups.append(self._db.NodeGroups.selectone_by(ngname='compute'))
        provision_network.nodegroups.append(self._db.NodeGroups.selectone_by(ngname='compute-imaged'))
        provision_network.nodegroups.append(self._db.NodeGroups.selectone_by(ngname='compute-diskless'))
        provision_network.save()
        provision_network.flush()

        #node = self._db.Nodes(name=hostname)
        # Default name of the installer node is master, update this value.
        node = self._db.Nodes.selectone_by(name='master')
        node.name = hostname
        if not nicCheck.singleNicInstall:
            public_nic = self._db.Nics(ip=public_nic_props['ip'], netid=public_network.netid, mac=public_nic_props['hwaddr'], boot=True)
            node.nics.append(public_nic)

        private_nic = self._db.Nics(ip=provision_nic_props['ip'], netid=provision_network.netid, mac=provision_nic_props['hwaddr'], boot=True)

        node.nics.append(private_nic)
        node.save()
        node.flush()

        #installer = self._db.NodeGroups(ngname='installer nodegroup', type='installer')
        #installer.nodes.append(node)
        #installer.save()
        #installer.flush()

        return True


