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
from kusu.genconfig import Report
from primitive.configtool.plugins import BasePlugin
from primitive.configtool.commands import ConfigCommand

class PAMConfigPlugin(BasePlugin):
    def validateArgs(self, args_dict):
        pass


class thisReport(Report):
    
    def toolHelp(self):
        print self.gettext("genconfig_pam_config_Help")

    def runPlugin(self, pluginargs):

        c = ConfigCommand(name='pam_config',
                          template='file:///opt/kusu/lib/plugins/genconfig/pam_conf_rhelfamily.tmpl',
                          plugin=PAMConfigPlugin,
                          plugin_args=None)
        print c.execute()
