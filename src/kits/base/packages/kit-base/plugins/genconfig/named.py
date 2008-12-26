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

from kusu.genconfig import Report
import sys
import string
from primitive.system.software.dispatcher import Dispatcher
from primitive.system.software.probe import OS

class thisReport(Report):

    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print self.gettext("genconfig_Named_Help")


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
        if data != '1':
            sys.exit(0)

        _ = self.gettext
        
        # Get the DNS Zone served by the Installer
        dnszone = self.db.getAppglobals('DNSZone')
        if not dnszone:
            sys.stderr.write(_("genconfig_cannot_determine_DNS_zone\n"))
            sys.exit(-1)

        # Get the DNS Forwarders.  This is optional for dhcp public network.
        query = ('select networks.usingdhcp from networks, nodes, ng_has_net where '
                 'nodes.ngid = ng_has_net.ngid and '
                 'ng_has_net.netid = networks.netid and '
                 'networks.type = \'public\' and '
                 'nodes.name = (select appglobals.kvalue from appglobals where '
                 'appglobals.kname = \'PrimaryInstaller\')')
        
        try:
            self.db.execute(query)
        
        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
        
        data = self.db.fetchall()
        
        usingDHCP = True;
        if data:
            # Checking for all public interfaces using iterative and.
            for row in data:
                usingDHCP = row[0] and usingDHCP
        
        dnsforwarders = []
        for key in ['dns1', 'dns2', 'dns3']:
            val = self.db.getAppglobals(key)
            if val: dnsforwarders.append(val)
        dnsforwarders = ','.join(dnsforwarders)
        
        if not dnsforwarders and not usingDHCP:
            sys.stderr.write(_("genconfig_cannot_determine_DNS_forwarders.\nIgnoring...\n"))
            #sys.exit(-1) No need to exit here. Can generate the rest of the config.

        # Get a list of installers IPs.  These will be DNS slave servers
        primaryIPs = []
        query = ('select nics.ip from nics,nodes where '
                 'nics.nid=nodes.nid and '
                 'nodes.name=(select kvalue from appglobals '
                 'where kname=\'PrimaryInstaller\')')
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
            
        data = self.db.fetchall()
        
        if data:
            for row in data: 
                primaryIPs.append(row[0])

        serverIPs = []
        query = ('select nics.ip from nics,nodes where '
                 'nics.nid=nodes.nid '
                 'and nodes.ngid=1')
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
            if ip in serverIPs: serverIPs.remove(ip)

        dnsslaves = ''
        dnsslaves = string.join(serverIPs, ';')

        named_dir = Dispatcher.get('named_dir')
        
        # Generate the file contents
        print "// "
        print "// Dynamically generated by: genconfig  (Do not edit!)"
        print "// "
        print 'options {'
        print '\tdirectory "%s";' % named_dir

        if OS()[0].lower() in ['sles', 'opensuse', 'suse']:
            print ''
            print '\t# Write dump and statistics file to the log subdirectory.'
            print '\t# The path names are relative to the chroot jail.'
            print '\tdump-file "/var/log/named_dump.db";'
            print '\tstatistics-file "/var/log/named.stats";'
        else:
            print '\tdump-file "%s/data/cache_dump.db";' % named_dir
            print '\tstatistics-file "%s/data/named_stats.txt";' % named_dir

        if dnsforwarders != '':
            print '\tforwarders { %s; };' % string.join(string.split(dnsforwarders, ','), ';')
        print '};'
        print ''

        if OS()[0].lower() in ['sles', 'opensuse', 'suse']:
            rndckey = "rndc-key"
        else:
            rndckey = "rndckey"

        print """
//
// a caching only nameserver config
//
controls {
        inet 127.0.0.1 allow { localhost; } keys { %s; };
};
""" % rndckey

        if OS()[0].lower() in ['sles', 'opensuse', 'suse']:
            print """
zone "." in {
        type hint;
        file "root.hint";
};

zone "localhost" in {
        type master;
        file "localhost.zone";
};

zone "0.0.127.in-addr.arpa" in {
        type master;
        file "127.0.0.zone";
};
"""
        else:
            print """
zone "." IN {
        type hint;
        file "named.ca";
};

zone "localdomain" IN {
        type master;
        file "localdomain.zone";
        allow-update { none; };
};

zone "localhost" IN {
        type master;
        file "localhost.zone";
        allow-update { none; };
};

zone "0.0.127.in-addr.arpa" IN {
        type master;
        file "named.local";
        allow-update { none; };
};

zone "0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa" IN {
        type master;
        file "named.ip6.local";
        allow-update { none; };
};

zone "255.in-addr.arpa" IN {
        type master;
        file "named.broadcast";
        allow-update { none; };
};

zone "0.in-addr.arpa" IN {
        type master;
        file "named.zero";
        allow-update { none; };
};
"""

        # Generate the zone entry
        print 'zone "%s" IN {' % dnszone
        print '\ttype %s;' % type
        print '\tfile "%s.zone";' % dnszone
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
        query = ('select distinct network,subnet from ng_has_net,networks where ng_has_net.netid=networks.netid and networks.usingdhcp=False')
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
                if ipbytes[3] != '0':
                    arpaname = "%s.%s.%s.%s" % (ipbytes[3], ipbytes[2],
                                                ipbytes[1], ipbytes[0])
                elif ipbytes[2] != '0':
                    arpaname = "%s.%s.%s" % (ipbytes[2],
                                             ipbytes[1], ipbytes[0])
                
                elif ipbytes[1] != '0':
                    arpaname = "%s.%s" % (ipbytes[1], ipbytes[0])

                else :
                    arpaname = "%s" % (ipbytes[0])

                print 'zone "%s.in-addr.arpa" in {' % arpaname
                print '\ttype %s;' % type
                print '\tfile "%s.rev";' % network
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

