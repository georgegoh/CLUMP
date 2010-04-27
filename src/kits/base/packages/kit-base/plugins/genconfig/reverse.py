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
from IPy import IP
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
            return True

        network = ''
        if pluginargs:
            network = pluginargs[0]
        else:
            self.toolHelp()
            return False
        try:
            largest_sn = IP('%s/32' % network)
        except ValueError:
            sys.stderr.write('ERROR:  Invalid network: %s!\n' % network)
            return False
            
        _ = self.gettext
            
        # Test the network given
        query = ('select netid, network, subnet from networks '
                 'where network="%s" and type<>"public"' % network)
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            return False

        networks = {} #all networks, {id:IP}
        data = self.db.fetchall() or []
        for row in data:
            nid, net, mask = row
            try:
                networks[nid] = IP('%s/%s' % (net, mask))
                #Need to find the largest subnet for unmanaged node
                if largest_sn < networks[nid]:
                   largest_sn = networks[nid]
            except ValueError:
                sys.stderr.write('ERROR:  Skip invalid network: %s/%s!\n' % (net, mask))

        if not networks:
            sys.stderr.write('ERROR:  Database contains no valid record of network: %s!\n' % network)
            return False

        # Get the name of the primary installer
        primaryinst = self.db.getAppglobals('PrimaryInstaller')
        if not primaryinst:
            sys.stderr.write(_("genconfig_cannot_determine_primary_installer\n"))
            return False

        # Get the DNS Zone served by the Installer
        dnszone = self.db.getAppglobals('DNSZone')
        if not dnszone:
            sys.stderr.write(_("genconfig_cannot_determine_DNS_zone\n"))
            return False

        # Get the name of the primary mail server
        mailserv = self.db.getAppglobals('SMTPServer')
        if not mailserv:
            servesmtp = self.db.getAppglobals('InstallerServeSMTP')
            if servesmtp == 'True':
                mailserv = '%s.%s' % (primaryinst, dnszone)

        # Get the default installer provision network's netid
        query = 'SELECT networks.netid '\
                'FROM nodes, nics, networks, ng_has_net WHERE nics.nid = nodes.nid '\
                'AND nics.netid = networks.netid AND networks.usingdhcp = False '\
                'AND networks.type = "provision" AND networks.suffix != "-bmc" '\
                'AND ng_has_net.netid = nics.netid AND ng_has_net.ngid = 1 '\
                'AND nodes.ngid = 1 ORDER BY networks.type, nics.boot desc, networks.device'

        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            return False

        self.default_installer_provision_netid = self.db.fetchone() or []

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


        # Print out all the NS entries, exclude public IP
        query = ('select nodes.name, nics.ip, networks.suffix '
                 'from nodes, nics, networks '
                 'where nodes.ngid=1 and nodes.nid=nics.nid and networks.netid=nics.netid '
                 'and networks.usingdhcp=False and networks.type<>"public"')
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            return Flase
            
        data = self.db.fetchall()
        
        if data:
            for row in data:
                dnsname, ip, nssuffix = row
                if not nssuffix: nssuffix = ''
                print '\t\tIN\tNS\t%s%s.%s.' % (dnsname, nssuffix, dnszone)
        else:
            sys.stderr.write("ERROR:  No private NS records in PCM domain: %s!\n", dnszone)
            return False
        print ''


        #got the unmanaged node group id
        umngid = self.db.getNgidOf('unmanaged')

        # Print out all the available managed nodes for this network
        query = ('select nodes.name,nodes.ngid,nics.ip,nics.boot,nics.netid,networks.suffix,networks.type '
                 'from nodes,nics,networks '
                 'where nodes.nid in (select nid from nics where network="%s") '
                 'and nodes.nid=nics.nid and nics.netid=networks.netid '
                 'and networks.type<>"public" and nodes.ngid<>%d '
                 'order by nodes.name, networks.device' % (network, umngid))
        try:
            self.db.execute(query)
        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            return False

        prev_dns_name = ''               #the previous dnsname
        written_short_name = False       #already give short name flag

        data = self.db.fetchall() or []

        for row in data:
            dnsname, ngid, ip, boot, netid, suffix, nettype = row
            if not suffix: suffix = ''

            if prev_dns_name != dnsname:
                #node changed
                written_short_name = False
                prev_dns_name = dnsname

            queried_net = networks.get(netid)
            if not written_short_name and ( (ngid == 1 and netid in self.default_installer_provision_netid) or \
                                            (ngid != 1 and self._is_name_short(nettype, suffix, boot)) ):
                written_short_name = True
                if queried_net:
                    arpaname = self._getarpaentry(ip, queried_net.strNetmask())
                    print '%s\tIN\tPTR\t%s.%s.' % (arpaname, dnsname, dnszone)
            else:
                if queried_net:
                    arpaname = self._getarpaentry(ip, queried_net.strNetmask())
                    print '%s\tIN\tPTR\t%s%s.%s.' % (arpaname, dnsname, suffix, dnszone)

        #Print out all unmanaged node on this network
        query = ('select nodes.name, nics.ip '
                 'from nodes,nics '
                 'where nodes.nid=nics.nid and nodes.ngid=%d '
                 'order by nics.ip' % umngid)
        try:
            self.db.execute(query)
        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            return False

        data = self.db.fetchall() or []
        for row in data:
            dnsname, ip = row
            if ip not in largest_sn:
                continue

            arpaname = self._getarpaentry(ip, largest_sn.strNetmask())
            print '%s\tIN\tPTR\t%s.%s.' % (arpaname, dnsname, dnszone)

    def _getarpaentry(self, ip, mask):
        # Need to find the portion of the IP address to print.
        # This should support classless subnets
        subbytes = string.split(mask, '.')
        ipbytes = string.split(ip, '.')
        if subbytes[0] != '255':
            print "# Subnet = %s, subbytes[0] = %s" % (mask, subbytes[0])
            arpaname = "%s.%s.%s.%s" % (ipbytes[3], ipbytes[2],
                                        ipbytes[1], ipbytes[0])
        elif subbytes[1] != '255':
            arpaname = "%s.%s.%s" % (ipbytes[3],
                                     ipbytes[2], ipbytes[1])
        elif subbytes[2] != '255':
            arpaname = "%s.%s" % (ipbytes[3], ipbytes[2])
        else:
            arpaname = "%s" % (ipbytes[3])

        return arpaname

    def _is_name_short(self, nettype, suffix, boot):
        #check the nics can be short name
        return nettype == 'provision' and suffix != '-bmc' and boot
