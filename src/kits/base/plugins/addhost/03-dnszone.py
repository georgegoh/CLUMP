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

import kusu.db
import os
 
class AddHostPlugin:
    def added(self, dbconn, nodename, info):
        dnsZone = dbconn.getAppglobals('DNSZone')
        os.system("/opt/kusu/bin/genconfig zone > /var/named/zone.%s" % dnsZone)

    def removed(self, dbconn, nodename, info):
        dnsZone = dbconn.getAppglobals('DNSZone')
        os.system("/opt/kusu/bin/genconfig zone > /var/named/zone.%s" % dnsZone)
