#!/usr/bin/python

#   Copyright 2007 Platform Computing Corporation
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

import os


MAXARGS=32000

class syncfun:
    """This is the class containing the metdods for synchronizing nodes.
    This includes the pdsh functions, and rsync ones"""
    def __init__(self):
        pass

    def runPdsh(self, hosts, command):
        """runPdsh - Use pdsh to run a command on a list of hosts.
        USE:   runPdsh(hosts, command where:
            hosts = A list containing the names of all the hosts
                    to run the command on.
            command = The command to run on each of the hosts.
        Returns:  A list with the output of pdsh in it.
            """
        global MAXARGS
        output = []
        hposition = 0

        if hosts == '' or command == '':
            return output

        # The number of hosts may exceed the length of the command line
        # buffer.  Much of the code below is to deal with that.
        while 1:
            hostlist = ''
            
            for hpos in range(hposition, len(hosts)):
                hostname = "%s" % hosts[hpos]
                hostlist += hostname
                hostlist += ','
                
                hposition = hpos + 1
                if len(hostlist) > MAXARGS:
                    break

            hostlist = hostlist[:-1]

            cmd = "/usr/bin/pdsh -w " + hostlist + " -- " + command
            try:
                for retline in os.popen(cmd).readlines():
                    # Insert the results into the list
                    output.append(retline)
            except:
                print "ERROR:  Unable to run:  /usr/bin/pdsh -w ... -- %s" % command 

            if hposition >= len(hosts):
                break

        return output
        
