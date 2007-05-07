# $Id$
#
#   Copyright 2007 Platform Computing Corporation
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

import dbreport
import sys

class thisReport(dbreport.Report):

    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print self.gettext("dbreport_Dhcpd_Help")


    def runPlugin(self, pluginargs):
        """runPlugin - This method provides the database report for this
        plugin.  All plugins must implement this method.  This plugin will
        generate the dhcpd.conf file contents."""

        _ = self.gettext
        
        # Need to get the name of the primary installer so we can see which networks
        # we need to install on.
        installer = self.db.getAppglobals('PrimaryInstaller')
        if not installer:
            sys.stderr.write(_("dbreport_cannot_determine_primary_installer\n"))
            sys.exit(-1)

        # Get the max lease time
        leasetime = self.db.getAppglobals('DHCPLeaseTime')
        if not leasetime:
            leasetime = 2400

        # Now get the networks
        query = ('select networks.network, networks.subnet, '
                 'networks.gateway, networks.netid, nics.ip '
                 'from networks,nics,nodes where nodes.nid=nics.nid and '
                 'nics.netid=networks.netid and nodes.name="%s"' % installer)
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)

        data = self.db.fetchall()
        if data:
            print "# "
            print "# Dynamically generated by: dbreport  (Do not edit!)"
            print "# "
            print "ddns-update-style none;"
            print "option space PXE;"
            print "option PXE.mtftp-ip code 1 = ip-address;"
            print "#"
            for netinfo in data:
                netmask, subnet, gateway, netid, pxehost = netinfo

                # Generate the section of the file for this network
                print 'subnet %s netmask %s {' % (netmask, subnet)
                print '\tdefault-lease-time %s;' % leasetime
                print '\tmax-lease-time %s;' % leasetime
                print '\toption routers %s;' % gateway
                print '\toption subnet-mask %s;' % subnet
                

                #option domain-name "local";
                #option domain-name-servers 10.101.1.1;
                #option nis-domain "rocks";
                #option broadcast-address 10.255.255.255;
                print '\tif substring (option  vendor-class-identifier, 0, 20)  = "PXEClient:Arch:00000" {'
                print '\t\tfilename  "pxelinux.0";'
                print '\t\toption vendor-class-identifier  "PXEClient";'
                print '\t\toption PXE.mtftp-ip 0.0.0.0;'
                print '\t\tvendor-option-space PXE;'
                print '\t\tnext-server %s;' % pxehost
                print '\t}'


                # Now cycle through the nodes on for this
                query = ('select nodes.name, nics.ip, nics.mac, networks.suffix '
                         'from networks,nics,nodes where nodes.nid=nics.nid and '
                         'nics.netid=networks.netid and nics.boot=1 '
                         'and networks.netid="%s"' % netid)

                try:
                    self.db.execute(query)

                except:
                    sys.stderr.write(_("DB_Query_Error\n"))
                    sys.exit(-1)

                dhcpdata = self.db.fetchall()
                if dhcpdata:
                    for row in dhcpdata:
                        print '\thost %s {' % row[0]
                        print '\t\thardware ethernet %s;' % row[2]
                        print '\t\toption host-name "%s";' % row[0]
                        print '\t\tfixed-address %s;' % row[1]
                        print '\t}'

                print '}'
        else:
	    print "# This machine is not the primary installer" 
