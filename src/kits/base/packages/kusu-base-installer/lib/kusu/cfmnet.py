#!/usr/bin/python

# $Id$

# cfmsnet.py - The Cluster File Management network library 

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

import os
import sys
import string
import socket
import time


class CFMNet:
    """This class contains the code for creating and sending the update notification
    packets.  It will construct the packet to send, update the sequence number, then
    send the packet."""



    def __init__(self):
        """__init__ - initializer for the class"""
        self.port       = 65001
        self.seqfile    = '/etc/.cfm.sequence'
        self.sequence   = 0      # The sequence number of the packet
        self.type       = 0      # The type of update to perform (Numeric)
        self.waittime   = 30     # Maximum random time to wait before client downloads
        self.ngid       = 0      # The node group ID to update  (0=all)
        self.version    = 0      # Packet version number
        self.installers = []     # List of installer IP's capable of providing files
        self.broadcasts = []     # List of broadcast IP's to send to
        self.resends    = 5      # Number of times to resend the broadcast
        self.sleep      = 1      # Time to wait between broadcasts


    def __setInstallers(self, installers):
        """__setInstallers - Populate the list of installers.  Limit the number
        so that we do not exceed the MTU."""
        cnt = 0
        self.installers = []
        for i in installers:
            self.installers.append(i)
            cnt = cnt + 1
            if cnt == 10:
                break


    def __updateSequence(self):
        """__updateSequence  - Set the current sequence number and update
        the file to a new sequence number."""
        if os.path.exists(self.seqfile):
            # Read and increment the sequence number
            filep = open(self.seqfile, 'r')
            for line in filep.readlines():
                if line[0] == '#':
                    continue
                try:
                    self.sequence = string.atoi(line)
                except:
                    print "ERROR:  The sequence file: %s does not have a valid format" % self.seqfile
                    sys.exit(1)

        filep = open(self.seqfile, 'w')
        newseq = self.sequence + 1
        filep.write('%i\n' % newseq)
        filep.close()

    
    def __buildMessage(self):
        message = 'MaRkScFm'
        message += "%08x" % self.sequence
        message += "%08x" % self.version
        message += "%08x" % self.type
        message += "%08x" % self.ngid
        message += "%08x" % self.waittime

        for i in range(0,10):
            if i >= len(self.installers):
                message += "00000000"
            else:
                substr = string.split(self.installers[i], '.')
                for num in substr:
                    message += "%02x" % string.atoi(num)
                    
        return message
    

    def __sendBroadcast(self):
        """__sendBroadcast() - Send the broadcast message out all of the interfaces"""
        
        port = 0
        try:
            port = socket.getservbyname('cfmd', 'udp')
        except:
            port = self.port

        message = self.__buildMessage()
        for ip in self.broadcasts:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(message, (ip, port))
            sock.close()
            print "Sending to %s" % ip


    def sendPacket(self, installers, broadcasts, type, ngid=0, waittime=30):
        """sendPacket - This method does the work of sending the update packet
        """
        self.__setInstallers(installers)
        self.broadcasts = broadcasts
        self.type     = type
        self.ngid     = ngid
        self.waittime = waittime

        self.__updateSequence()

        for i in range(0, self.resends):
            self.__sendBroadcast()
            time.sleep(self.sleep)


if __name__ == '__main__':
    # Use Etherreal to inspect the packet for validity. 
    p = CFMNet()
    p.sendPacket(['172.25.243.3', '10.0.0.1'], ['172.25.243.255', '10.255.255.255'], 0, 0, 30)

