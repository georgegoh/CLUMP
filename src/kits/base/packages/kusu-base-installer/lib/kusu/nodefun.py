#!/usr/bin/python
#
# Nodefun class
#
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

# Author: Shawn Starr <sstarr@plaform.com>

import os
import string
import popen2
from kusu.db import KusuDB
import kusu.ipfun

""" class NodeFun
    This class handles adding, deleting, updating, replacing nodes, it also provides functionality to generate a node name. """
class NodeFun:
    def __init__(self, rack=0, nodegroup=None):
        # Housekeeping
        self._nodeList = []
        self._nodeName = None
        self._nodeFormat = None
        self._newIPAddress = None
        self._nodeGroupType = nodegroup
        self._rackNumber = rack
        self._rankCount = 0
        self._isMasterInstaller = False
        
        # Instances of a read and write database.
        self._dbReadonly = KusuDB()
        self._dbRWrite = KusuDB()
                
        # Do a try here
        self._dbReadonly.connect()
        self._dbRWrite.connect('kusudb', 'apache')

    def isNodenameHasRack(self):
        """ isNodenameHasRack()
        Checks if the node format has a Rack AND rank. If it does, returns true, else false """
        
        flag = 0
        # Find special characters
        for i in range (0, len(self._nodeFormat)):
             if self._nodeFormat[i] == "#":
                 flag = 1
                 continue

             if flag:
                 if self._nodeFormat[i] == 'R':
                     return True

        return False	

    def getNodeFormat(self):
        """getNodeFormat()
        Gets and sets the node format from database. """
        
        try:
            self._dbReadonly.execute("SELECT nameformat FROM nodegroups WHERE ngid=%s" % self._nodeGroupType)
            self._nodeFormat = self._dbReadonly.fetchone()[0]
        except:
            self._nodeFormat = None
            raise OperationalError,msg

    def _hostNameParse(self):
        """_hostNameParse()
        Parses the node format and generates the appropriate node name """
        
        flag = 0
        newString = []
        rackNum = 0 
        rankNum = 0
        self._nodeName = None
        tmpR = "%s" % self._rackNumber   # Use rack number, maybe 0 depending on node format.
        tmpN = "%s" % self._rankCount

        # Find special characters and count the number of each special character.
        for i in range (0, len(self._nodeFormat)):
             if self._nodeFormat[i] == "#":
                 flag = 1
                 continue

             if flag == 1:
                 if self._nodeFormat[i] == 'N':
                     flag = 2
                     rankNum += 1
                 elif self._nodeFormat[i] == 'R':
                     flag = 2
                     rackNum += 1
                 continue

             if flag == 2 and self._nodeFormat[i] == 'R' and rackNum:
                 rackNum += 1
             elif flag == 2 and self._nodeFormat[i] == 'N' and rankNum:
                 rankNum += 1
             else:
                 flag = 0
                 if rackNum:
                     newString += tmpR.zfill(rackNum) # zfill fills in padded zeros for you.
                     rackNum = 0
                 if rankNum:
                     newString += tmpN.zfill(rankNum)
                     rankNum = 0
                 newString += self._nodeFormat[i]

        if rackNum:
            newString += tmpR.zfill(rackNum)
        if rankNum:
            newString += tmpN.zfill(rankNum)

        self._nodeName = string.join(newString, "")

    def _getNodes (self):
        """_getNodes()
        Gets the nodes from the database, returns a list of nodes and the conflicting node groups that share the same node format """
        
        self.getNodeFormat()
        self._dbReadonly.execute("SELECT ngid FROM nodegroups WHERE nameformat='%s'" % self._nodeFormat)
        ngConflicts = self._dbReadonly.fetchall()
        
        # Build the SQL query since there many be more than one node group that has the same node group format.
        sqlquery = "SELECT nodes.name FROM nodegroups,nodes WHERE nodes.ngid=nodegroups.ngid AND ("
        for ngid in ngConflicts:
            sqlquery += "nodegroups.ngid=%s" % ngid
            if ngid:
                sqlquery += " OR "

        if sqlquery[len(sqlquery)-3:].strip() == "OR":
                sqlquery = sqlquery[:-4]

        sqlquery += ") AND nodes.rack=%d ORDER BY nodes.rack, nodes.rank"

        self._dbReadonly.execute(sqlquery % self._rackNumber)
        data = self._dbReadonly.fetchall()

        for info in data:
             self._nodeList.append(info[0])
        self._nodeList.sort()
        return self._nodeList, ngConflicts

    def _getPrimaryInstaller(self):
        """_getPrimaryInstaller()
        gets and returns the primary installer name """
        
        return self._dbReadonly.getAppglobals('PrimaryInstaller')
    
    def nodeIsPrimaryInstaller(self, nodename):
        if nodename.strip() == self._getPrimaryInstaller():
            return True
        return False
        
    def _getNodeID (self, nodename):
        """_getNodeID(nodename)
        Returns the node ID if found, otherwise false if nodename is the primary installer name, or not found in db """
        
        if self.nodeIsPrimaryInstaller(nodename):
            return None
        try:
            self._dbReadonly.execute("SELECT nid FROM nodes WHERE nodes.name='%s'" % nodename)
            self._isMasterInstaller = False
            return self._dbReadonly.fetchone()[0]
        except:
             return None
    
    def getNodeInformation(self, nodename):
        """getNodeInformation(nodename)
        Returns node information: nodegroup id, node id, nic id, network id, ip address, mac address, node name """
        
        info = {}
        
        if self.nodeIsPrimaryInstaller(nodename):
            return None
        self._dbReadonly.execute("SELECT nodes.ngid, nodes.nid, nodes.name, nics.netid, nics.ip, nics.mac FROM nodes, nics \
                                   WHERE nodes.name='%s' AND nodes.nid=nics.nid" % nodename)

        data = self._dbReadonly.fetchall()
        
        # Initialize multi dictionary list
        # Format: nodeInfo["nodename"][number_of_interfaces]['key_item']
    
        for i in range(0, len(data)):
             info["%s" % data[i][2]] = {}
        
        for i in range(0, len(data)):
            info["%s" % data[i][2]][i] = {}
            
        for i in range(0, len(data)):
             info["%s" % data[i][2]][i] = {'nodegroupid' : {}, 'nodeid' : {}, 'nicnetid' : {}, 'ipaddress' : {}, 'macaddress' : {}}
             for i in range(0, len(data)):
                  info["%s" % data[i][2]][i]['nodegroupid'] = int(data[i][0])
                  info["%s" % data[i][2]][i]['nodeid'] = int(data[i][1])
                  info["%s" % data[i][2]][i]['nicnetid'] = int(data[i][3])
                  info["%s" % data[i][2]][i]['ipaddress'] = data[i][4]
                  info["%s" % data[i][2]][i]['macaddress'] = data[i][5]
        return info
        
    def addNode (self, macaddr, selectedinterface):
        """newNode()
        Returns a valid node not present in the kusu database. Use this function to create a new node. """
        
        self._nodeList, ngConflicts = self._getNodes()

        # Check if the node format has a rack AND rank.
        self.isNodenameHasRack()

        # Build SQL query based on the node groups sharing the same node format.
        sqlquery = "SELECT nodes.rank FROM nodes, nodegroups WHERE nodes.rack=%d AND nodes.ngid=nodegroups.ngid AND (" % self._rackNumber
        for ngid in ngConflicts:
             sqlquery += "nodegroups.ngid=%d" % ngid
             if ngid:
                 sqlquery += " OR "

        if sqlquery[len(sqlquery)-3:].strip() == "OR":
                sqlquery = sqlquery[:-4]

        sqlquery += ") ORDER BY nodes.rank"

        self._dbReadonly.execute(sqlquery)
        data = self._dbReadonly.fetchall()
        
        # If there's no RANK data found in query, then the rank starts from 0.
        if not len(data):
            self._rankCount = 0
        else:
            # Iterate though the list, increment the rack count if a previous number exists.
            for rankInfo in data:
                 if rankInfo[0] == self._rankCount:
                     self._rankCount += 1
                 else:
                     break

        # If there's no node name in the list. Generate a new one.
        if not len(self._nodeList):
            self._hostNameParse()
        else:
            # Iterate though list, generate a node, check if it exists already in the list. If it does, increment the rank number
            # Otherwise, return the new node name.
            for nodeIdx in self._nodeList:
                 self._hostNameParse()
                 if self._nodeName in self._nodeList:
                     self._rankCount += 1
                 else:
                     self._createNodeEntry(macaddr, selectedinterface)
                     return self._nodeName

        # All existing nodes are consecutive in database, no spaces free, just create a new one (rank of 0).
        self._hostNameParse()
        self._createNodeEntry(macaddr, selectedinterface)
        return self._nodeName

    def deleteNode(self, nodename):
        """deleteNode(nodename)
        Deletes node from database, and calls deleteDHCPLease() to delete the DHCP entry also. """
        
        # We can't be the master installer
        if not self._isMasterInstaller:
            nid = self._getNodeID(nodename)
            self._deleteDHCPLease(nodename)
            self._dbRWrite.execute("DELETE FROM nics where nid='%s'" % nid)
            self._dbRWrite.execute("DELETE FROM nodes where nid='%s'" % nid)

    def _isIPUsed(self, ipaddress):
        """_isIPUsed(ipaddress)
        Checks if the IP is in use, returns false if not, true if it is. """
        
        self._dbReadonly.execute("SELECT COUNT(*) FROM nics WHERE ip = '%s'" % ipaddress)
        result = self._dbReadonly.fetchone()[0]
        if int(result) == 0:
            return False
        return True
        
    def _createNodeEntry(self, macaddr, selectedinterface):
        """createNodeEntry()
        Create a node in the database. """
        
        self._dbRWrite.execute("INSERT INTO nodes (ngid, name, state, bootfrom, rack, rank) VALUES ('%s', '%s', 'Expired', 0, '%s', '%s')" % 
        (self._nodeGroupType, self._nodeName, self._rackNumber, self._rankCount))
        
        nodeID = self._getNodeID(self._nodeName)
        interfaces = self._findInterfaces()
        # Iterate though list of interface devices.
        for nicdev in interfaces:
             NICInfo = interfaces[nicdev].split()
             networkID = NICInfo[0]
             subnetNetwork = NICInfo[1]
             self._newIPAddress = NICInfo[2]
             IPincrement = int(NICInfo[3])
             
             while True:
                 if self._isIPUsed(self._newIPAddress):
                      self._newIPAddress = kusu.ipfun.incrementIP(self._newIPAddress, IPincrement, subnetNetwork)
                 else:
                    break
                
             # We're a DHCP/boot interface
             if nicdev == selectedinterface:
                 self._createNICBootEntry(nodeID, networkID, self._newIPAddress, 1, macaddr)
                 self._writeDHCPLease(self._newIPAddress, macaddr)
             else:
             # Not a boot interface, just write out other info.
                 self._createNICBootEntry(nodeID, networkID, self._newIPAddress, 0)

    def replaceNodeEntry(self, nodename):
        """replaceNodeEntry(nodename)
        Replaces an existing node, first by deleting the existing DHCP entry for the node since it contains the old mac address. 
        Then setting the MAC address to NULL so a new DHCP request may be done.  """
        
        nid = self._getNodeID(nodename)
        if not self._isMasterInstaller:
            self._deleteDHCPLease(nodename)
            self._dbRWrite.execute("UPDATE nics SET mac=NULL WHERE nid='%s'" % nid)
            self._dbRWrite.execute("UPDATE nodes SET state='Expired' WHERE nid='%s'" % nid)
            return True
        else:
            print "Error: Cannot replace the primary installer!!!!"
            return False
    
    def replaceNICBootEntry(self, nodename, macaddress):
        """replaceNICBootEntry(nodename, macaddress)
        Replaces nics table containing new mac address for replaced node """
        
        nid = self._getNodeID(nodename)
        self._dbRWrite.execute("UPDATE nics SET mac='%s' WHERE nid='%s' AND boot = 1" % (macaddress, nid))
        self._dbReadonly.execute("SELECT nics.ip FROM nics WHERE nics.nid=%s AND boot = 1" % nid)
        data = self._dbReadonly.fetchone()[0]
        self._nodeName = nodename
        # Recreate DHCP lease, this time using the new mac address found
        self._writeDHCPLease(data, macaddress)
            
    def _createNICBootEntry(self, nodeid, networkid, ipaddress, bootflag, macaddress=None):
        """createNICBootEntry(nodeid, networkid, ipaddress, bootflag, macaddress)
        Creates NIC entries for a specific node. If there's a mac address specified. Then that nic table entry 
        will have its bootdhcp flag enabled. Otherwise, other network interfaces cannot be PXE booted from. """
        
        if macaddress:
            self._dbRWrite.execute("INSERT INTO nics (nid, netid, mac, ip, boot) VALUES ('%s', '%s', '%s', '%s', '%s')" % (nodeid, networkid, macaddress, ipaddress, bootflag))
        else:
            self._dbRWrite.execute("INSERT INTO nics (nid, netid, ip, boot) VALUES ('%s', '%s', '%s', '%s')" % (nodeid, networkid, ipaddress, bootflag))
   
    def _writeDHCPLease(self, ipaddr, macaddr):
        """writeDHCPLease(ipaddr, macaddr)
        Use DHCP's API to create a DHCP entry in the /var/lib/dhcpd/dhcpd.leases file """
        
        fromchild, tochild = popen2.popen2("/usr/bin/omshell")
        tochild.write("connect\n")
        tochild.flush()
        tochild.write("new host\n")
        tochild.flush()
        tochild.write('set name = "%s"\n' % self._nodeName)
        tochild.flush()
        tochild.write("set hardware-address = %s\n" % macaddr)
        tochild.flush()
        tochild.write("set hardware-type = 1\n")  # Set to Ethernet
        tochild.flush()
        tochild.write("set ip-address = %s\n" % ipaddr)
        tochild.flush()
        tochild.write("create\n")
        tochild.flush()
        tochild.close()
        fromchild.close()

    def _deleteDHCPLease(self, nodename):
        """writeDHCPLease(nodename)
        Use DHCP's API to delete a DHCP entry in the /var/lib/dhcpd/dhcpd.leases file """
        
        fromchild, tochild = popen2.popen2("/usr/bin/omshell")
        tochild.write("connect\n")
        tochild.flush()
        tochild.write("new host\n")
        tochild.flush()
        tochild.write('set name = "%s"\n' % nodename)
        tochild.flush()
        tochild.write("open\n")
        tochild.flush()
        tochild.write("remove\n")
        tochild.close()
        fromchild.close()
    
    def findMACAddress(self, macaddr):
        self._dbReadonly.execute("SELECT mac FROM nics WHERE mac='%s'" % macaddr)
        try:
          result = self._dbReadonly.fetchone()[0] 
          # Mac address exists
          return True
        except:
          # Mac address does not exist
          return False
        
    def _findInterfaces(self):
        """findInterfaces()
        Returns a dictionary containing Networks ID number, Subnetwork, Starting IP Address and IP Increment value.
        The dictionary uses the device name as its key item[1]. """
        
        interfaceInfo = {}
        self._dbReadonly.execute("SELECT networks.netid, networks.device, networks.subnet, networks.startip, networks.inc FROM \
                                   networks,ng_has_net WHERE ng_has_net.netid=networks.netid AND ng_has_net.ngid = %s AND \
                                   networks.usingdhcp = 0" % self._nodeGroupType)
        data = self._dbReadonly.fetchall()
        for item in data:
             interfaceInfo[item[1]] = "%d %s %s %s" % (item[0], item[2], item[3], item[4])
        return interfaceInfo

    def findBootDevice(self, nodename):
        """findBootDevice()
        Returns the boot device that has its boot flag set to 1 """
        
        nid = self._getNodeID(nodename)
        self._dbReadonly.execute("SELECT networks.device FROM networks,nics WHERE networks.netid=nics.netid AND nics.nid=%s and nics.boot = 1" % nid)
        data = self._dbReadonly.fetchone()
        return data[0]
        
