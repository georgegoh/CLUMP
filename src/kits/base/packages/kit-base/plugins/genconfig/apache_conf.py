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

from primitive.configtool.plugins import BasePlugin
from primitive.configtool.commands import ConfigCommand
from primitive.system.software.dispatcher import Dispatcher
from primitive.system.software.probe import OS

from path import path
 
class ApacheConfPlugin(BasePlugin):
    def validateArgs(self, args_dict):
        pass

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

        # publicdnszone = self.db.getAppglobals('PublicDNSZone')
        # if not publicdnszone:
            # sys.stderr.write(_("genconfig_cannot_determine_Public_DNS_zone\n"))
            # sys.exit(-1)

        # Determine the list of networks that this installer can serve
        query = ('select distinct network, subnet from networks where network is not NULL')
        try:
            self.db.execute(query)

        except:
            sys.stderr.write(_("DB_Query_Error\n"))
            sys.exit(-1)

        allowlist = []
        data = self.db.fetchall()
        if data:
            for row in data:
                network, subnet = row
                allowlist.append('%s/%s' % (network, subnet))
        allowlist.append('127.0.0.1')
    
        wwwroot = path(Dispatcher.get('webserver_docroot'))
        reposdir = wwwroot / 'repos'
        imagesdir = wwwroot / 'images'

        os = OS()[0].lower()
        cacheDisabled = False

        if os in ['rhel', 'centos', 'fedora']:
            disableCache = True
        elif os in ['sles', 'opensuse', 'suse']:
            disableCache = False

        c = ConfigCommand(name='apache_conf',
                          template='file:///opt/kusu/lib/plugins/genconfig/apache_conf.tmpl',
                          plugin=ApacheConfPlugin,
                          plugin_args={'installer': installer, 'dnszone': dnszone, 
                                       'allowlist': allowlist, 
                                       'reposdir': reposdir, 
                                       'imagesdir': imagesdir, 
                                       'cfmdir': cfmdir,
                                       'wwwdir': wwwroot,
                                       'disableCache': disableCache})
        print c.execute()
