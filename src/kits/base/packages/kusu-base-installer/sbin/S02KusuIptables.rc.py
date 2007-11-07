#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import re
from path import path
from kusu.core import rcplugin
from kusu.hardware import probe 
import sqlalchemy as sa
import kusu.core.database as db
from kusu.util.structure import Struct

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'iptables'
        self.desc = 'Setting up iptables'
        self.ngtypes = ['installer']
        self.delete = True
        self.allowed_ports = [('tcp', 22),
                              ('tcp', 53),
                              ('udp', 53)]

    def run(self):
        self.setupSysCtl()
        self.runCommand('/sbin/sysctl -p')[0]

        self.setupIPTableConf()
        self.runCommand('/etc/init.d/iptables restart')[0]

        self.runCommand('/sbin/chkconfig iptables on')

        return True

    def setupSysCtl(self, conf='/etc/sysctl.conf'):
        """Set up the IP Forward option in the kernel."""
        try:
            f = open(conf)
            s = f.read()
            p = re.compile('net.ipv4.ip_forward\s*=\s*0')
            s = p.sub('net.ipv4.ip_forward = 1', s)
            f.close()
        except IOError:
            s = 'net.ipv4.ip_forward = 1'
        f = open(conf, 'w')
        f.write(s)
        f.close()

    def setupIPTableConf(self, conf='/etc/sysconfig/iptables'):
        """Set up the iptables configuration."""
        conf = path(conf)

        all_intf_dict = probe.getAllInterfaces()
        db_nics = self.queryDBForMasterNICs()
        nics = [nic for nic in db_nics if (nic['device'] in all_intf_dict.keys())]
        self.verifyNICs(nics, all_intf_dict)

        devices_by_network_name = Struct(public=self.getNICsOfType(nics, 'public'),
                                         provision=self.getNICsOfType(nics, 'provision'),
                                         others=self.getNICsOfType(nics, 'others'))

        s = self.generateIPTablesConfig(devices_by_network_name)
        f = open(conf, 'w')
        f.write(s)
        f.close()
        conf.chown(0,0)
        conf.chmod(0600)

    def queryDBForMasterNICs(self):
        """Get from kusudb the NICs related to the master node."""
        dbs = db.DB('mysql', 'kusudb', 'root')
        nodes = dbs.nodes
        nics = dbs.nics
        networks = dbs.networks
        stmt = sa.select([nodes.c.name, nics.c.mac, nics.c.ip,
                          networks.c.device, networks.c.type])

        stmt.distinct = True
        stmt.append_from(nodes.join(nics, nodes.c.nid==nics.c.nid).join(
                         networks, nics.c.netid==networks.c.netid))

        master = self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller')
        stmt.append_whereclause(nodes.c.name==master.kvalue)
        result = stmt.execute().fetchall()
        return result

    def verifyNICs(self, nics, intf_dict):
        """
            Verify that the devices we detected and the devices in the db
            do in fact refer to the same device by comparing their MAC address.
        """
        for nic in nics:
            device = nic['device']
            intf = intf_dict[device]
            if nic['mac'] != intf['hwaddr']:
                return False
        return True

    def getNICsOfType(self, nics, type):
        return [nic for nic in nics if nic['type']==type]

    def generateIPTablesConfig(self, devices_by_network_name):
        """Generate the iptables configuration."""
        public = devices_by_network_name.public[0]['device']

        nat = '*nat\n'
        nat += '-A POSTROUTING -o %s -j MASQUERADE\n' % public
        nat += 'COMMIT\n\n'

        filter = '*filter\n'

        # get all non-public interfaces.
        provision_devices = devices_by_network_name.provision
        private_nics = [nic['device'] for nic in provision_devices]
        other_devices = devices_by_network_name.others
        private_nics += [nic['device'] for nic in other_devices]

        filter += '# Preamble\n'
        for proto, port in self.allowed_ports:
            filter += '-A INPUT -i %s -m state --state NEW -p %s --dport %d -j ACCEPT\n' % \
                        (public, proto, port)
        filter += '#-A INPUT -i eth1 -m state --state NEW -p udp --dport 80 -j ACCEPT\n'
        filter += '#-A INPUT -i eth1 -m state --state NEW -p udp --dport 443 -j ACCEPT\n'

        for dev in private_nics:
            filter += '-A FORWARD -i %s ' % dev + \
                      '-o %s -m state ' % public + \
                      '--state RELATED,ESTABLISHED -j ACCEPT\n'
            filter += '-A FORWARD -i %s -j ACCEPT\n' % dev
            filter += '-A INPUT -i %s -j ACCEPT\n' % dev
        filter += '-A INPUT -i lo -j ACCEPT\n'
        filter += '-A INPUT -p icmp --icmp-type any -j ACCEPT\n'
        filter += '-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT\n'
        filter += '-A INPUT -i %s -p tcp --dport 0:1024 -j REJECT\n' % public
        filter += '-A INPUT -i %s -p udp --dport 0:1024 -j REJECT\n' % public
        filter += 'COMMIT\n'

        return nat + filter
