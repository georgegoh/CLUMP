# Copyright (C) 2007 Platform Computing Inc.

# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import os
from kusu.addhost import *
import kusu.core.db
from primitive.system.software.dispatcher import Dispatcher
 
class AddHostPlugin(AddHostPluginBase):
    def updated(self):
        dnsZone = self.dbconn.getAppglobals('DNSZone')
        
        named_dir = Dispatcher.get('named_dir')

        os.system("/opt/kusu/bin/genconfig zone > %s/%s.zone" % (named_dir,dnsZone))
        os.system("kill -HUP `pidof named`")

    def finished(self, nodelist, prePopulateMode):
        dnsZone = self.dbconn.getAppglobals('DNSZone')
        
        named_dir = Dispatcher.get('named_dir')

        os.system("/opt/kusu/bin/genconfig zone > %s/%s.zone" % (named_dir, dnsZone))
        os.system("kill -HUP `pidof named`")
