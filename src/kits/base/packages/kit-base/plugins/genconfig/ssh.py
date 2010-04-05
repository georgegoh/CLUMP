# $Id: ssh.py 3135 2009-10-23 05:42:58Z ltsai $
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
from primitive.configtool.plugins import BasePlugin
from primitive.configtool.commands import ConfigCommand

class SSHConfigPlugin(BasePlugin):
    def validateArgs(self, args_dict):
        pass


class thisReport(Report):
    
    def toolHelp(self):
        print self.gettext("genconfig_Ssh_Help")

    def runPlugin(self, pluginargs):
       # Get the DNS Zone served by the Installer
        dnszone = self.db.getAppglobals('DNSZone')
        if not dnszone:
            sys.stderr.write(self.gettext("genconfig_cannot_determine_DNS_zone\n"))
            sys.exit(0)

        query = ('select nics.ip,nodes.name,networks.suffix,nics.boot '
                 'from nics,nodes,networks where nics.nid = nodes.nid '
                 'and nics.netid = networks.netid and '
                 'networks.usingdhcp = False order by nics.ip')

        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)
        else:
            hosts = self.db.fetchall()


        c = ConfigCommand(name='ssh_config',
                          template='file:///opt/kusu/lib/plugins/genconfig/ssh_config.tmpl',
                          plugin=SSHConfigPlugin,
                          plugin_args={'dnszone': dnszone, 'hosts': hosts})
        print c.execute()
