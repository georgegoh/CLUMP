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
import sys
from kusu.addhost import *

global removedMode
removedMode = False

class AddHostPlugin(AddHostPluginBase):
      def removed(self, nodename, info):
          global removedMode
          removedMode = True

      def finished(self, nodeList, prePopulateMode):
          global removedMode
          if removedMode:
             # Remove host(s) from root's .ssh/known_hosts file.
             if os.path.exists("/root/.ssh/known_hosts"):
                rptr = open("/root/.ssh/known_hosts", 'r')
             else:
                print "Could not find /root/.ssh/known_hosts, ignoring plugin"
                return

             wptr = open("/tmp/known_hosts.root", 'w')
             
             data = rptr.readlines()
             rptr.close()
             new_data = []
             for line in data: 
                 flag = 0
                 # Check node list for match
                 for node in nodeList:
                     if node == line.split(',')[0]: 
                        #print "FOUND A MATCH: %s" % line.split(',')[0]
                        flag = 1
                 if not flag:
                    #print "LEAVE NODE: %s" % line.split(',')[0]
                    new_data.append(line)
                      
             wptr.writelines(new_data)
             wptr.close()
             os.rename("/tmp/known_hosts.root", "/root/.ssh/known_hosts")
