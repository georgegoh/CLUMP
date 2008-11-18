# $Id$
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
from path import path
from kusu.genconfig import Report
from kusu.core import database
from kusu.ipfun import *
from Cheetah.Template import Template
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
        dbpassword = 'None'

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
                 'and nodes.name=\'%s\' and networks.type=\'provision\'' % installer)
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

                # Generate the section of the file for this network
                #print 'subnet %s netmask %s {' % (netmask, subnet)
                #print '\tdefault-lease-time %s;' % leasetime
                #print '\tmax-lease-time %s;' % leasetime

                if not gateway:
                    gateway = pxehost

                #print '\toption routers %s;' % gateway
                #print '\toption subnet-mask %s;' % subnet
                
                #if dnsdomain:
                #    print '\toption domain-name "%s";' % dnsdomain
                    
                #print '\tif substring (option  vendor-class-identifier, 0, 20)  = "PXEClient:Arch:00000" {'
                #print '\t\tfilename  "pxelinux.0";'
                #print '\t\toption vendor-class-identifier  "PXEClient";'
                #print '\t\toption PXE.mtftp-ip 0.0.0.0;'
                #print '\t\tvendor-option-space PXE;'
                #print '\t\tnext-server %s;' % pxehost
                #print '\t}'


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
                            #    print '\thost %s%s {' % (row[0], row[3])
                                host.name = '%s%s' % (row[0], row[3])
                            else:
                            #    print '\thost %s-%s {' % (row[0], row[4])
                                host.name = '%s-%s' % (row[0], row[3])

                            # Handle interfaces that may not have a MAC
                            # address (such as Infiniband)
                            #if row[2]:
                            #    print '\t\thardware ethernet %s;' % row[2]
                            host.mac = row[2]
                            host.hostname = row[0]
                            host.ip = row[1]
                            #print '\t\toption host-name "%s";' % row[0]
                            #print '\t\tfixed-address %s;' % row[1]
                            #print '\t}'
                            network.hosts.append(host)

                network.ranges = getNetworkRanges(network.subnet,
                                                  network.netmask,
                                                  network.gateway,
                                                  [x.ip for x in network.hosts])

                #print '}'
                networks.append(network)
 
            ns = {'leasetime': leasetime, 
                  'dnsdomain': dnsdomain,
                  'networks': networks,
                  'installerip': pi_ip,
                  'provision': provision}
            t = Template(file='/opt/kusu/etc/templates/dhcpd.tmpl', searchList=[ns])  
            print str(t)
        else:
            print "# This machine is not the primary installer"

def getNetworkRanges(subnet, netmask, gateway, hosts):
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
    ip_hosts = [IP(x) for x in hosts]
    ip_range = [x for x in IP('%s/%s' % (subnet, netmask))]
    used_idx = [0,len(ip_range)-1] # first and last are reserved.

    # Add gateway IP to list of used indices.
    if gateway:
        ip = IP(gateway)
        index = ip_range.index(ip)
        if index not in used_idx:
            used_idx.append(index)
    # Each host must be added as used.
    for h in ip_hosts:
        index = ip_range.index(h)
        if index not in used_idx:
            used_idx.append(index)
    used_idx = sorted(used_idx)

    last_reserved_idx = getIndexOfLastConsecutiveNum(used_idx, from_back=True)
    last_usable_ip = used_idx[last_reserved_idx] - 1
    range_boundaries = []
    i = 0 # index of the last ip of the usable range search
    range_end = 0
    # Don't go beyond end of usage range
    while range_end < last_usable_ip and i < len(used_idx):
        # look for the last consecutive number in the used indexes,
        # and offset the starting search by i.
        idx = getIndexOfLastConsecutiveNum(used_idx[i:]) + i
        range_start = used_idx[idx] + 1
        range_end = used_idx[idx+1] - 1
        range_boundaries.append((ip_range[range_start], ip_range[range_end]))
        i = idx + 1
    return range_boundaries

def getIndexOfLastConsecutiveNum(series, from_back=False):
    if from_back:
        last_val = series[-1]
        for i,v in enumerate(reversed(series)):
            if v != last_val-i:
                return len(series)-i
    else: 
        first_val = series[0]
        for i,v in enumerate(series):
            if v != first_val+i:
                return i-1
    return 0

if __name__ == '__main__':
    print 'Testing getNetworkRanges'
    r1 = getNetworkRanges('10.10.10.0', '255.255.255.0', '10.10.10.1', ['10.10.10.2', '10.10.10.3', '10.10.10.4'])
    assert r1 == [(IP('10.10.10.5'), IP('10.10.10.254'))]
    r2 = getNetworkRanges('10.10.10.0', '255.255.255.0', '10.10.10.1', ['10.10.10.2', '10.10.10.3', '10.10.10.40']) 
    assert r2 == [(IP('10.10.10.4'), IP('10.10.10.39')),
                  (IP('10.10.10.41'), IP('10.10.10.254'))]
    r3 = getNetworkRanges('192.168.0.0', '255.255.255.0', '192.168.0.100', ['192.168.0.1', '192.168.0.3', '192.168.0.110']) 
    assert r3 == [(IP('192.168.0.2'), IP('192.168.0.2')),
                  (IP('192.168.0.4'), IP('192.168.0.99')),
                  (IP('192.168.0.101'), IP('192.168.0.109')),
                  (IP('192.168.0.111'), IP('192.168.0.254'))]
    print 'OK'
