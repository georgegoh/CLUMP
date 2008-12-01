#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import re
import os
from path import path
from kusu.core import rcplugin
from primitive.system.hardware.probe import getAllInterfaces
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
                              ('udp', 53),
                              ('tcp', 80),
                              ('tcp', 443)]

    def run(self):
        self.setupSysCtl()
        self.runCommand('/sbin/sysctl -p')[0]

        self.setupIPTableConf()
        
        success, (out, retcode, err) = self.service('firewall', 'restart')
        if not success:
            raise Exception, err
        
        success, (out, retcode, err) = self.service('firewall', 'enable')
        if not success:
            raise Exception, err
        
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
        
        all_intf_dict = getAllInterfaces()
        db_nics = self.queryDBForMasterNICs()
        nics = [nic for nic in db_nics if (nic['device'] in all_intf_dict.keys())]
        self.verifyNICs(nics, all_intf_dict)

        devices_by_network_name = Struct(public=self.getNICsOfType(nics, 'public'),
                                         provision=self.getNICsOfType(nics, 'provision'),
                                         others=self.getNICsOfType(nics, 'others'))
        
        s = ''
        if self.os_name in ["sles", "opensuse", "suse"]:
            s = self.generateSuSEfirewall2Config(devices_by_network_name)
            conf = '/etc/sysconfig/SuSEfirewall2'
        elif self.os_name in ["rhel", "redhat", "centos"]:
            s = self.generateIPTablesConfig(devices_by_network_name)
        conf = path(conf)
        
        f = open(conf, 'w')
        f.write(s)
        f.close()
        conf.chown(0,0)
        conf.chmod(0600)

    def queryDBForMasterNICs(self):
        """Get from kusudb the NICs related to the master node."""
        engine = os.getenv('KUSU_DB_ENGINE')
        if engine == 'mysql':
            dbs = db.DB('mysql', 'kusudb', 'root')
        else: # postgres
            dbs = db.DB('postgres', 'kusudb', 'apache')
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

        for dev in private_nics:
            filter += '-A FORWARD -i %s ' % dev + \
                      '-o %s -m state ' % public + \
                      '--state RELATED,ESTABLISHED -j ACCEPT\n'
            filter += '-A FORWARD -i %s -j ACCEPT\n' % dev
            filter += '-A INPUT -i %s -j ACCEPT\n' % dev
        filter += '-A INPUT -i lo -j ACCEPT\n'
        filter += '-A INPUT -p icmp --icmp-type any -j ACCEPT\n'
        filter += '-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT\n'
        filter += '-A INPUT -i %s -j REJECT\n' % public
        filter += 'COMMIT\n'

        return nat + filter

    def generateSuSEfirewall2Config(self, devices_by_network_name):
        public = devices_by_network_name.public[0]['device']

        # get all non-public interfaces.
        provision_devices = devices_by_network_name.provision
        private_nics = [nic['device'] for nic in provision_devices]
        other_devices = devices_by_network_name.others
        private_nics += [nic['device'] for nic in other_devices]
        private = ''
        for dev in private_nics:
            private = str(dev) + ' '
        
        conf = 'FW_DEV_EXT="%s"\n' % public
        conf += 'FW_DEV_INT="%s"\n' % private
        conf += 'FW_ROUTE="yes"\n'
        conf += 'FW_MASQUERADE="yes"\n'
        conf += 'FW_PROTECT_FROM_INT="no"\n'
        
        conf_ext_tcp = ''
        conf_ext_udp = ''
        conf_ext_rpc = ''
        conf_ext_ip = ''
        for proto, port in self.allowed_ports:
            if 'tcp' == proto:
                conf_ext_tcp += '%s ' % port
            elif 'udp' == proto:
                conf_ext_udp += '%s ' % port
            elif 'rpc' == proto:
                conf_ext_rpc += '%s ' % port
            elif 'ip' == proto:
                conf_ext_ip += '%s ' % port
        
        conf += 'FW_SERVICES_EXT_TCP="%s"\n' % conf_ext_tcp
        conf += 'FW_SERVICES_EXT_UDP="%s"\n' % conf_ext_udp
        conf += 'FW_SERVICES_EXT_RPC="%s"\n' % conf_ext_rpc
        conf += 'FW_SERVICES_EXT_IP="%s"\n' % conf_ext_ip
        
        conf_forward = '' 
        for dev in private_nics:
            conf_forward += "%s,%s,,, " % (dev, public)
        conf += 'FW_FORWARD="%s%s,0/0,,,"\n' % (conf_forward, dev)
        conf += 'FW_TRUSTED_NETS="127.0.0.1 0/0,icmp"\n'
        
        return conf

