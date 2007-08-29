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
import kusu.core.db
from kusu.addhost import *

class AddHostPlugin(AddHostPluginBase):
    def added(self, nodename, info):
        if info:
            self.dbconn.execute("SELECT networks.network FROM networks, ng_has_net, nodes WHERE nodes.name='%s' \
                            AND ng_has_net.netid=networks.netid AND nodes.ngid=ng_has_net.ngid" % nodename)

            networks = self.dbconn.fetchall()

            # Run genconfig for each network
            for net in networks:
                 os.system("/opt/kusu/bin/genconfig reverse %s > /var/named/reverse.%s" % (net[0], net[0]))

    def removed(self, nodename, info):
        if info:
            self.dbconn.execute("SELECT networks.network FROM networks, ng_has_net, nodes WHERE nodes.name='%s' \
                            AND ng_has_net.netid=networks.netid AND nodes.ngid=ng_has_net.ngid" % nodename)
            networks = self.dbconn.fetchall()

            # Run genconfig for each network
            for net in networks:
                 os.system("/opt/kusu/bin/genconfig reverse %s > /var/named/reverse.%s" % (net[0], net[0]))
