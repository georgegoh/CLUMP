# $Id$
#
#  Copyright (C) 2007 Platform Computing Inc
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

import sys
from kusu.genconfig import Report

class thisReport(Report):

    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print self.gettext("genconfig_Apache_Help")


    def runPlugin(self, pluginargs):
        """runPlugin - This method provides the database report for this
        plugin.  All plugins must implement this method.  This plugin will
        generate the dhcpd.conf file contents."""

        _ = self.gettext

        # Need to get the name of the primary installer so we can see which networks
        # we need to install on.
        installer = self.db.getAppglobals('PrimaryInstaller')
        if not installer:
            sys.stderr.write(_("genconfig_cannot_determine_primary_installer\n"))
            sys.exit(-1)

        # Get the DNS Zone served by the Installer
        dnszone = self.db.getAppglobals('DNSZone')
        if not dnszone:
            sys.stderr.write(_("genconfig_cannot_determine_DNS_zone\n"))
            sys.exit(-1)
            
        cfmdir = self.db.getAppglobals('CFMBaseDir')
        if not cfmdir:
            sys.stderr.write(_("genconfig_cannot_determine_cfmbasedir\n"))
            sys.exit(-1)

        print "# "
        print "# Dynamically generated by: genconfig  (Do not edit!)"
        print "# "
        print "# Changes needed in this file should be made in the"
        print "# apache_conf.py plugin."
        print ""
        print "UseCanonicalName Off"
        print "ServerName %s.%s" % (installer, dnszone)
        print "CacheDisable /cfm"
        print ""
        # Forget mod_python.  Does not work with MySQLDb module, and php
        # print "LoadModule python_module modules/mod_python.so"  
        print ""

        # Determine the list of networks that this installer can serve
        query = ('select distinct network, subnet from networks where network is not NULL')
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)

        allowlist = ''
        data = self.db.fetchall()
        if data:
            for row in data:
                network, subnet = row
                allowlist = allowlist + '\tAllow from %s/%s\n' % (network, subnet)
        allowlist = allowlist + '\tAllow from 127.0.0.1'

        # Allow access to the Repos        
        print '<Directory "/var/www/html/repos/">'
        print '\tOptions FollowSymLinks Indexes ExecCGI'
        #print '\tAddHandler mod_python .py'
        #print '\tPythonHandler mod_python.publisher'
        #print '\tPythonDebug On'
        print '\tSetEnv PYTHONPATH /opt/kusu/lib/python'
        print '\tAddHandler cgi-script cgi'
        print '\tAllowOverride None'
        print '\tOrder deny,allow'
        print allowlist
        print '\tDeny from all'
        print '</Directory>'
        print ''

        # Allow access to the Images
        print '<Directory "/var/www/html/images/">'
        print '\tOptions FollowSymLinks Indexes'
        print '\tAllowOverride None'
        print '\tOrder deny,allow'
        print allowlist
        print '\tDeny from all'
        print '</Directory>'
        print ''
        
        # Allow access to the CFM base directory
        print '<Directory "%s">' % cfmdir
        print '\tOptions FollowSymLinks Indexes'
        print '\tAllowOverride None'
        print '\tOrder deny,allow'
        print allowlist
        print '\tDeny from all'
        print '</Directory>'
        print ''

        query = ("SELECT nics.ip "
                 "FROM nics, nodes, networks WHERE nics.nid = nodes.nid "
                 "AND nics.netid = networks.netid AND networks.usingdhcp=0 "
                 "AND networks.type = 'public' AND nodes.ngid!=5 ORDER BY nics.ip")

        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)

        #Configure rewrite rule to rewrite URL in to Zope
        data = self.db.fetchone()
        if data:
            print '<VirtualHost *:80>'
            print 'RewriteEngine On'
            print 'RewriteRule ^/$ http://%{HTTP_HOST}/Plone/ [R]'
            print 'RewriteRule ^/Plone$ http://%{HTTP_HOST}/Plone/ [R]'
            print 'RewriteRule ^/Plone/(.*) http://%{HTTP_HOST}:8080/VirtualHostBase/http/%{HTTP_HOST}:80/VirtualHostRoot/Plone/$1 [L,P]'
            print '</VirtualHost>'
