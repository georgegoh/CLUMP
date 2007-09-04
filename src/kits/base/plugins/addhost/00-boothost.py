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

class AddHostPlugin(AddHostPluginBase):
    def added(self, nodename, info, prePopulateMode):
           if prePopulateMode == False:
	      os.system("/opt/kusu/sbin/boothost -n %s" % nodename)

    def removed(self, nodename, info):
	try:
             testnode = info[nodename][0]["macaddress"]
	except:
	     return -1

	macaddr = "01:%s" % info[nodename][0]["macaddress"]
	macaddr = macaddr.replace(':','-')
	if os.path.isfile("/tftpboot/kusu/pxelinux.cfg/%s" % macaddr):
             os.system("rm -f /tftpboot/kusu/pxelinux.cfg/%s" % macaddr)
             return 0
        else:
             return -1

    def finished(self, nodelist):
           try:
               self.dbconn.execute('SELECT nodegroups.ngname FROM nodegroups, nodes WHERE nodes.ngid=nodegroups.ngid AND \
                                    nodes.name="%s"' % nodelist[0])
               ngname = self.dbconn.fetchone()[0]
               os.system("/opt/kusu/sbin/boothost -t %s" % ngname)
           except:
               pass
     
