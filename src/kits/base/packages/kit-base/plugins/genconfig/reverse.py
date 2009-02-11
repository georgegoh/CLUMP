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

import sys
import string
import time
from kusu.genconfig import Report
from kusu.ipfun import *

class thisReport(Report):
    
    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print self.gettext("genconfig_Reverse_Help")


    def runPlugin(self, pluginargs):
        """runPlugin - This method provides the database report for this
        plugin.  All plugins must implement this method."""
        
        # Test to see if the Installer node should be running DNS.
        dnsenabled = self.db.getAppglobals('InstallerServeDNS')
        if dnsenabled != '1':
            sys.exit(0)

        network = ''
        if pluginargs:
            network = pluginargs[0]
        else:
            self.toolHelp()
            sys.exit(-1)
            
        _ = self.gettext
            
        # Test the network given
        query = ('select subnet, suffix from networks where network=\'%s\'' % network)
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
            
        data = self.db.fetchone()
        if data:
            subnet, suffix = data
        else:
            sys.stderr.write('ERROR:  Database contains no record of network: %s!\n' % network)
            sys.exit(-1)

        # Get the name of the primary installer
        primaryinst = self.db.getAppglobals('PrimaryInstaller')
        if not primaryinst:
            sys.stderr.write(_("genconfig_cannot_determine_primary_installer\n"))
            sys.exit(-1)

        # Get the DNS Zone served by the Installer
        dnszone = self.db.getAppglobals('DNSZone')
        if not dnszone:
            sys.stderr.write(_("genconfig_cannot_determine_DNS_zone\n"))
            sys.exit(-1)

        # Get the name of the primary mail server
        mailserv = self.db.getAppglobals('SMTPServer')
        if not mailserv:
            servesmtp = self.db.getAppglobals('InstallerServeSMTP')
            if servesmtp == 'True':
                mailserv = '%s.%s' % (primaryinst, dnszone)

        
        # Generate the file contents
        print "; "
        print "; Dynamically generated by: genconfig  (Do not edit!)"
        print "; "
        print '; Reverse file for: %s' % network
        print '$TTL 2d    ; 172800 secs default TTL for zone'
        print '@\t\tIN\tSOA\t%s.%s. root.%s. (' % (primaryinst, dnszone, dnszone)
        tmp = '%f' % time.time()
        serial = string.split(tmp, '.')[0]
        print '\t\t\t%s\t; Serial number' % serial
        print '\t\t\t4h\t; Refresh'
        print '\t\t\t15m\t; Update retry time'
        print '\t\t\t24h\t; Expiry time'
        print '\t\t\t3h\t; Minimum'
        print '\t\t\t)'


        # Print out all the NS entries
        query = ('select nodes.name, nics.ip, networks.suffix from '
                 'nodes, nics, networks where '
                 'nodes.ngid=1 and nics.nid=nodes.nid and '
                 'networks.netid=nics.netid and networks.usingdhcp=False')
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
            
        data = self.db.fetchall()
        
        if data:
            for row in data:
                dnsname, ip, nssuffix = row
                outline = '\t\tIN\tNS\t%s' % dnsname
                if nssuffix and nssuffix != '':
                    outline += '%s' % nssuffix
                outline += '.%s.' % dnszone
                print outline
                
        print ''

        # Print out all the available names for this network
        query = ('select nodes.name, nics.ip, networks.suffix from '
                 'nodes,nics,networks where nodes.nid=nics.nid and '
                 'nics.netid=networks.netid and networks.network=\'%s\' '
                 'order by nics.ip' % network)

        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)
            
        data = self.db.fetchall()

        if data:
            for row in data:
                dnsname, ip, suffix = row
                if not onNetwork(network, subnet, ip):
                    continue
		
                # Need to find the protion of the IP address to print.
                # This should support classless subnets
                subbytes = string.split(subnet, '.')
                ipbytes = string.split(ip, '.')
                if subbytes[0] != '255':
                    print "Subnet = %s, subbytes[0] = %s" % (subnet, subbytes[0])
                    arpaname = "%s.%s.%s.%s" % (ipbytes[3], ipbytes[2],
                                                ipbytes[1], ipbytes[0])
                elif subbytes[1] != '255':
                    arpaname = "%s.%s.%s" % (ipbytes[3],
                                             ipbytes[2], ipbytes[1])
                elif subbytes[2] != '255':
                    arpaname = "%s.%s" % (ipbytes[3], ipbytes[2])
                else:
                    arpaname = "%s" % (ipbytes[3])
                
                outline = '%s\tIN\tPTR\t%s' % (arpaname, dnsname)
                if suffix and suffix != '':
                    outline += '%s' % suffix
                print '%s.%s.' % (outline, dnszone)
        else:
            print "; No data on this network"
