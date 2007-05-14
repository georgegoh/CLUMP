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

# Author: Shawn Starr <sstarr@platform.com>

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
        
        self.getNodeFormat()
        
        # If the nodeformat is None, return False immediately.
        if not self._nodeFormat:
            return False
            
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
            self._dbReadonly.execute("SELECT nameformat FROM nodegroups WHERE ngid='%s'" % self._nodeGroupType)
            self._nodeFormat = self._dbReadonly.fetchone()[0]
        except:
            self._nodeFormat = None

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
        sqlquery = "SELECT nodes.name FROM nodegroups,nodes WHERE nodes.ngid=nodegroups.ngid"
        
        if ngConflicts:
            sqlquery += " AND ("
            for ngid in ngConflicts:
                sqlquery += "nodegroups.ngid=%s" % ngid
                if ngid:
                    sqlquery += " OR "
            sqlquery += ")"

        if sqlquery[len(sqlquery)-4:].strip() == "OR )":
            sqlquery = sqlquery[:-4].strip() + ")"

        sqlquery += " AND nodes.rack=%d ORDER BY nodes.rack, nodes.rank"

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

        if not nodename:
            return False
            
        if nodename.strip() == self._getPrimaryInstaller():
            return True
        return False
        
    def getNodeID (self, nodename):
        """getNodeID(nodename)
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
        
        if not self._nodeList and not ngConflicts:
            return False

        # Check if the node format has a rack AND rank. If it doesn't set the rack to 0 always,
        if self.isNodenameHasRack() == False:
            self._rackNumber = 0
   
        # Check if node group exists by looking for the nodeformat If it's empty. Abort.
        if self._nodeFormat == None:
            return False
            
        # Build SQL query based on the node groups sharing the same node format.
        sqlquery = "SELECT nodes.rank FROM nodes, nodegroups WHERE nodes.rack=%d AND nodes.ngid=nodegroups.ngid" % self._rackNumber
        
        if ngConflicts:
            sqlquery += " AND ("
            for ngid in ngConflicts:
                sqlquery += "nodegroups.ngid=%s" % ngid
                if ngid:
                    sqlquery += " OR "
            sqlquery += ")"

        if sqlquery[len(sqlquery)-4:].strip() == "OR )":
            sqlquery = sqlquery[:-4].strip() + ")"
        
        sqlquery += " ORDER BY nodes.rank"

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

        if not nodename or nodename == None:
            return False
            
        # We can't be the master installer
        if not self._isMasterInstaller:
            nid = self.getNodeID(nodename)
            if nid == None:
                return False
                
            self._deleteDHCPLease(nodename)
            self._dbRWrite.execute("DELETE FROM nics where nid=%s" % nid)
            self._dbRWrite.execute("DELETE FROM nodes where nid=%s" % nid)
            return True

    def isIPUsed(self, ipaddress):
        """isIPUsed(ipaddress)
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
        
        nodeID = self.getNodeID(self._nodeName)
        interfaces = self._findInterfaces()
        # Iterate though list of interface devices.
        for nicdev in interfaces:
             NICInfo = interfaces[nicdev].split()
             networkID = NICInfo[0]
             subnetNetwork = NICInfo[1]
             self._newIPAddress = NICInfo[2]
             IPincrement = int(NICInfo[3])
             
             while True:
                 if self.isIPUsed(self._newIPAddress):
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
        
        nid = self.getNodeID(nodename)
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
        
        nid = self.getNodeID(nodename)
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
    
    def validateInterface(self, interface):
        """validateInterface(self, interface)
        Checks if the requested interface exists in the database from the primary installer. If it does, returns True, otherwise False"""
        
        self._dbReadonly.execute("SELECT networks.device FROM networks, nics, nodes WHERE nodes.nid=nics.nid \
                                   AND nics.netid=networks.netid AND networks.device='%s' AND \
                                   nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller')" % interface)
        result = self._dbReadonly.fetchone()
 
        try:
            testval = result[0]
            return True
        except:
            return False

    def validateNodegroup(self, nodegroup):
        """validateNodegroup(self, nodegroup)
        Checks if the requested node group exists. If it does, returns True and the ngid, otherwise False"""

        # Check for valid nodegroup.
        self._dbReadonly.execute("SELECT ngid, ngname FROM nodegroups WHERE ngname = '%s'" % nodegroup)
        result = self._dbReadonly.fetchone()
        try:
            testval = result[0]
            return True, testval
        except:
            return False, None

    def validateNode(self, node):
        """validateNode(self, node)
        Checks if the requested node exists or not. If it does, returns True, otherwise False"""
        
        # Check for valid node to replace. if not return an error.
        self._dbReadonly.execute("SELECT nodes.name FROM nodes WHERE nodes.name = '%s'" % node)
        result = self._dbReadonly.fetchone()
 
        try:
            testval = result[0]
            return True
        except:
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
        
        nid = self.getNodeID(nodename)
        try:
            self._dbReadonly.execute("SELECT networks.device FROM networks,nics WHERE networks.netid=nics.netid AND nics.nid=%s and nics.boot = 1" % nid)
        except:
            return None
        try:
            data = self._dbReadonly.fetchone()
            return data[0]
        except:
            return None
        
# Run some unittests
if __name__ == "__main__":
    myNodeFun = NodeFun()

    # Test validateNode
    if myNodeFun.validateNode("node0000"):
        print "* Testing NodeFun.validateNode(\"node0000\"): Result: PASS (Found)"
    else:
        print "* Testing NodeFun.validateNode(\"node0000\"): Result: FAIL (Not found)"
    
    if myNodeFun.validateNode("foobar001") == False:  # Does not exist in database, PASS if NOT found.
        print "* Testing NodeFun.validateNode(\"foobar001\"): Result: PASS (Not found)"
    else:
        print "* Testing NodeFun.validateNode(\"foobar001\"): Result: FAIL (Found)"
    
    # Test findMACAddress
    if myNodeFun.findMACAddress("aa:bb:cc:dd:ee:ff") == False:
        print "* Testing NodeFun.findMACAddress(\"aa:bb:cc:dd:ee:ff\"): Result: PASS (Not found)"
    else:
        print "* Testing NodeFun.findMACAddress(\"aa:bb:cc:dd:ee:ff\"): Result: FAIL (Found)"
    
    if myNodeFun.findMACAddress("00:11:22:33:44:32"):
        print "* Testing NodeFun.findMACAddress(\"00:11:22:33:44:32\"): Result: PASS (Found)"
    else:
        print "* Testing NodeFun.findMACAddress(\"00:11:22:33:44:32\"): Result: FAIL (Not found)"
        
    # Test findBootDevice
    if myNodeFun.findBootDevice("foobar001"):
        print "* Testing NodeFun.findBootDevice(\"foobar001\"): Result: FAIL (Found)"
    else:
        print "* Testing NodeFun.findBootDevice(\"foobar001\"): Result: PASS (Not found)"

    if myNodeFun.findBootDevice("c01-01"):
        print "* Testing NodeFun.findBootDevice(\"c01-01\"): Result: PASS (Found)"
    else:
        print "* Testing NodeFun.findBootDevice(\"c01-01\"): Result: FAIL (Not found)"

    # Test validateNodegroup
    result, ngid = myNodeFun.validateNodegroup("Kusu Rules")
    if result:
        print "* Testing NodeFun.validateNodegroup(\"Kusu Rules\"): Result: FAIL (Found)"
    else:
        print "* Testing NodeFun.validateNodegroup(\"Kusu Rules\"): Result: PASS (Not found)"
    
    result, ngid = myNodeFun.validateNodegroup("Compute Diskless")
    if result:
        print "* Testing NodeFun.validateNodegroup(\"Compute Diskless\"): Result: PASS (Found)"
    else:
        print "* Testing NodeFun.validateNodegroup(\"Compute Diskless\"): Result: FAIL (Not found)"
        
    # Test getNodeInformation
    nodeinfo = myNodeFun.getNodeInformation("hello-00-world00-24")
    if nodeinfo:
        print "* Testing NodeFun.getNodeInformation(\"hello-00-world00-24\"): Result: FAIL (Found)"
    else:
        print "* Testing NodeFun.getNodeInformation(\"hello-00-world00-24\"): Result: PASS (Not found)"
        
    nodeinfo = myNodeFun.getNodeInformation("c02-01")
    if nodeinfo:
        print "* Testing NodeFun.getNodeInformation(\"c02-01\"): Result: PASS (Found)"
        print "* NodeFun.getNodeInformation() Returns: %s" % nodeinfo
    else:
        print "* Testing NodeFun.getNodeInformation(\"c02-01\"): Result: FAIL (Not found)"
        
    # Test isIPused
    if myNodeFun.isIPUsed("192.168.30.62") == False:
        print "* Testing NodeFun.isIPUsed(\"192.168.30.62\"): Result: PASS (IP Not used)"
    else:
        print "* Testing NodeFun.isIPUsed(\"192.168.30.62\"): Result: FAIL (IP Used)"

    if myNodeFun.isIPUsed("10.1.2.13"):
        print "* Testing NodeFun.isIPUsed(\"10.1.2.13\"): Result: PASS (IP used)"
    else:
        print "* Testing NodeFun.isIPUsed(\"10.1.2.13\"): Result: FAIL (IP Not Used)"
        
    # Test getNodeID
    if myNodeFun.getNodeID("gooble092-agZf43t"):
        print "* Testing NodeFun.getNodeID(\"gooble092-agZf43t\"): Result: FAIL (Found)"
    else:
        print "* Testing NodeFun.getNodeID(\"gooble092-agZf43t\"): Result: PASS (Not found)"

    if myNodeFun.getNodeID("host003"):
        print "* Testing NodeFun.getNodeID(\"host003\"): Result: PASS (Found)"
    else:
        print "* Testing NodeFun.getNodeID(\"host003\"): Result: FAIL (Not found)"
    
    del myNodeFun
    
    # Invalid case, No such rack -100 and nodegroup -5.
    myNodeFun = NodeFun(rack=-100, nodegroup=-5)
    if myNodeFun.addNode("aa:bb:cc:dd:ee:ff", "eth0") == False:
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth0\"): Given: Rack -100, ngid -5 (Invalid): Result: PASS (Node group not found)"
    else:
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth0\"): Given: Rack -100, ngid -5 (Invalid): Result: FAIL (Node group found)"
    del myNodeFun
    
    # Valid case, create node in 'Compute' node group.
    myNodeFun = NodeFun(rack=1, nodegroup=2)
    createdNode = myNodeFun.addNode("aa:bb:cc:dd:ee:ff", "eth1")
    if createdNode:
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth1\"): Given: Rack 1, ngid 2 (Compute): Result: PASS (Node created)"
        print "\t* NodeFun.addNode(): Returns: %s" % createdNode
    else:
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth1\"): Given: Rack 1, ngid 2 (Compute): Result: FAIL (Node not created)"
        
    del myNodeFun

    # Valid case, delete created node and check.
    myNodeFun = NodeFun()
    if myNodeFun.deleteNode(createdNode):
        print "* Testing NodeFun.deleteNode(\"%s\"): Result: PASS (Deleted)" % createdNode
        if myNodeFun.validateNode(createdNode) == False:
            print "\t* Confirm Node %s is deleted: NodeFun.validateNode(\"%s\"): Result: PASS (Deleted)" % (createdNode, createdNode)
            createdNode = None
        else:
            print "\t* Confirm Node %s is deleted: NodeFun.validateNode(\"%s\"): Result: FAIL (Not deleted)" % (createdNode, createdNode)
        
    else:
        print "* Testing NodeFun.deleteNode(\"%s\"): Result: FAIL (Not deleted)" % createdNode
        
    # Invalid case, create node in Bogus rack and nodegroup.
    myNodeFun = NodeFun(rack=54645, nodegroup=999999)
    if myNodeFun.addNode("aa:bb:cc:dd:ee:ff", "eth1") == False:
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth1\"): Given: Rack 54645, ngid 999999 (Invalid): Result: PASS (Node group not found)"
        createdNode = None
    else:
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth1\"): Given: Rack 54645, ngid 999999 (Invalid): Result: FAIL (Node created)"
        print "* NodeFun.addNode(): Returns: %s" % createdNode

    del myNodeFun
    # Invalid case, delete created node and check. Shouldn't get to this at all.
    
    if createdNode:
        myNodeFun = NodeFun()
        if myNodeFun.deleteNode(createdNode):
            print "* Testing NodeFun.deleteNode(\"%s\"): Result: PASS (Deleted)" % createdNode
            if myNodeFun.validateNode(createdNode):
                print "\t* Confirm Node %s is deleted: NodeFun.validateNode(\"%s\"): Result: PASS (Deleted)" % (createdNode, createdNode)
            else:
                print "\t* Confirm Node %s is deleted: NodeFun.validateNode(\"%s\"): Result: FAIL (Not deleted)" % (createdNode, createdNode)
        
        else:
            print "* Testing NodeFun.deleteNode(\"%s\"): Result: FAIL (Not deleted)" % createdNode
        
        del myNodeFun

    # Valid case, delete node c02-01
    createdNode = "c02-01"
    myNodeFun = NodeFun()
    if myNodeFun.deleteNode(createdNode):
        print "* Testing NodeFun.deleteNode(\"%s\"): Result: PASS (Deleted)" % createdNode
        if myNodeFun.validateNode(createdNode) == False:
            print "\t* Confirm Node %s is deleted: NodeFun.validateNode(\"%s\"): Result: PASS (Deleted)" % (createdNode, createdNode)
        else:
            print "\t* Confirm Node %s is deleted: NodeFun.validateNode(\"%s\"): Result: FAIL (Not deleted)" % (createdNode, createdNode)
        
    else:
        print "* Testing NodeFun.deleteNode(\"%s\"): Result: FAIL (Not deleted)" % createdNode

    # Invalid case, create node in 'Compute Diskless'
    myNodeFun = NodeFun(rack=2, nodegroup=4)
    if myNodeFun.addNode("aa:bb:cc:dd:ee:ab", "eth1"):
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth1\"): Given: Rack 2, ngid 4 (Compute Diskless): Result: PASS (Node created)"
        print "\t* NodeFun.addNode(): Returns: %s" % createdNode
        if createdNode == "c02-01":
            print "\t* Testing NodeFun.addNode() PASSED. Correct node added."
    else:
            print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth1\"): Given: Rack 2, ngid 4 (Compute Diskless): Result: FAIL (Node not created)"
