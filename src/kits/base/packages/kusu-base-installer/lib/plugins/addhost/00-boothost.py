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
	#print "boothost.py: called AddHostPlugin->added()"
	#print "boothost.py: system call: /opt/kusu/sbin/boothost -n %s" % nodename
	os.system("/opt/kusu/sbin/boothost -n %s" % nodename)

    def removed(self, dbconn, nodename, info):
	try:
             testnode = info[nodename][0]["macaddress"]
	except:
	     return -1

        #print "boothost.py: AddHostPlugin->removed(): nodeName = %s" % nodename
	#print "boothost.py: Removing node with mac: %s" % info[nodename][0]["macaddress"]
	macaddr = "01:%s" % info[nodename][0]["macaddress"]
	macaddr = macaddr.replace(':','-')
	if os.path.isfile("/tftpboot/kusu/pxelinux.cfg/%s" % macaddr):
             #print "boothost.py: Deleting: /tfpboot/kusu/pxelinux.cfg/%s" % macaddr
             os.system("rm -f /tftpboot/kusu/pxelinux.cfg/%s" % macaddr)
             return 0
        else:
             #print "boothost.py: No PXE File /tftpboot/kusu/pxelinux.cfg/%s found." % macaddr
             return -1
