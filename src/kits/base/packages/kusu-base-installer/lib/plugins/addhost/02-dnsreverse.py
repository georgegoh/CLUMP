# Copyright (C) 2007 Platform Computing Corporation

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
	#print "dbreport-reverse.py: called AddHostPlugin->added()"
	dbconn.execute("SELECT networks.network FROM networks, ng_has_net, nodes WHERE nodes.name='%s' \
                        AND ng_has_net.netid=networks.netid AND nodes.ngid=ng_has_net.ngid" % nodename)

        networks = dbconn.fetchall()
	for net in networks:
	     # Run dbeport for each network
	     #print "dbreport-reverse.py: Will run /opt/kusu/bin/dbreport reverse %s" % net
	     #os.system("/opt/kusu/bin/dbreport reverse %s" % net)
	     pass

    def removed(self, dbconn, nodename, info):
	if info:
            #print "dbreport-reverse.py: called AddHostPlugin->removed()"
	    print "DEBUG: %s" % nodename
            dbconn.execute("SELECT networks.network FROM networks, ng_has_net, nodes WHERE nodes.name='%s' \
                            AND ng_has_net.netid=networks.netid AND nodes.ngid=ng_has_net.ngid" % nodename)
            networks = dbconn.fetchall()
            for net in networks:
                 # Run dbeport for each network
	         #print "dbreport-reverse.py: Will run /opt/kusu/bin/dbreport reverse %s" % net
                 #os.system("/opt/kusu/bin/dbreport reverse %s" % net)
                 pass
