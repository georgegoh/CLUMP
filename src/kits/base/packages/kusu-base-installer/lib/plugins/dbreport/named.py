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

import dbreport
import sys
import string

class thisReport(dbreport.Report):

    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print self.gettext("dbreport_Named_Help")


    def runPlugin(self, pluginargs):
        """runPlugin - This method provides the database report for this
        plugin.  All plugins must implement this method."""

        # What type of file should we generate
        type = 'master'
        if pluginargs and pluginargs[0] == 'slave':
            type = 'slave'

        
        # Test to see if the Installer node should be running DNS.
        dnsenabled = 0
        data = self.db.getAppglobals('InstallerServeDNS')
        if data != 'True':
            sys.exit(0)

        _ = self.gettext
        
        # Get the DNS Zone served by the Installer
        dnszone = self.db.getAppglobals('DNSZone')
        if not dnszone:
            sys.stderr.write(_("dbreport_cannot_determine_DNS_zone\n"))
            sys.exit(-1)

        # Get the DNS Forwarders.  This might be optional
        dnsforwarders = self.db.getAppglobals('DNSForwarders')
        if not dnsforwarders:
            sys.stderr.write(_("dbreport_cannot_determine_DNS_forwarders\n"))
            sys.exit(-1)

        # Get a list of installers IPs.  These will be DNS slave servers
        primaryIPs = []
        query = ('select nics.ip from nics,nodes where '
                 'nics.nid=nodes.nid and '
                 'nodes.name=(select kvalue from appglobals '
                 'where kname="PrimaryInstaller")')
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
            
        data = self.db.fetchall()
        
        if data:
            for row in data: 
                primaryIPs.append(row[0])

        print primaryIPs
        serverIPs = []
        query = ('select nics.ip from nics,nodes,nodegroups where '
                 'nics.nid=nodes.nid and nodegroups.ngname="Installer" '
                 'and nodegroups.ngid=nodes.ngid')
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
            
        data = self.db.fetchall()
        if data:
            for row in data: 
                serverIPs.append(row[0])

        # The Primary Installer is the DNS master, strip it out of the
        # serverIPs, so the serverIPs only contains the Secondary DNS Masters
        for ip in primaryIPs:
            serverIPs.remove(ip)

        dnsslaves = ''
        dnsslaves = string.join(serverIPs, ';')
        
        # Generate the file contents
        print "# "
        print "# Dynamically generated by: dbreport  (Do not edit!)"
        print "# "
        print 'options {'
        print '\tdirectory "/var/named";'
        print '\tversion "Sparky_Dog";'
        print '\tnotify "yes";'
        print '\tdump-file "/var/named/data/cache_dump.db";'
        print '\tstatistics-file "/var/named/data/named_stats.txt";'
        if dnsforwarders != '':
            print '\tforwarders { %s; };' % string.join(string.split(dnsforwarders, ','), ';')
        print '};'
        print ''

        # Generate the root DNS config
        print 'zone "." in{'
        print '\ttype hint;'
        print '\tfile "named.root";'
        print '};'
        print ''

        # Generate the standard localhost entries
        print 'zone "localhost" in {'
        print '\ttype master;'
        print '\tfile "zone.localhost";'
        print '\tallow-update { none; };'
        print '};'
        print ''
        print 'zone "0.0.127.in-addr.arpa" in {'
        print '\ttype master;'
        print '\tfile "reverse.localhost";'
        print '\tallow-update { none; };'
        print '};'
        print ''

        # Generate the zone entry
        print 'zone "%s" IN {' % dnszone
        print '\ttype %s;' % type
        print '\tfile "zone.%s";' % dnszone
        if type == 'master':
            print '\tnotify yes;'
            print '\tallow-update { none; };'
            if dnsslaves != '':
                print '\tallow-transfer { %s; };' % dnsslaves
        else:
            print '\tmasters { %s; };' % string.join(primaryIPs, ';')

        print '};'
        print ''

        # Generate the in-addr.arpa entries for all subnets
        query = ('select network, subnet from networks')
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
            
        data = self.db.fetchall()
        if data:
            for row in data:
                network, subnet = row
                ipbytes = string.split(network, '.')
                if ipbytes[3] != 0:
                    arpaname = "%s.%s.%s.%s" % (ipbytes[3], ipbytes[2],
                                                ipbytes[1], ipbytes[0])
                elif ipbytes[2] != 0:
                    arpaname = "%s.%s.%s" % (ipbytes[2],
                                             ipbytes[1], ipbytes[0])
                
                elif ipbytes[1] != 0:
                    arpaname = "%s.%s" % (ipbytes[1], ipbytes[0])

                else :
                    arpaname = "%s" % (ipbytes[0])

                print 'zone "%s.in-addr.arpa" in {' % arpaname
                print '\ttype %s;' % type
                print '\tfile "reverse.%s";' % network
                if type == 'master':
                    print '\tnotify yes;'
                    print '\tallow-update { none; };'
                    if dnsslaves != '':
                        print '\tallow-transfer { %s; };' % dnsslaves
                else:
                    print '\tmasters { %s; };' % string.join(primaryIPs, ';')

                print '};'
                print ''
                    
        print 'include "/etc/rndc.key";'

                
