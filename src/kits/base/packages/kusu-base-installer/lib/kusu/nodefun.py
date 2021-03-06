#!/usr/bin/env python
#
# Nodefun class
#
# $Id$
#
# Copyright (C) 2007 Platform Computing Inc

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
try:
    import subprocess
except:
    from popen5 import subprocess
import tempfile
import sys
from IPy import IP
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
from kusu.core import database
import kusu.ipfun
from kusu.util.errors import UserExitError
from kusu.util.verify import verifyFQDN, verifyIP
from kusu.util.tools import getClusterHostNames

def createDB():
    engine = os.getenv('KUSU_DB_ENGINE')
    if engine == 'mysql':
        dbdriver = 'mysql'
    else:
        dbdriver = 'postgres'
    dbdatabase = 'kusudb'
    dbuser = 'apache'
    dbpassword = None

    return database.DB(dbdriver, dbdatabase, dbuser, dbpassword)


class NodeFun(object, KusuApp):
    """
    This class handles adding, deleting, updating, replacing nodes.
    It also provides functionality to generate a node name.
    """

    def __init__(self, rack=0, nodegroup=None):
        KusuApp.__init__(self)
        # Housekeeping
        self.kusuApp = KusuApp()
        self._nodeList = {}
        self._nodeName = None
        self._nodeFormat = None
        self._nodeGroupType = nodegroup
        self._rackNumber = rack
        self._rankCount = 0
        self._isMasterInstaller = False
        self._primaryInstaller = ""
        self._cachedDeviceIPs = {}
        self._nodegroupInterfaces = {}
        self._cachedUsedIP = None
        self._preservedBMCIP = {}
        self._cachedMACAddress = {}
        self._installerNetworks = None
        # For specifying IP address for NG node: kusu-addhost -n -x
        self._specifiedIPAddr = None

        # Instances of a read and write database.
        self._dbReadonly = KusuDB()
        self._dbRWrite = KusuDB()
        self._database = createDB()
                
        try:
            self._dbReadonly.connect()
            self._dbRWrite.connect('kusudb', 'apache')
            # Cache primary installer value
            self._primaryInstaller = self._dbReadonly.getAppglobals('PrimaryInstaller')
        except:
            print self.kusuApp._("DB_Query_Error\n")
            sys.exit(-1)

        # Get a list of all the IPs sorted.
        if not self._cachedUsedIP:
            self._getUsedIPs()
            self._getMACAddresses()
            self.getNodeFormat()
            if self._nodeGroupType:
                self._nodegroupInterfaces = self._findInterfaces()
            self._installerNetworks = self._getInstallerNetworks()
            self._ngConflicts = self._getNodegroupConflicts()
            self._nodeList = self._getSelectedNodes()
            self._getPreservedBMCIPs()

    def _getInstallerNetworks(self):
        # Get the installer's subnet and network information.
        query = ('SELECT networks.subnet, networks.network \
                  FROM networks, nics, nodes \
                  WHERE nodes.nid=nics.nid AND nics.netid=networks.netid AND \
                      nodes.name=(SELECT kvalue FROM appglobals WHERE kname="PrimaryInstaller")')
        self._dbReadonly.execute(query)
        return self._dbReadonly.fetchall()

    def setRackNumber(self, rack):
        self._rackNumber = rack

    def setSpecifiedIPAddr(self, ipaddr):
        self._specifiedIPAddr =  ipaddr
  
    def setRankNumber(self, rank):
        self._rankCount = rank

    def getRankNumber(self):
        return self._rankCount

    def getNGNetworks(self):
        # get all provisioning networks for selected NG.
        if not self._nodeGroupType:
            return []
        self._dbReadonly.execute('select networks.* from networks, ng_has_net where \
                                  networks.netid = ng_has_net.netid and \
                                  networks.type = "provision" and \
                                  ng_has_net.ngid = %s' % self._nodeGroupType)
        return self._dbReadonly.fetchall()
 
    def getNodegroupByName(self, ngname):
        self._dbReadonly.execute('SELECT ngid FROM nodegroups WHERE ngname = "%s"' % ngname)
        return self._dbReadonly.fetchone()[0]

    def getNodegroupFromNode(self, node):
        self._dbReadonly.execute('select ngname from nodegroups, nodes \
                                  where nodegroups.ngid = nodes.ngid and \
                                      nodes.name = \'%s\'' % node)
        return self._dbReadonly.fetchone()[0]

    def nodegroupNameFormatMatches(self, src_ngname, dst_ngname):
        self._dbReadonly.execute('select nameformat from nodegroups where ngname = \'%s\'' % src_ngname)
        src_nameformat = self._dbReadonly.fetchone()[0]
        self._dbReadonly.execute('select nameformat from nodegroups where ngname = \'%s\'' % dst_ngname)
        dst_nameformat = self._dbReadonly.fetchone()[0]
        return src_nameformat == dst_nameformat

    def allNodegroupsHaveSameNameFormat(self, nglist):
        self._dbReadonly.execute('select distinct nameformat from nodegroups \
                                  where ngname in %s' % seq2tplstr(nglist))
        if self._dbReadonly.rowcount == 1:
            return True
        return False

    def allNodesHaveSameNameFormat(self, nodelist):
        self._dbReadonly.execute('select distinct nodegroups.nameformat \
                                  from nodegroups, nodes \
                                  where nodegroups.ngid = nodes.ngid \
                                  and nodes.name in %s' % seq2tplstr(nodelist))
        return self._dbReadonly.rowcount == 1

    def getAllNodesInNodeGroups(self, ngnamelist):
        self._dbReadonly.execute('select nodes.name from nodes, nodegroups \
                                  where nodegroups.ngid = nodes.ngid and \
                                  nodegroups.ngname in %s' % seq2tplstr(ngnamelist))
        nodelist = [node[0] for node in self._dbReadonly.fetchall()]
        return nodelist

    def checkNodesForOldHostname(self, node_list, dst_ngname):
        dst_ngid = self.getNodegroupByName(dst_ngname) 
        for node in node_list:
            self._dbReadonly.execute('select nics.mac from nodes, nics \
                                      where nics.nid = nodes.nid and \
                                      nodes.name = \'%s\'' % node)
            mac = self._dbReadonly.fetchone()[0]
            if not self.findOldHostnameForNode(mac, dst_ngid):
                return False
        return True           

    def _getUsedIPs(self):
        self._cachedUsedIP = {}
        self._dbReadonly.execute("SELECT nics.ip from nics")
        ips = self._dbReadonly.fetchall()
      
        for i in range(0, len(ips)):
            self._cachedUsedIP["%s" % ips[i][0]] = 'Used'

    def _getPreservedBMCIPs(self):
        self._preservedBMCIP = {}
        preserveNodeIP = self._dbReadonly.getAppglobals('PRESERVE_NODE_IP')
        if preserveNodeIP != '1':
            return
        self._dbReadonly.execute("SELECT distinct bmcip, mac from alteregos where bmcip != ''")
        ips = self._dbReadonly.fetchall()

        for ip, mac in ips:
            #{bmcip:mac,...}
            self._preservedBMCIP[ip] = mac

    def isPreservedBMCIP(self, bmcip, exclude_mac=None):
        """Check if given BMC ip is preserved by some node, except for exclude_mac"""
        preserved_mac = self._preservedBMCIP.get(bmcip)
        if preserved_mac:
            return preserved_mac != exclude_mac
        return False

    def validBMCIPForNode(self, bmcip, mac):
        if self.isIPUsed(bmcip):
            return False

        for nicName, nicInfo in self._nodegroupInterfaces.items():
            if nicName.lower() != 'bmc':
                continue
            if nicInfo['subnet'] == 'None':
                return False
            network = kusu.ipfun.getNetwork(nicInfo['startip'], nicInfo['subnet'])
            if self.isPreservedBMCIP(bmcip, exclude_mac=mac):
                return False
            return kusu.ipfun.onNetwork(network, nicInfo['subnet'], bmcip, nicInfo['startip'])

        #BMC network not found
        return False

    def _getMACAddresses(self):
        self._dbReadonly.execute("SELECT mac FROM nics")
        macs = self._dbReadonly.fetchall()
        
        for i in range(0, len(macs)):
            self._cachedMACAddress["%s" % macs[i][0]] = 'Used'

    def _addUsedIP(self, ip):
        self._cachedUsedIP[ip] = 'Used'

    def addUsedMAC(self, mac):
        self._cachedMACAddress[mac] = 'Used'

    def isNodenameHasRack(self):
        """Checks if the node format has a Rack AND rank.
        If it does, returns true, else false """
        
        flag = 0
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

    def compareRankAvailable(self, rank):
        return rank == self._rankCount

    def getNodeFormat(self):
        """Gets and sets the node format from database. """
        try:
            self._dbReadonly.execute("SELECT nameformat FROM nodegroups \
                                      WHERE ngid='%s'" % self._nodeGroupType)
            self._nodeFormat = self._dbReadonly.fetchone()[0]
        except:
            self._nodeFormat = None

    def _genHostName(self):
        """Generate compute node name. If the current generated name has
        name clash with any existing node (including unmanaged node)
        then regenerate the node name until there is no name clash."""

        self._hostNameParse()
        # If the generated hostname is in use, increment the rank number
        while self.validateNode(self._nodeName):
            self._rankCount += 1
            self._hostNameParse()

    def _hostNameParse(self):
        """Parses the node format and generates the appropriate node name """
        
        flag = 0
        newString = []
        rackNum = 0 
        rankNum = 0
        self._nodeName = None
        tmpR = "%s" % self._rackNumber   # Use rack number, may be 0 depending on node format.
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

        self._nodeName = string.join(newString, "").lower()

    def _getNodegroupConflicts(self):
        self._dbReadonly.execute("SELECT ngid FROM nodegroups \
                                  WHERE nameformat='%s'" % self._nodeFormat)
        conflicts = self._dbReadonly.fetchall()
        return conflicts

    def _getAllNodes(self):
        sqlquery = 'SELECT nodes.name FROM nodes,nodegroups \
                    WHERE nodes.ngid=nodegroups.ngid AND \
                        NOT nodes.name=(SELECT kvalue FROM appglobals WHERE kname="PrimaryInstaller")'
        self._dbReadonly.execute(sqlquery)
        data = self._dbReadonly.fetchall()
        return [ node[0] for node in data ]
            
    def _getSelectedNodes(self):
        """Gets selected based nodes from the database.
        Returns a list of nodes and the conflicting node groups that 
        share the same node format """
       
        # Build the SQL query since there may be more than one nodegroup
        # that has the same node group format.
        sqlquery = "SELECT nodes.name FROM nodegroups,nodes WHERE nodes.ngid=nodegroups.ngid"
    
        if self._ngConflicts:
            sqlquery += " AND ("
            for ngid in self._ngConflicts:
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
            if not self._nodeList.has_key(info[0]):
                self._nodeList[info[0]] = info[0]
        return self._nodeList

    def _getPrimaryInstaller(self):
        """Returns the primary installer name."""
        return self._primaryInstaller
    
    def nodeIsPrimaryInstaller(self, nodename):
        if not nodename:
            return False
        return nodename.strip() == self._getPrimaryInstaller()
        
    def getNodeID (self, nodename, skip_master=True):
        """Returns the node ID if found.
        Returns false if nodename is the primary installer name, or not found in db """

        # return None for FE node if skip_master
        if self.nodeIsPrimaryInstaller(nodename) and skip_master:
            self._isMasterInstaller = True
            print self._("remove_primary_installer_error\n")
            return None
        try:
            self._dbReadonly.execute("SELECT nid FROM nodes WHERE nodes.name='%s'" % nodename)
            self._isMasterInstaller = False
            return self._dbReadonly.fetchone()[0]
        except:
            return None
    
    def getNodeInformation(self, nodename):
        """Returns the following node information: 
        nodegroup id, node id, nic id, network id, ip address, mac address, node name """
        
        info = {}
        self._dbReadonly.execute("SELECT nodes.ngid, nodes.nid, nodes.name, nics.netid, "
                                 "nics.ip, nics.mac, nodes.rack, nodes.rank, networks.device, nics.boot "
                                 "FROM nodes, nics, nodegroups, networks "
                                 "WHERE nodes.name='%s' AND nodes.ngid = nodegroups.ngid "
                                 "AND nics.netid=networks.netid AND nodes.nid=nics.nid" % nodename)

        data = self._dbReadonly.fetchall()
        
        # Initialize multi dictionary list
        # Format: nodeInfo["nodename"][number_of_interfaces]['key_item']
    
        for i in range(0, len(data)):
            info["%s" % data[i][2]] = {}
        
        for i in range(0, len(data)):
            info["%s" % data[i][2]][i] = {}
            
        for i in range(0, len(data)):
            info["%s" % data[i][2]][i] = {'nodegroupid' : {}, 'nodeid' : {}, 'nicnetid' : {}, 'ipaddress' : {}, 'macaddress' : {}, 'rack' : {}, 'rank' : {}}
            for i in range(0, len(data)):
                info["%s" % data[i][2]][i]['nodegroupid'] = int(data[i][0])
                info["%s" % data[i][2]][i]['nodeid'] = int(data[i][1])
                info["%s" % data[i][2]][i]['nicnetid'] = int(data[i][3])
                info["%s" % data[i][2]][i]['ipaddress'] = data[i][4]
                info["%s" % data[i][2]][i]['macaddress'] = data[i][5]
                info["%s" % data[i][2]][i]['rack'] = data[i][6]
                info["%s" % data[i][2]][i]['rank'] = data[i][7]
                info["%s" % data[i][2]][i]['nicname'] = data[i][8]
                info["%s" % data[i][2]][i]['boot'] = data[i][9]
        return info

    def addNode(self, macaddr, selectedinterface, installer=True, 
            unmanaged=False, snackInstance=None, ipaddr=None, 
            hostname=None, uid='', bmc_ip=None):
        """Returns a valid node not present in the kusu database.
        Use this function to create a new node. """
        if not self._nodeList and not self._ngConflicts:
            return False

        # Check if the node format has a rack AND rank.
        # If it doesn't, set the rack to 0 always,
        if self.isNodenameHasRack() == False:
            self._rackNumber = 0
   
        # Check if node group exists by looking for the nodeformat.
        # If it's empty, abort.
        if self._nodeFormat == None:
            return False

        preserveNodeIP = self._dbReadonly.getAppglobals('PRESERVE_NODE_IP')

        if not bmc_ip and preserveNodeIP == '1':
            bmc_ip = self.findOldBMCIPForNode(macaddr, int(self._nodeGroupType))

        if not hostname and (preserveNodeIP == '1'):
            hostname = self.findOldHostnameForNode(macaddr, int(self._nodeGroupType))

        # Use the hostname if provided. 
        if hostname:
            self._rackNumber = self._rankCount = 0
            if preserveNodeIP == '1':
                # verify whether mac and hostname already exist in alteregos table
                query="select rack, rank from alteregos where name = '%s' and mac = '%s'" % (hostname, macaddr)
                self._dbReadonly.execute(query)
                data = self._dbReadonly.fetchone()
                if data:
                    self._rackNumber = data[0]
                    self._rankCount = data[1]

            # Verify whether this hostname is still valid.  
            if not self.validateNode(hostname):
                self._nodeName = hostname
                self._createNodeEntry(macaddr, selectedinterface, False, installer, unmanaged=unmanaged, snackinstance=snackInstance, ipaddr=ipaddr, uid=uid, bmc_ip=bmc_ip)
                return self._nodeName

        # The hostname provided by the user is not valid, generate new hostname.
        # Build SQL query based on the node groups sharing the same node format.
        sqlquery = "SELECT nodes.rank FROM nodes, nodegroups \
                    WHERE nodes.rack=%d AND nodes.ngid=nodegroups.ngid" % self._rackNumber
        if self._ngConflicts:
            sqlquery += " AND ("
            for ngid in self._ngConflicts:
                sqlquery += "nodegroups.ngid=%s" % ngid
                if ngid:
                    sqlquery += " OR "
            sqlquery += ")"

        if sqlquery[len(sqlquery)-4:].strip() == "OR )":
            sqlquery = sqlquery[:-4].strip() + ")"
        
        if preserveNodeIP == '1':
            sqlquery += " UNION "
            nodegroup_ids = map(str, [ngid[0] for ngid in self._ngConflicts])
            sqlquery += "SELECT alteregos.rank FROM alteregos \
                         WHERE alteregos.rack=%d AND alteregos.ngid in (%s) \
                             AND rank IS NOT NULL" % (self._rackNumber, ', '.join(nodegroup_ids))
            sqlquery += " ORDER BY rank"
        else:
            sqlquery += " ORDER BY nodes.rank"

        self._dbReadonly.execute(sqlquery)
        data = self._dbReadonly.fetchall()
        # If there's no RANK data found in query, then the rank starts from 0 
        # otherwise if setRankCount called, use that rank number as starting point.
        if not len(data):
            # We may not be a matching node format, but the node format 
            # may have a rack and rank. Check the rack and rank to verify
            while True:
                sqlquery = "SELECT COUNT(rack) FROM nodes \
                            WHERE rack=%d AND rank=%d AND ngid=%d" % \
                            (self._rackNumber, self._rankCount, int(self._nodeGroupType))
                self._dbReadonly.execute(sqlquery)
                data = int(self._dbReadonly.fetchone()[0])
                if data == 0: 
                    break
                else:
                    self._rankCount += 1
        else:
            # Iterate though the list, increment the rack count if a previous number exists.
            for rankInfo in data:
                if rankInfo[0] == self._rankCount:
                    self._rankCount += 1
                else:
                    break

        preserveNodeIP = self._dbReadonly.getAppglobals('PRESERVE_NODE_IP')

        if hostname and (preserveNodeIP == '1'):
            # verify if mac and hostname already exist in alteregos table
            query="select rack, rank from alteregos \
                   where name = '%s' and mac = '%s'" % (hostname, macaddr)
            self._dbReadonly.execute(query)
            data = self._dbReadonly.fetchone()
            if data:
                self._rackNumber = data[0]
                self._rankCount = data[1]

            # Verify whether this hostname is still valid.  
            if not self.validateNode(hostname):
                self._nodeName = hostname
                self._createNodeEntry(macaddr, selectedinterface, False,
                        installer, unmanaged=unmanaged, snackinstance=snackInstance,
                        ipaddr=ipaddr, uid=uid, bmc_ip=bmc_ip)
                return self._nodeName

        # If there's no node name in the list. Generate a new one.
        if not len(self._nodeList):
            self._genHostName()
        else:
            # Iterate though list, generate a node and check if it already
            # exists already in the list. If it does, increment the rank number.
            # Otherwise, return the new node name.
            for i in range(1, len(self._nodeList)):
                 self._genHostName()
                 if self._nodeList.has_key(self._nodeName):
                     self._rankCount += 1
                 else:
                     self._createNodeEntry(macaddr, selectedinterface, False, 
                             installer, unmanaged=unmanaged, snackinstance=snackInstance,
                             ipaddr=ipaddr, uid=uid, bmc_ip=bmc_ip)
                     return self._nodeName

        # All existing nodes are consecutive in database, 
        # no spaces free, just create a new one (rank of 0).
        self._genHostName()
        self._createNodeEntry(macaddr, selectedinterface, False,
                installer, unmanaged=unmanaged, snackinstance=snackInstance,
                ipaddr=ipaddr, uid=uid, bmc_ip=bmc_ip)
        return self._nodeName

    def deleteNode(self, nodename):
        """Deletes node from database. Also calls deleteDHCPLease()
        to delete the DHCP entry."""
        if not nodename or nodename == None:
            return False
            
        # We can't be the master installer
        if not self._isMasterInstaller:
            nid = self.getNodeID(nodename)
            if nid == None:
                print "Node '%s' not found" % nodename
                return False
                
            self._deleteDHCPLease(nodename)
            self._dbRWrite.execute("DELETE FROM nics where nid=%s" % nid)
            self._dbRWrite.execute("DELETE FROM nodes where nid=%s" % nid)
            return True

    def getNodesFromNodegroup(self, ngid):
        """Get the node names list ordered by nodes.name for a specified nodegroup. """
        self._dbReadonly.execute("SELECT nodes.name FROM nodes \
                                  WHERE ngid=%s ORDER BY nodes.name" % ngid)
        return self._dbReadonly.fetchall()

    def nodeHasNICEntry(self, nid, netid):
        query = 'SELECT COUNT(*) FROM nics WHERE nid=%s AND netid=%s' % (nid, netid)
        try:
            self._dbReadonly.execute(query)
        except:
            return False
        if not self._dbReadonly.fetchone()[0]:
            return False
        return True

    def isIPUsed(self, ipaddress):
        """Checks if the IP is in use. Returns false if not, true if it is. """
        return self._cachedUsedIP.has_key(ipaddress)

    def _createNodeEntry(self, macaddr, selectedinterface, dhcpUnmanaged=False,
            installer=True, unmanaged=False, static=False,
            snackinstance=None, ipaddr=None, uid='', bmc_ip=None):
        """Create a node in the database. """
        flag = 0
        installer_subnet = None
        installer_network = None
        interfaces = {}

        if self._nodeList.has_key(self._nodeName):
            return

        if static == False:
            self._nodegroupInterfaces = self._findInterfaces()

        if static == True:
            unmanagedID = self.getNodegroupByName('unmanaged')
            self._dbRWrite.execute("INSERT INTO nodes (ngid, name, state, bootfrom, rack, rank, uid) \
                    VALUES ('%s', '%s', 'Installed', False, '%s', '%s', '%s')" % \
                    (unmanagedID, self._nodeName, self._rackNumber, self._rankCount, uid))
        else:
            self._dbRWrite.execute("INSERT INTO nodes (ngid, name, state, bootfrom, rack, rank, uid) \
                    VALUES ('%s', '%s', 'Expired', False, '%s', '%s', '%s')" % \
                    (self._nodeGroupType, self._nodeName, self._rackNumber, self._rankCount, uid))

        if self._dbRWrite.driver == 'mysql':
            self._dbRWrite.execute("SELECT last_insert_id()")
        else: #hardcode to postgres for now
            self._dbRWrite.execute("SELECT last_value from nodes_nid_seq")
        nodeID = self._dbRWrite.fetchone()[0]

        # Add the node to the 'used' list of nodes in db.
        self._nodeList[self._nodeName] = self._nodeName

        # Get selected installer's subnet and network information.
        interfaces.update(self._nodegroupInterfaces)

        if installer:
            self._dbReadonly.execute("SELECT networks.subnet, networks.network \
                    FROM networks, nics, nodes \
                    WHERE nodes.nid=nics.nid AND \
                        nics.netid=networks.netid AND \
                        networks.usingdhcp=False AND \
                        nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller') AND \
                        networks.device='%s'" % selectedinterface)

            # Use the gui selected network interface as the installer's interface.
            installer_subnet, installer_network = self._dbReadonly.fetchone()

        if static == False:
            if self._nodegroupInterfaces == {}:
                print "ERROR:  Could not add nodes on interface '%s'. This interface is marked as DHCP only. Please try a different interface\n" % selectedinterface
                if os.path.isfile("/var/lock/subsys/kusu-addhost"):
                    os.unlink("/var/lock/subsys/kusu-addhost")
                sys.exit(-1)
 
        if not installer:
            for subnet, network in self._installerNetworks:
                # We don't need to check other subnets only one needs to pass
                if flag:
                    break

                NICInfo = interfaces[selectedinterface]

                networkID = NICInfo['netid']
                subnetNetwork = NICInfo['subnet']
               
                if self._cachedDeviceIPs.has_key(selectedinterface):
                    startIP = self._cachedDeviceIPs[selectedinterface]
                else:
                    try: 
                        startIP = NICInfo['startip']
                    except:
                        print "ERROR: Cannot add a host to an interface that uses DHCP. Please choose a different network."
                        self._dbRWrite.execute("DELETE from nodes where nid = %s" % nodeID)
                        if os.path.isfile("/var/lock/subsys/kusu-addhost"):
                            os.unlink("/var/lock/subsys/kusu-addhost")
                        sys.exit(-1)

                IPincrement = int(NICInfo['incr'])
                ngGateway = NICInfo['gateway']
                if ipaddr:
                    iphint = True
                else:
                    iphint = False

                while True:
                    # if the desired ip address of the node is provided, then
                    # try to assign it. Must not fail if moving to unmanaged
                    if iphint:
                        if (kusu.ipfun.onNetwork(network, subnet, ipaddr) and 
                                not self.isIPUsed(ipaddr) and 
                                not self.isPreservedBMCIP(ipaddr)) or unmanaged:
                            self._cachedDeviceIPs[selectedinterface] = ipaddr
                            self._addUsedIP(ipaddr)
                            self._createNICBootEntry(nodeID, networkID, True, ipaddr, macaddr)
                            self._writeDHCPLease(ipaddr, macaddr)
                            del interfaces[selectedinterface]
                            flag = 1
                            break
                        else:
                            # we cannot use the desired IP address, so nuke the desired IP
                            # and skip the 'if ipaddr' branch of code.
                            iphint = False
                    # If desired ip address is not provided, then try to provide an IP.
                    elif kusu.ipfun.onNetwork(network, subnet, startIP) or unmanaged:
                        if self.isIPUsed(startIP) or self.isPreservedBMCIP(startIP):
                            try:
                                startIP = kusu.ipfun.incrementIP(startIP, IPincrement, subnetNetwork)
                            except:
                                # Delete the bogus entry created
                                print "ERROR:  Too many hosts specified for network. Choose a bigger network."
                                self._dbRWrite.execute("DELETE from nodes where nid = %s" % nodeID)
                                if os.path.isfile("/var/lock/subsys/kusu-addhost"):
                                    os.unlink("/var/lock/subsys/kusu-addhost")
                                sys.exit(-1)
                        else:
                            # We're a DHCP/boot interface
                            self._cachedDeviceIPs[selectedinterface] = startIP
                            self._addUsedIP(startIP)
                            self._createNICBootEntry(nodeID, networkID, True, startIP, macaddr)
                            self._writeDHCPLease(startIP, macaddr)
                            del interfaces[selectedinterface]
                            flag = 1
                            break
                    else:
                        break
            if not flag:
                self._dbRWrite.execute("DELETE FROM nodes where nodes.ngid=%s AND nodes.name='%s'" % (self._nodeGroupType, self._nodeName))
                print "ERROR:  Could not create nodes on interface '%s'. Please try a different interface\n" % selectedinterface
                if os.path.isfile("/var/lock/subsys/kusu-addhost"):
                    os.unlink("/var/lock/subsys/kusu-addhost")
                sys.exit(-1)

        # Iterate though interface devices that are found
        for nicdev in interfaces:
             NICInfo = []
             NICInfo = interfaces[nicdev]
             networkID = NICInfo['netid']
             excludeMac = None

             # 3rd party DHCP server network interface
             if NICInfo['subnet'] == None and NICInfo['gateway'] == None and NICInfo['startip'] == None:
                 self._createNICBootEntry(nodeID, networkID, False)
                 continue

             subnetNetwork = NICInfo['subnet']

             # If the interface has no subnet (maybe DHCP based)
             if subnetNetwork == "None":
                 self._createNICBootEntry(nodeID, networkID, False)
                 continue

             if self._cachedDeviceIPs.has_key(nicdev):
                 newIP = self._cachedDeviceIPs[nicdev]
             else:
                 newIP = NICInfo['startip']

             # For bmc nic, try to use the given bmc_ip.
             # And if not given the bmc_ip, try to find a unused/unpreserved ip from startip. 
             if nicdev.lower() == 'bmc':
                 excludeMac = macaddr
                 newIP = bmc_ip or newIP

             # in installer mode: we set newIP as user specified one for the installer network.
             if self._specifiedIPAddr:
                 provnet = IP(NICInfo['startip']).make_net(NICInfo['subnet'])
                 if IP(self._specifiedIPAddr) in provnet:
                     newIP = self._specifiedIPAddr
 
             IPincrement = int(NICInfo['incr'])
             try:
                 ngGateway = NICInfo['gateway']
             except:
                 ngGateway = None
                 pass  # For nodes without a gateway
            
             while True:
                 if self.isIPUsed(newIP) or self.isPreservedBMCIP(newIP, excludeMac):
                     try:
                         newIP = kusu.ipfun.incrementIP(newIP, IPincrement, subnetNetwork)
                     except:  
                         if os.path.isfile("/var/lock/subsys/kusu-addhost"):
                             os.unlink("/var/lock/subsys/kusu-addhost")

                         try:
                             snackinstance.finish()
                         except:
                             pass

                         print "ERROR:  IP Address overflow, please use a different subnetwork"
                         os._exit(-1)
                 else:
                     # Add the used IP to cache list
                     self._addUsedIP(newIP)
                     self._cachedDeviceIPs[nicdev] = newIP
                     break

             if installer:
                 # Installer mode - We *know* the specific network to boot from 
                 # vs prepopulating nodes which we don't.
                 # We're a DHCP/boot interface

                # If gateway is empty, use the newIP instead.
                if not ngGateway:
                    ngGateway = newIP

                if kusu.ipfun.onNetwork(installer_network, installer_subnet, ngGateway) and \
                        self.findMACAddress(macaddr) == False and nicdev != 'bmc':
                    # Mark the MAC as used.
                    self.addUsedMAC(macaddr)
                    self._createNICBootEntry(nodeID, networkID, True, newIP, macaddr)
                    self._writeDHCPLease(newIP, macaddr)
                else:
                    # Not a boot interface, just write out other info. 
                    if dhcpUnmanaged == False: 
                        # Dont create other boot entries when using unmanaged DHCP
                        self._createNICBootEntry(nodeID, networkID, False, newIP)
             else:
                 self._createNICBootEntry(nodeID, networkID, False, newIP)

    def replaceNodeEntry(self, nodename):
        """Replaces an existing node, first by deleting the existing 
        DHCP entry for the node since it contains the old mac address. 
        Then set the MAC address to NULL so a new DHCP request may be done."""

        nid = self.getNodeID(nodename)
        if not self._isMasterInstaller:
            # Delete the /tftpboot/kusu/pxelinux.cfg/macfile so node will pxe properly.
            self._dbRWrite.execute("SELECT mac FROM nics, nodes \
                    WHERE nics.nid=nodes.nid AND nodes.name='%s'" % nodename)
            macNodeInfo = self._dbRWrite.fetchall()
            for macaddr in macNodeInfo:
                if macaddr[0]:
                    macfile = "/tftpboot/kusu/pxelinux.cfg/01-%s" % macaddr[0].replace(':','-')
                    if os.path.isfile(macfile):
                        try:
                            os.unlink(macfile)
                        except:
                            pass

            self._deleteDHCPLease(nodename)
            self._dbRWrite.execute("UPDATE nics SET mac=NULL WHERE nid='%s'" % nid)
            self._dbRWrite.execute("UPDATE nodes SET state='Expired', bootfrom=False WHERE nid='%s'" % nid)
            return True
        else:
            print self.kusuApp._("replace_primary_installer_error\n")
            return False
   
    def addUnmanagedStaticDevice(self, devicename, ip):
        """Adds devices such as printers, switches, routers that have an IP
        or may use DHCP to set an IP."""

        # Check if the node name is a fully qualified name
        ret, msg = verifyFQDN(devicename)
        if not ret:
            msg = self.kusuApp._("addhost_options_invalid_hostname") % devicename
            return False, msg

        # Check if the node name exceeds the maximum length
        nameMaxLen = int(self._database.Nodes.c.name.type.length)
        if len(devicename) > nameMaxLen:
            msg = self.kusuApp._("addhost_options_hostname_too_long") % (devicename, nameMaxLen)
            return False, msg

        # Check if the node name is already used.
        if self.validateNode(devicename):
            msg = self.kusuApp._("addhost_options_hostname_inuse") % devicename
            return False, msg

        # Check if the IP is a valid IPv4 address
        ret, msg = verifyIP(ip)
        if not ret:
            msg = self.kusuApp._("addhost_options_invalid_ip") % ip
            return False, msg

        # Check if the IP is already used.
        if self.isIPUsed(ip):
            msg = self.kusuApp._("addhost_options_ip_inuse") % ip
            return False, msg

        # Check if the IP is preserved in alteregos(now only for BMC)
        if self.isPreservedBMCIP(ip):
            msg = self.kusuApp._("IP Address %s already preserved") % ip
            return False, msg

        # Check if the IP is in one private network.
        if not self.isIPInPrivateNet(ip):
            msg = self.kusuApp._("addhost_options_ip_not_on_network") % ip
            return False, msg

        self._dbReadonly.execute('SELECT ngid FROM nodegroups WHERE ngname="unmanaged"')
        ngid = self._dbReadonly.fetchone()[0]
 
        self._dbReadonly.execute('SELECT networks.netid FROM nodegroups,networks,ng_has_net \
                                  WHERE ng_has_net.netid=networks.netid AND \
                                      nodegroups.ngid=ng_has_net.ngid AND \
                                      ng_has_net.ngid=%s' % ngid) 
        netid = self._dbReadonly.fetchone()[0]

        self._dbRWrite.execute('INSERT INTO nodes (ngid, name, state, bootFrom) \
                VALUES ("%s", "%s", "Installed", "False")' % (ngid, devicename))
        if self._dbRWrite.driver == 'mysql':
            self._dbRWrite.execute("SELECT last_insert_id()")
        else: # xxx postgres for now
            self._dbRWrite.execute("SELECT last_value from nodes_nid_seq")
        nid = self._dbRWrite.fetchone()[0]
        self._dbRWrite.execute('INSERT INTO nics (netid, nid, ip, boot) \
                VALUES ("%s", "%s", "%s", "False")' % (netid, nid, ip))
        self._addUsedIP(ip)
        return True, "Success"

    def addUnmanagedDHCPDevice(self, interface, devicename, mac):
        self._nodeName = devicename
        self.setNodegroupByID(1)
        self._nodegroupInterfaces = self._findInterfaces()
        self._createNodeEntry(mac, interface, dhcpUnmanaged=True, installer=True, static=True)
           
    def replaceNICBootEntry(self, nodename, macaddress):
        """Replaces nics table containing new mac address for replaced node """
        nid = self.getNodeID(nodename)

        # The assumption is there is only one provision network!
        self._dbReadonly.execute("SELECT nics.mac FROM nics, networks "
                                 "WHERE nics.nid='%s' AND nics.netid=networks.netid AND "
                                 "networks.type='provision' AND lower(networks.device)!='bmc'" % nid)
        old_macaddress = self._dbReadonly.fetchone()[0]
        self._dbRWrite.execute("UPDATE alteregos SET mac='%s' WHERE mac='%s'" % (macaddress, old_macaddress))

        self._dbRWrite.execute("UPDATE nics SET mac='%s' WHERE nid='%s' AND boot = True" % (macaddress, nid))
        self._dbReadonly.execute("SELECT nics.ip FROM nics WHERE nics.nid=%s AND boot = True" % nid)
        data = self._dbReadonly.fetchone()[0]
        self._nodeName = nodename
        # call boothost to generate PXE file immediately before we accept new lease.
        os.system("/opt/kusu/sbin/kusu-boothost -m %s" % self._nodeName)

        # Recreate DHCP lease, this time using the new mac address found
        self._writeDHCPLease(data, macaddress)
            
    def _createNICBootEntry(self, nodeid, networkid, bootflag, ipaddress=None, macaddress=None):
        """Creates NIC entries for a specific node.
        If there's a mac address specified. Then that nic table entry 
        will have its bootdhcp flag enabled. Otherwise, other network
        interfaces cannot be PXE booted from. """
        if bootflag:# needed to coerce 0s and 1s to True or false
            bootflag = True
        else:
            bootflag = False

        if macaddress:
            self._dbRWrite.execute("INSERT INTO nics (nid, netid, mac, ip, boot) \
                    VALUES ('%s', '%s', '%s', '%s', %s)" %
                    (nodeid, networkid, macaddress, ipaddress, bootflag))
        else:
            if ipaddress:
                try:
                    self._dbRWrite.execute("INSERT INTO nics (nid, netid, ip, boot) \
                            VALUES ('%s', '%s', '%s', %s)" %
                            (nodeid, networkid, ipaddress, bootflag))
                except:
                    pass # There's no entry to write, maybe installer interface being added.
            else:
                self._dbRWrite.execute("INSERT INTO nics (nid, netid, boot) \
                        VALUES ('%s', '%s', %s)" % (nodeid, networkid, bootflag))

    def _writeDHCPLease(self, ipaddr, macaddr):
        if self._dbReadonly.getAppglobals('InstallerServeDHCP') == '0':
            return
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
        """Use DHCP's API to delete a DHCP entry in the 
        /var/lib/dhcpd/dhcpd.leases file """
        if self._dbReadonly.getAppglobals('InstallerServeDHCP') == '0':
            return
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
        return self._cachedMACAddress.has_key(macaddr)

        self._dbReadonly.execute("SELECT mac FROM nics WHERE mac='%s'" % macaddr)
        try:
            result = self._dbReadonly.fetchone()[0] 
            return True
        except:
            return False
    
    def validateInterface(self, interface, installer=True, nodegroup=None):
        """Checks if the requested interface exists in the database
        for the primary installer. If it does, returns True, otherwise False"""
        if nodegroup:
            # if the nodegroup's installtype is 'unmanaged', interface is always valid.
            self._dbReadonly.execute("SELECT installtype FROM nodegroups WHERE ngid='%s'" % nodegroup)
            if self._dbReadonly.fetchone()[0] == 'unmanaged':
                return True

        if installer: 
            query = "SELECT networks.device \
                     FROM networks, nics, nodes \
                     WHERE nodes.nid=nics.nid AND \
                        nics.netid=networks.netid AND \
                        networks.device='%s' AND \
                        nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller')" % \
                        interface
            self._dbReadonly.execute(query)
        else:
            self._dbReadonly.execute("SELECT networks.device \
                    FROM networks, ng_has_net \
                    WHERE networks.netid=ng_has_net.netid AND \
                        ng_has_net.ngid=%s AND networks.device='%s'" % (nodegroup, interface))

        result = self._dbReadonly.fetchone()
        try:
            testval = result[0]
            return True
        except:
            return False

    def validateNodegroup(self, nodegroup):
        """Checks if the requested nodegroup exists.
        If it does, returns True and the ngid, otherwise False"""

        # Check for valid nodegroup.
        self._dbReadonly.execute("SELECT ngid, ngname FROM nodegroups WHERE ngname = '%s'" % nodegroup)
        result = self._dbReadonly.fetchone()
        try:
            testval = result[0]
            return True, testval
        except:
            return False, None

    def validateNode(self, node):
        """Checks if the requested node exists or not.
        If it does, returns True, otherwise False"""
        return node in self._getReservedHostnames()

    def _getReservedHostnames(self):
        """Retrieve the host list returned by 'kusu-genconfig hosts'"""
        rsvNames = []
        file = "/etc/hosts.append"
        
        if os.path.isfile(file):
            fp = open(file,'r')
            lines = fp.readlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                hostRec = line.split()[1:] # ignore 1st element(IP)
                rsvNames.extend(hostRec)

            fp.close()

        nodesDict, nodes_in_str_format = getClusterHostNames(self._dbReadonly)

        for hosts in nodesDict.values():
            rsvNames.extend(hosts)

        return rsvNames

    def isIPInPrivateNet(self, unmanagedip, networks=None):
        """Checks if the requested ip is in one private network.
        If it is, returns True, otherwise False"""

        if not networks:
            query = "SELECT network, subnet FROM networks WHERE usingdhcp=False AND type<>'public'"
            self._dbReadonly.execute(query)
            networks = self._dbReadonly.fetchall() or []

        for net, mask in networks:
            if kusu.ipfun.onNetwork(net, mask, unmanagedip):
                return True

        return False

    def _findInterfaces(self):
        """Returns a dictionary containing Networks ID number, 
        Subnetwork, Starting IP Address and IP Increment value.
        The dictionary uses the device name as its key item[1]. """

        query = 'SELECT networks.netid, networks.device, networks.subnet, \
                     networks.startip, networks.inc, networks.gateway \
                 FROM networks,ng_has_net \
                 WHERE ng_has_net.netid=networks.netid AND \
                     ng_has_net.ngid = "%s"' % self._nodeGroupType
        self._dbReadonly.execute(query)
        data = self._dbReadonly.fetchall()

        interfaceInfo = {}
        for item in data:
            interfaceInfo[item[1]] = {'netid': {}, 'networks': {}, 'subnet': {},
                                      'startip': {}, 'incr': {}, 'gateway': {}}
            interfaceInfo[item[1]]['netid'] = item[0]
            interfaceInfo[item[1]]['subnet'] = item[2]
            interfaceInfo[item[1]]['startip'] = item[3]
            interfaceInfo[item[1]]['incr'] = item[4]
            interfaceInfo[item[1]]['gateway'] = item[5]

        return interfaceInfo

    def findBootDevice(self, nodename):
        """Returns the boot device that has its boot flag set to 1 """
        query = "SELECT networks.network, networks.subnet, networks.device, networks.gateway \
                 FROM networks, nics, nodes \
                 WHERE nodes.nid=nics.nid AND nics.netid=networks.netid \
                     AND nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller') \
                     AND NOT lower(networks.device)='bmc' ORDER BY device"

        self._dbReadonly.execute(query)
        installerInfo = self._dbReadonly.fetchall()

        # Get list of node available gateway
        query = 'SELECT distinct networks.device, nics.ip \
                 FROM networks,nics,nodes \
                 WHERE networks.netid = nics.netid AND \
                     nodes.nid=nics.nid AND nics.boot = True AND \
                     nodes.name = "%s"' % nodename

        self._dbReadonly.execute(query)
        nodeInfo = [(device,ip) for (device,ip) in self._dbReadonly.fetchall() if ip]

        try:
            nodeIP = nodeInfo[0][1]
        except IndexError:
            return None
        nodeDevice = nodeInfo[0][0]

        for installer_network, installer_subnet, installer_device, installer_gateway in installerInfo:
            if kusu.ipfun.onNetwork(installer_network, installer_subnet, nodeIP):
                return nodeDevice

        return None

    def retrieveIPFromAlteregos(self, mac, ngid):
        # search for a previous IP for the mac address and ngid in alteregos table
        query = "select ip from alteregos where mac='%s' and ngid=%i" % (mac, ngid )
        try:
            self._dbReadonly.execute(query)
            return self._dbReadonly.fetchone()[0]
        except:
            pass
        return None

    def findOldIPForNode(self, mac, ngid):
        '''returns the IP address to use, or None'''
        result = None
        ipaddr = None

        # Test first to see if this node has been in this nodegroup before.
        # If so try to reuse the IP.

        ipaddr = self.retrieveIPFromAlteregos(mac, ngid)
        if ipaddr:
            return ipaddr
        else:
            query = "SELECT distinct nodegroups.ngid \
                     FROM alteregos, nodegroups, ng_has_net, networks \
                     WHERE nodegroups.ngid=ng_has_net.ngid AND \
                         ng_has_net.netid=networks.netid AND \
                         networks.type='provision' AND \
                         alteregos.ngid=nodegroups.ngid AND \
                         nodegroups.ngid!=%i AND \
                         networks.netid IN (SELECT netid from ng_has_net WHERE ngid=%i )" % (ngid, ngid)
            try:
                self._dbReadonly.execute(query)
                result = self._dbReadonly.fetchone()[0]
            except:
                pass

            if result:
                ipaddr = self.retrieveIPFromAlteregos(mac, result)

        return ipaddr

    def retrieveBMCIPFromAlteregos(self, mac, ngid):
        # search for a previous BMC IP for the mac address and ngid in alteregos table
        query = "select bmcip from alteregos where mac='%s' and ngid=%i" % (mac, ngid)
        ipaddr = None
        try:
            self._dbReadonly.execute(query)
            ipaddr = self._dbReadonly.fetchone()[0]
        except:
            pass
        return ipaddr

    def findOldBMCIPForNode(self, mac, ngid):
        '''Returns the BMC IP address to use, or None'''
        ipaddr = None

        # Test first to see if this node has been in this nodegroup before
        # If so try to reuse the IP.
        ipaddr = self.retrieveBMCIPFromAlteregos(mac, ngid)

        if ipaddr and self.validBMCIPForNode(ipaddr, mac):
            return ipaddr

        for ipaddr, macaddr in self._preservedBMCIP.items():
            if macaddr == mac and self.validBMCIPForNode(ipaddr, macaddr):
                return ipaddr

        return None

    def retrieveHostnameFromAlteregos(self, mac, ngid):
        #search for a previous hostname that has been used for
        #the mac address and ngid in alteregos table

        query = "select name from alteregos where mac='%s' and ngid=%i" % (mac, ngid )
        try:
            self._dbReadonly.execute(query)
            return self._dbReadonly.fetchone()[0]
        except:
            pass
        return None

    def findOldHostnameForNode(self, mac, ngid):
        '''Returns the hostname to use, or None'''

        result = None
        hname = self.retrieveHostnameFromAlteregos(mac, ngid)

        if hname:
            return hname
        else:
            query = "SELECT distinct nodegroups.ngid \
                     FROM alteregos, nodegroups \
                     WHERE alteregos.ngid=nodegroups.ngid \
                         AND nodegroups.ngid!=%i \
                         AND nodegroups.nameformat IN \
                             (SELECT nameformat from nodegroups WHERE ngid=%i)" % (ngid, ngid)
            try:
                self._dbReadonly.execute(query)
                result = self._dbReadonly.fetchone()[0]
            except:
                pass

            if result:
                hname = self.retrieveHostnameFromAlteregos(mac, result)
        return hname

    def setNodegroupByName(self, nodegroupname):
        # Convert the name into a nodegroup id
        query = "SELECT ngid FROM nodegroups WHERE ngname='%s'" % nodegroupname
        try:
            self._dbReadonly.execute(query)
            self._nodeGroupType = self._dbReadonly.fetchone()[0]
        except:
            self._nodeGroupType = None

    def setNodegroupByID(self, ngid):
        self._nodeGroupType = ngid
        if self._nodeFormat == None:
            self.getNodeFormat()
            self._ngConflicts = self._getNodegroupConflicts()
            self._nodegroupInterfaces = self._findInterfaces()
     
    def getNodegroupNameByID(self, ngid):
        query = "SELECT ngname FROM nodegroups WHERE ngid=%s" % ngid
        try:
            self._dbReadonly.execute(query)
            return self._dbReadonly.fetchone()[0]
        except:
            return None

    def moveNodegroups(self, groupList, destGroup):
         dupeList = []
         nodeList = []
         
         self.setNodegroupByName(destGroup)
         # Check for valid nodegroup.
         if not self._nodeGroupType:
             return None, None, None
         
         # Check if the group being moved is not the destination nodegroup.
         # Delete from the list if it is.
         if destGroup in groupList:
             dupeList.append(destGroup)
      
         for dupegroup in dupeList:
             groupList.remove(dupegroup)
    
         # Get a list of nodes for all the nodegroups.
         for group in groupList:
             self._dbReadonly.execute("SELECT nodes.name FROM nodes, nodegroups \
                     WHERE nodes.ngid=nodegroups.ngid AND nodegroups.ngname='%s'" % group)
             nodes = self._dbReadonly.fetchall()
             for node in nodes:
                 nodeList.append(node[0])
        
         return self.moveNodes(nodeList, destGroup)

    def moveNodes(self, requestedNodes, nodegroupname,rack=0):
        dataList = {}
        bmcList = {}
        macList = {}
        badList = []
        ipList = []
        dupeList = []
        interfaceName = ""
        self.setNodegroupByName(nodegroupname)
        nodeList = set(self._getAllNodes())

        # Check which nodes are valid.
        for requestNode in requestedNodes:
            if requestNode in nodeList:
                continue
            else:
                badList.append((requestNode, 'Node does not exist'))

        for node in badList:
            requestedNodes.remove(node[0])

        # Check for valid nodegroup.
        if not self._nodeGroupType:
            return None, None, None

        # Remove the primary installer if the user tries to move it to another node group.
        primaryInstaller = self._getPrimaryInstaller()
        if primaryInstaller in nodeList:
            nodeList.remove(primaryInstaller)
            badList.remove(primaryInstaller)

        if primaryInstaller in badList:
            badList.remove(primaryInstaller)

        # Check if the item being moved already exists in the same node group.
        # Delete from list if it is.
        for node in requestedNodes: 
            self._dbReadonly.execute("SELECT COUNT(nodes.name) FROM nodes \
                    WHERE nodes.name='%s' AND nodes.ngid=%s" % (node, self._nodeGroupType))
            data = bool(self._dbReadonly.fetchone()[0])
            if data:
                dupeList.append(node)

        if dupeList:
            for dupenode in dupeList:
                requestedNodes.remove(dupenode)

        self._dbReadonly.execute("SELECT networks.device \
                FROM networks, ng_has_net \
                WHERE ng_has_net.netid = networks.netid \
                    AND ng_has_net.ngid = %s" % self._nodeGroupType)
        provision_networkdev = [x[0] for x in self._dbReadonly.fetchall()]
        for node in requestedNodes:
            self._dbReadonly.execute("SELECT nics.mac, nics.ip, networks.device \
                    FROM nics,nodes,networks,nodegroups \
                    WHERE nodes.name='%s' AND nodes.nid=nics.nid AND \
                        networks.netid=nics.netid AND nics.boot=True AND \
                        nodegroups.ngid=nodes.ngid" % node) 
            data = self._dbReadonly.fetchone()
            if data:
                # Make sure MAC address is not empty
                if not data[0]:
                    badList.append((node, 'No valid MAC address'))
                elif data[2] not in provision_networkdev:
                    badList.append((node, 'No network device available for provision (Available:%s Required:%s' % (data[2], provision_networkdev)))
                else:
                    dataList["%s" % node] = "%s %s %s" % (data[0], data[1], data[2])
                    macList["%s" % node] = "%s" % data[0]
            else:
                badList.append((node, 'No network device available for provision (Required:%s)' % (provision_networkdev)))

        for node in badList:
            if node[0] in requestedNodes:
                requestedNodes.remove(node[0])

        self._dbReadonly.execute("SELECT installtype FROM nodegroups WHERE ngname='%s'" % nodegroupname)
        ng_installtype = self._dbReadonly.fetchone()[0]

        #Need to validate BMC network for multiboot nodegroup
        if ng_installtype == 'multiboot':
            for node in requestedNodes:
                self._dbReadonly.execute("SELECT nics.ip, networks.device FROM nics,nodes,networks "
                                         "WHERE nodes.name='%s' AND nodes.nid=nics.nid "
                                         "AND networks.netid=nics.netid "
                                         "AND lower(networks.device)='bmc'" % node)
                data = self._dbReadonly.fetchone()
                if data:
                    bmcList["%s" % node] = "%s" % data[0]
            if 'bmc' not in [x.lower() for x in provision_networkdev]:
                for node in bmcList.keys():
                    badList.append((node, 'No BMC network available in target nodegroup'))
                    requestedNodes.remove(node)

        # Get the new nodegroups network and device table list
        self._dbReadonly.execute("SELECT networks.device, networks.subnet, networks.network \
                FROM networks, ng_has_net \
                WHERE ng_has_net.netid=networks.netid AND \
                    (networks.type='provision' OR lower(networks.device)='bmc') AND \
                    ng_has_net.ngid = %s" % self._nodeGroupType)
        newngdata = list(self._dbReadonly.fetchall())
        if newngdata == []:
            return [], ipList, macList, requestedNodes, None

        # Check if the existing nodegroup device matches the new 
        # nodegroup device that is bootable. Otherwise, indicate an error.
        # The user will have to resolve this by running addhost.
        for node in requestedNodes:
            badflag = 1
            nodeData = dataList[node].split()
            #if move to multiboot nodegroup, need to check bmc network
            if node in bmcList and ng_installtype=='multiboot':
                for netinfo in newngdata:
                    device, network, subnet = netinfo
                    if device.lower() != 'bmc':
                        continue
                    if kusu.ipfun.onNetwork(network, subnet, bmcList[node]):
                        badflag = 0
                        break
                if badflag:
                    badList.append((node, 'Existing BMC IP on different network'))
                    continue

            badflag = 1
            for netinfo in newngdata:
                device, network, subnet = netinfo
                interfaceName = device

                # Check if the existing IP fits on the new nodegroup network.
                # Also check if the device matches, otherwise warn user later.
                if (device.lower() != 'bmc' and 
                        kusu.ipfun.onNetwork(network, subnet, nodeData[1])) or \
                        ng_installtype=='unmanaged':
                    badflag = 0
                    ipList.append(nodeData[1])
                    break

            if badflag:
                badList.append((node,'Existing IP on different network'))

        if badList:
            for badnode in badList:
                if badnode[0] in nodeList:
                    nodeList.remove(badnode[0])
                    if badnode[0] in requestedNodes:
                        requestedNodes.remove(badnode[0])

        return requestedNodes, ipList, macList, badList, interfaceName

# For ngedit

def validateNodeFormat(nodestr):
    """Returns true if the string format is valid, false if not."""
    digit_flag = 0
    special = 0
    mini_rank = 0
    rack_found = 0
    alphanum = 0

    if nodestr.find(' ') > 0:
        return False
  
    for i in range(0, len(nodestr)):

        if nodestr[i].isdigit():
            digit_flag = 1
            continue

        if digit_flag and nodestr[i] == "#":
            if nodestr[i-1].isdigit():
                return False

        if nodestr[i] == '#':
            if special == 1:
                return False
            special = 1
            continue

        if special:
            if nodestr[i] == 'R':
                rack_found = 1
                continue

        if special:
            if nodestr[i] == 'N':
                mini_rank = 1
                continue

        if special:
            if nodestr[i].isdigit():
                return False

        special = 0
        alphanum = 1

    if not mini_rank:
        return False

    if not alphanum:
        return False

    return True

def seq2tplstr(seq):
    '''convert a sequence to a tuple string representation without a trailing comma'''
    if not seq:
        return None
    try:
        if len(seq) == 1:
            tplstr = '(\'%s\')' % str(seq[0])
        else:
            tplstr = str(tuple(seq))
        return tplstr
    except:
        return None

# Run some unittests
if __name__ == "__amain__":
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
    
    if myNodeFun.findMACAddress("50:11:ff:33:44:41"):
        print "* Testing NodeFun.findMACAddress(\"00:11:22:33:44:56\"): Result: PASS (Found)"
    else:
        print "* Testing NodeFun.findMACAddress(\"00:11:22:33:44:56\"): Result: FAIL (Not found)"
        
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

    # Valid case, create node in 'Compute Diskless'
    myNodeFun = NodeFun(rack=2, nodegroup=4)
    if myNodeFun.addNode("aa:bb:cc:dd:ee:ab", "eth1"):
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth1\"): Given: Rack 2, ngid 4 (Compute Diskless): Result: PASS (Node created)"
        print "\t* NodeFun.addNode(): Returns: %s" % createdNode
        if createdNode == "c02-01":
            print "\t* Testing NodeFun.addNode() PASSED. Correct node added."
    else:
        print "* Testing NodeFun.addNode(\"aa:bb:cc:dd:ee:ff\", \"eth1\"): Given: Rack 2, ngid 4 (Compute Diskless): Result: FAIL (Node not created)"


    # Test moving nodes
    flag = 0
    myNodeFun = NodeFun()
    movenodes = ["c01-00", "node0000", "foobarFAKE0342-34", "installer00", "host000"]

    moveList, macList, badList = myNodeFun.moveNodes(movenodes, "Foobar")
    if (moveList, macList, badList == None):
       print "* Testing NodeFun.moveNodes(\"[c01-00, node0000, foobarFAKE0342-34, installer00, host000]\", \"Foobar\"): Result: PASS (Invalid Nodegroup, not moving)"
       print "\t* Testing NodeFun.moveNodes: Returns: %s" % moveList
    else:
       print "* Testing NodeFun.moveNodes(\"[c01-00, node0000, foobarFAKE0342-34, installler00, host000]\", \"Foobar\"): Result: FAIL (Invalid Nodegroup, Moving!)"
       print "\t* Testing NodeFun.moveNodes: Returns: %s" % moveList

    myNodeFun = NodeFun()
    movenodes = ["node0000", "node0003", "installer02", "host003", "host004", "installer00", "c01-01"]
   
    moveList, macList, badList, interface = myNodeFun.moveNodes(movenodes, "Installer")
    if (moveList, macList, badList):
        print "* Testing NodeFun.moveNodes(\"[node0000, node0003, installer00, installer02, c01-01]\", \"Installer\"): Result: PASS (Valid Nodegroup, Moving nodes to Installer)"
        print "\t* Testing NodeFun.moveNodes: Returns: %s" % moveList
      
        # Create Temp file
        (fd, tmpfile) = tempfile.mkstemp()
        tmpname = os.fdopen(fd, 'w')
        for node in moveList:
            tmpname.write("%s\n" % macList[node])
        tmpname.close()

        # Call addhosts to delete these nodes
        print "COMMAND: /opt/kusu/sbin/kusu-addhost --remove %s" % string.join(moveList, ' ')
        os.system("/opt/kusu/sbin/kusu-addhost --remove %s" % string.join(moveList, ' '))

        # Add these back using mac file
        print "COMMAND: /opt/kusu/sbin/kusu-addhost --file='%s' --interface=%s --nodegroup='%s'" % (tmpfile, interface, "Installer") # Installer ngid
        os.system("/opt/kusu/sbin/kusu-addhost --file=%s --interface=%s --nodegroup='%s'" % (tmpfile, interface, myNodeFun.getNodegroupNameByID(1)))
     
        # Remove temp file
        os.remove(tmpfile)

        # Now check if the nodes created really exist as installer03, and installer04.
        if myNodeFun.validateNode("installer03"):
            print "* Testing NodeFun.validateNode(\"installer03\"): Result: PASS (Found)"
            flag = 1
        else:
            print "* Testing NodeFun.validateNode(\"installer03\"): Result: FAIL (Not found)"
            flag = 0

        if myNodeFun.validateNode("installer04"):
            print "* Testing NodeFun.validateNode(\"installer04\"): Result: PASS (Found)"
            flag = 1
        else:
            print "* Testing NodeFun.validateNode(\"installer04\"): Result: FAIL (Not found)"
            flag = 0

        if flag:
            print "\t* Overall myNodeFun.moveNodes(): PASSED!"
        else:
            print "\t* Overall MyNodeFun.moveNodes(): FAILED!"
    else:
        print "* Testing NodeFun.moveNodes(\"[node0000, node0003, installer00, installer02, c01-01]\"): Result: FAIL (Valid Nodegroup, NOT Moving nodes to Installer)"
 
    # Now move them back to their original place.
    myNodeFun = NodeFun()
    movenodes = ["installer03", "installer04"]
  
    moveList, macList, badList, interface = myNodeFun.moveNodes(movenodes, "Compute")
    if (moveList, macList, badList):
        print "* Testing NodeFun.moveNodes(\"[installer03, installer04]\", \"Compute\"): Result: PASS (Valid Nodegroup, Moving nodes to Compute)"
        print "\t* Testing NodeFun.moveNodes: Returns: %s" % moveList

        # Create Temp file
        (fd, tmpfile) = tempfile.mkstemp()
        tmpname = os.fdopen(fd, 'w')
        for node in moveList:
           tmpname.write("%s\n" % macList[node])
        tmpname.close()

        # Call addhosts to delete these nodes
        print "COMMAND: /opt/kusu/sbin/kusu-addhost --remove %s" % string.join(moveList, ' ')
        os.system("/opt/kusu/sbin/kusu-addhost --remove %s" % string.join(moveList, ' '))

        # Add these back using mac file
        print "COMMAND: /opt/kusu/sbin/kusu-addhost --file='%s' --interface=%s --nodegroup='%s'" % (tmpfile, interface, "Compute") # Installer ngid
        os.system("/opt/kusu/sbin/kusu-addhost --file=%s --interface=%s --nodegroup='%s'" % (tmpfile, interface, myNodeFun.getNodegroupNameByID(2)))
    
        # Remove temp file
        os.remove(tmpfile)

        # Now check if the nodes created really exist as installer03, and installer04.
        if myNodeFun.validateNode("node0000"):
            print "* Testing NodeFun.validateNode(\"node0000\"): Result: PASS (Found)"
            flag = 1
        else:
            print "* Testing NodeFun.validateNode(\"node0000\"): Result: FAIL (Not found)"
            flag = 0

        if myNodeFun.validateNode("node0003"):
            print "* Testing NodeFun.validateNode(\"node0003\"): Result: PASS (Found)"
            flag = 1
        else:
            print "* Testing NodeFun.validateNode(\"node0003\"): Result: FAIL (Not found)"
            flag = 0

        if flag:
            print "\t* Overall myNodeFun.moveNodes(): PASSED!"
        else:
            print "\t* Overall MyNodeFun.moveNodes(): FAILED!"
    else:
        print "* Testing NodeFun.moveNodes(\"[installer03, installer04]\"): Result: FAIL (Valid Nodegroup, NOT Moving nodes to Installer)"

if __name__ == "__amain__":
    #myNodeFun = NodeFun()

    #movegroups = ["Compute", "Compute Disked", "Compute Diskless"]
    #moveList, macList, badList, interface = myNodeFun.moveNodegroups(movegroups, "Installer")
    #if (moveList, macList, badList):
    #    print "\t* Testing NodeFun.moveNodegroups: Returns: %s" % moveList
    #    print "\t* badList = %s" % badList
    #    print "Interface = %s" % interface

    # Now move them back to their original place.
    myNodeFun = NodeFun()
    myNodeFun.setRackNumber(9)
    movenodes = ["host000","installer-09-05", "garbage"]

    #moveList, ipList, macList, badList, interface = myNodeFun.moveNodes(movenodes, "installer-rhel-5-x86_64")
    moveList, ipList, macList, badList, interface = myNodeFun.moveNodes(movenodes, "compute-rhel-5-x86_64")
    if (moveList, macList, badList):
        print "* Testing NodeFun.moveNodes(\"[compute-00-00]\", \"Compute\"): Result: PASS (Valid Nodegroup, Moving nodes to installer-rhel-5-x86_64)"
        print "\t* Testing NodeFun.moveNodes: Returns: %s" % moveList

        # Create Temp file
        (fd, tmpfile) = tempfile.mkstemp()
        tmpname = os.fdopen(fd, 'w')
        for node in moveList:
           tmpname.write("%s\n" % macList[node])
        tmpname.close()

        # Call addhosts to delete these nodes
        print "COMMAND: /opt/kusu/sbin/kusu-addhost --remove %s" % string.join(moveList, ' ')
        print moveList, ipList, macList, badList, interface
        #os.system("/opt/kusu/sbin/kusu-addhost --remove %s" % string.join(moveList, ' '))

        # Add these back using mac file
        print "COMMAND: /opt/kusu/sbin/kusu-addhost --file='%s' --interface=%s --nodegroup='%s'" % (tmpfile, interface, "installer-rhel-5-x86_64") # Installer ngid
        #os.system("/opt/kusu/sbin/kusu-addhost --file=%s --interface=%s --nodegroup='%s'" % (tmpfile, interface, myNodeFun.getNodegroupNameByName("installer-rhel-5-x86_64")))

if __name__ == "__main__":

   if validateNodeFormat("1234#R#N-ABCDEF") == False:
       print "PASS: Format is INVALID (number next to special charactor)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("compute-#R-#N"):
       print "PASS: Format is VALID (Valid format)"
   else:
       print "FAIL: Evaluated format is INVALID"

   if validateNodeFormat("compute-room-3452-#R") == False:
       print "PASS: Format is INVALID (Missing Rank, has only rack)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("1#N") == False:
       print "PASS: Format is INVALID (Number next to rank)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("1#R") == False:
       print "PASS: Format is INVALID (Number next to rack)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("#N#N#N#R") == False:
       print "PASS: Format is INVALID (Special charactor next to another special charactor)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("1-2-#N-#N-#N") == True:
       print "PASS: Format is VALID (Rank number minimally specified)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("compute-room-3452-#R") == False:
       print "PASS: Format is INVALID (Missing rank number only rack specified)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("hello world") == False:
       print "PASS: Format is INVALID (Whitespace in hostname format)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("hello-#R0") == False:
       print "PASS: Format is INVALID (Number after special charactor)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("#R") == False:
       print "PASS: Format is INVALID (No other charactors other than special charactor)"
   else:
       print "FAIL: Evaluated format is VALID"

   if validateNodeFormat("hello") == False:
       print "PASS: Format is INVALID (Minimal rank not specified)"
   else:
       print "FAIL: Evaluated format is VALID"


