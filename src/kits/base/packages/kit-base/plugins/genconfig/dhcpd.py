# $Id: dhcpd.py 3529 2010-02-19 12:46:40Z ankit $
#
#   Copyright 2007 Platform Computing Inc
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
#

import sys
from kusu.genconfig import Report
from kusu.core import database
from kusu.ipfun import *
from Cheetah.Template import Template
from sets import Set
from IPy import IP

class Network(object): pass
class Host(object): pass

class thisReport(Report):

    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print self.gettext("genconfig_Dhcpd_Help")


    def runPlugin(self, pluginargs):
        """runPlugin - This method provides the database report for this
        plugin.  All plugins must implement this method.  This plugin will
        generate the dhcpd.conf file contents."""

        engine = os.getenv('KUSU_DB_ENGINE')
        if engine == 'mysql':
            dbdriver = 'mysql'
        else:
            dbdriver = 'postgres'
        dbdatabase = 'kusudb'
        dbuser = 'apache'
        dbpassword = None

        dbs = database.DB(dbdriver, dbdatabase, dbuser, dbpassword)

        _ = self.gettext
        
        # Need to get the name of the primary installer so we can see which networks
        # we need to install on.
        installer = self.db.getAppglobals('PrimaryInstaller')
        if not installer:
            sys.stderr.write(_("genconfig_cannot_determine_primary_installer\n"))
            sys.exit(-1)

        # Get the Primary Installer's IP.
        try:
            pi_nics = dbs.Nodes.selectfirst_by(name=installer).nics
            pi_ip = filter(lambda x: x.network.type=='provision', pi_nics)[0].ip
        except: pi_ip = ''

        # Get the provisioning IP for all installers
        query = ("SELECT nics.ip FROM nodes, nics, networks WHERE "
                 "nodes.nid=nics.nid AND nics.netid=networks.netid "
                 "AND networks.type='provision' "
                 "AND nodes.ngid=1 "
                 "AND not networks.device='bmc' "
                 "AND not lower(networks.device) like 'ib%%'")

        try:
            self.db.execute(query)
        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
 
        data = self.db.fetchall()
        dnssrv = ''
        if data:
            for ds in data:
                tmp = ds[0]
                dnssrv = dnssrv + tmp + ','
            dnssrv = dnssrv[:-1]
 
        # Get the max lease time
        leasetime = self.db.getAppglobals('DHCPLeaseTime')
        if not leasetime:
            leasetime = 2400

        # Get the DNS
        dnsdomain = self.db.getAppglobals('DNSZone')
       
        # Get the PROVISION type
        provision = dbs.AppGlobals.select_by(kname = 'PROVISION')[0].kvalue


        # Now get the networks
        query = ('select networks.network, networks.subnet, '
                 'networks.gateway, networks.netid, nics.ip '
                 'from networks,nics,nodes where nodes.nid=nics.nid and '
                 'nics.netid=networks.netid and networks.usingdhcp=False '
                 'and nodes.name=\'%s\' and networks.type=\'provision\' and not networks.device=\'bmc\' and not lower(networks.device) like \'ib%%\'' % installer)
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)

        data = self.db.fetchall()
        networks = []
        if data:
            for netinfo in data:
                netwrk, subnet, gateway, netid, pxehost = netinfo
                network = Network()
                network.netmask = subnet
                network.subnet = netwrk
                network.gateway = gateway
                network.pxehost = pxehost

                if not gateway:
                    gateway = pxehost

                # Now cycle through the nodes on for this
                network.hosts = []
                query = ('select nodes.name, nics.ip, nics.mac, networks.suffix, networks.device '
                         'from networks,nics,nodes where nodes.nid=nics.nid and '
                         'nics.netid=networks.netid and nics.boot=True and networks.usingdhcp=False')

                try:
                    self.db.execute(query)

                except:
                    sys.stderr.write(_("DB_Query_Error\n"))
                    sys.exit(-1)

                dhcpdata = self.db.fetchall()
                if dhcpdata:
                    for row in dhcpdata:
                        # Test to see if this nodes IP lies on the same network
                        # as this DHCP section and that there is a MAC
                        # address for the interface.
                        if onNetwork(netwrk, subnet, row[1]) and row[2]:
                            host = Host()
                            if row[3]:
                                host.name = '%s%s' % (row[0], row[3])
                            else:
                                host.name = '%s-%s' % (row[0], row[3])

                            # Handle interfaces that may not have a MAC
                            # address (such as Infiniband)
                            host.mac = row[2]
                            host.hostname = row[0]
                            host.ip = row[1]
                            network.hosts.append(host)

                network.ranges = getNetworkRanges(network.subnet,
                                                  network.netmask,
                                                  network.gateway,
                                                  [x.ip for x in network.hosts],
                                                  provision=provision)

                networks.append(network)
 
            ns = {'leasetime': leasetime, 
                  'dnsdomain': dnsdomain,
                  'dnsdomainserver': dnssrv,
                  'networks': networks,
                  'installerip': pi_ip,
                  'provision': provision}
            t = Template(file='/opt/kusu/etc/templates/dhcpd.tmpl', searchList=[ns])  
            print str(t)
        else:
            print "# This machine is not the primary installer"


def getNetworkRanges(subnet, netmask, gateway, hosts, provision='KUSU'):
    """ Returns a list of usable ranges in the the given subnet/netmask,
        while taking into account the IPs that are used up by the gateway
        and the list of hosts.
        subnet,netmask,gateway: dotted IP format(xxx.xxx.xxx.xxx)
        hosts: list of dotted IP format

        Note: This function DOES NOT check for validity of the saneness
        of the input values. It is assumed that the gateway and hosts
        are valid IPs for the subnet/netmask given.
    """
    # Use IPy to create the range of IP addresses, and subtract the hosts.
    ip_hosts = [IP(x).int() for x in hosts]
    network = IP('%s/%s' % (subnet, netmask))
    used_ips = Set([network[0], network[-1]])

    if gateway:
        used_ips.add(IP(gateway))
    # HP-ICE provisioning needs the hosts' IPs to be excluded from dhcpd's available list.
    if provision != 'KUSU':
        for h in ip_hosts:
            used_ips.add(IP(h))
    #else:
        # KUSU stores fixed addresses for hosts in dhcpd, no need to further exclude their IPs.

    # Convert IPs to integers for easier manipulation.
    ip_ints = sorted([x.int() for x in used_ips])
    used_ranges = splitConsecutiveRanges(ip_ints)
    range_startings = [x[-1] for x in used_ranges] [:-1]
    range_endings = [x[0] for x in used_ranges] [1:]

    # Create a list of (start IP, end IP) tuples to return to dhcpd config.
    allocatable_ranges = []
    count = 0
    for i,s in enumerate(range_startings):
        start = s+1
        end = range_endings[i]-1
        
        # Limit range to a sane size
        if (end - start) > 65533:
            end = start + 65533

        count += (end - start)
        allocatable_ranges.append((IP(start), IP(end)))

        # Limit total allocable IPs
        if count >= 65533:
            break
    
    return allocatable_ranges


def splitConsecutiveRanges(li):
    """ Look for ranges within the list that contain consecutive numbers."""
    consecutive_ranges = []
    last = li[0]
    _range = li[0:1]
    for x in li[1:]:
        if x == (_range[-1] + 1):
            _range.append(x)
        else:
            consecutive_ranges.append(_range)
            _range = [x]
    consecutive_ranges.append(_range)
    return consecutive_ranges


if __name__ == '__main__':
    print 'Testing getNetworkRanges'
    r1 = getNetworkRanges('10.10.10.0', '255.255.255.0', '10.10.10.1', ['10.10.10.2', '10.10.10.3', '10.10.10.4'])
    assert r1 == [(IP('10.10.10.5'), IP('10.10.10.254'))], 'Bad r1: %s' % r1
    r2 = getNetworkRanges('10.10.10.0', '255.255.255.0', '10.10.10.1', ['10.10.10.2', '10.10.10.3', '10.10.10.40']) 
    assert r2 == [(IP('10.10.10.4'), IP('10.10.10.39')),
            (IP('10.10.10.41'), IP('10.10.10.254'))], 'Bad r2: %s' % r2
    r3 = getNetworkRanges('192.168.0.0', '255.255.255.0', '192.168.0.100', ['192.168.0.1', '192.168.0.3', '192.168.0.110']) 
    assert r3 == [(IP('192.168.0.2'), IP('192.168.0.2')),
                  (IP('192.168.0.4'), IP('192.168.0.99')),
                  (IP('192.168.0.101'), IP('192.168.0.109')),
                  (IP('192.168.0.111'), IP('192.168.0.254'))], 'Bad r3: %s' % r3
    r4 = getNetworkRanges('10.0.0.0', '255.0.0.0', '10.0.0.100', ['10.0.0.1', '10.0.0.3', '10.0.0.110']) 
    assert r4 == [(IP('10.0.0.2'), IP('10.0.0.2')),
                  (IP('10.0.0.4'), IP('10.0.0.99')),
                  (IP('10.0.0.101'), IP('10.0.0.109')),
                  (IP('10.0.0.111'), IP('10.255.255.254'))], 'Bad r4: %s' % r4
    print 'OK'
