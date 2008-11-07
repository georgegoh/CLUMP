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
                subnet, netmask, gateway, netid, pxehost = netinfo
                network = Network()
                network.netmask = netmask
                network.subnet = subnet
                network.gateway = gateway
                network.pxehost = pxehost

                # Generate the section of the file for this network
                #print 'subnet %s netmask %s {' % (netmask, subnet)
                #print '\tdefault-lease-time %s;' % leasetime
                #print '\tmax-lease-time %s;' % leasetime

                if not gateway:
                    gateway = pxehost

                iprange = IP('%s/%s' % (subnet, netmask))
                gw = IP(gateway)
                
                if gw not in iprange: # this shouldn't happen
                    network.ipranges = [ (iprange[1],iprange[-2]) ]
                elif gw == iprange[1]: # gateway is first ip
                    network.ipranges = [ (iprange[2],iprange[-2]) ]
                elif gw == iprange[-2]: # gateway is last ip
                    network.ipranges = [ (iprange[1],iprange[-3]) ]
                else:
                    # partition free lease range
                    ip = [ip for ip in iprange]
                    idx = ip.index(gw) 

                    if idx == 2: # gateway = 2nd ip
                        network.ipranges = [ (iprange[1],None), (iprange[idx+1],iprange[-2]) ]
                    elif idx == len(ip)-3: # gateway = 2nd last ip
                        network.ipranges = [ (iprange[1],iprange[idx-1]), (None,iprange[-2]) ]
                    else:     
                        network.ipranges = [ (iprange[1],iprange[idx-1]), (iprange[idx+1],iprange[-2]) ]
                    
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
                if provision == 'KUSU':
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
                            if onNetwork(netmask, subnet, row[1]) and row[2]:
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
