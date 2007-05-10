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

import os

class AddHostPlugin:
    def finished(self, dbconn):
	#print "dhcpd.py: called AddHostPlugin->finished()"
	#print "dhcpd.py: system call: /opt/kusu/bin/dbreport dhcpd"
	os.system("/opt/kusu/bin/dbreport.py dhcpd > /etc/dhcpd.conf")
	os.system("/etc/init.d/dhcpd restart")
