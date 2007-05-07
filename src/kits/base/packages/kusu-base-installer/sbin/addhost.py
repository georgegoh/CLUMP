#!/usr/bin/python
#
# Kusu add host
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
import sys
import string
import gettext
import time
import popen2
from kusuapp import KusuApp
from kusudb import KusuDB
import snack
import screens.screenfactory
import screens.navigator
import screens.kusuwidgets
import ipfun

NAV_NOTHING = -1
NAV_FORWARD = 0
NAV_BACK = 1
NAV_QUIT = 2

NOCANCEL    = 0
ALLOWCANCEL = 1

class NodeData:
    def __init__(self):
        # Public 
        self.nodeRackNumber = 0
        self.nodeGroupSelected = 0
        self.nodesInstalled = []
        self.selectedInterface = None
        self.syslogFilePosition = None
        self.optionReplaceMode = False
        self.pluginLocation = "/opt/kusu/lib/plugins/addhost"
        self.optionReplaceMode = False
        self.addHostPlugins = []
        # We don't want to prompt the user to quit if we reached the last screen.
        self.quitPrompt = True

# Global Instance of data
global myNodeInfo
myNodeInfo = NodeData()

class AddHostApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)
        self.dbconnection = KusuDB()
        self.kusuApp = KusuApp()

    def toolVersion(self, option, opt, value, parser):
        """ 
        toolVersion()
        Prints out the version of the tool to screen. 
        """
        
        i18nPrint("Addhosts Version %s\n\n", self.version)
        sys.exit(0)
        
    def parseargs(self):
        """
        parseargs()
        Parse the command line arguments.
        """

        self.parser.add_option("-v", "--version", action="callback",
                                callback=self.toolVersion, help=self.kusuApp._("addhost_version_usage"))
        self.parser.add_option("-n", "--nodegroup", action="store",
                                type="string", dest="nodegroup", help=self.kusuApp._("addhost_nodegroup_usage"))
        self.parser.add_option("-i", "--interface", action="store",
                                type="string", dest="interface", help=self.kusuApp._("addhost_interface_usage"))
        self.parser.add_option("-f", "--file", action="store",
                                type="string", dest="macfile", help=self.kusuApp._("addhost_macfile_usage"))
        self.parser.add_option("-e", "--remove", action="callback",
                                dest="remove", callback=self.varargs, help=self.kusuApp._("addhost_remove_usage"))
        self.parser.add_option("-p", "--replace", action="store",
                                type="string", dest="replace", help=self.kusuApp._("addhost_replace_usage"))
        self.parser.add_option("-r", "--rack", action="store",
                                type="int", dest="rack", help=self.kusuApp._("addhost_rack_usage"))
        self.parser.add_option("-u", "--update", action="store_true", dest="update", help=self.kusuApp._("addhost_update_usage"))
    
        (self.options, self.args) = self.parser.parse_args(sys.argv[1:])

    def loadPlugins(self):
        """ loadPlugins()
        Loads all plugins for Add hosts.
        """
        
        pluginList = []
        moduleInstance = None
        if not os.path.exists(myNodeInfo.pluginLocation):
            # No plugins found the tool should still work even without any plugins.
            return
        else:
            sys.path.append(myNodeInfo.pluginLocation)
        
        pluginFileList = os.listdir(myNodeInfo.pluginLocation)
        pluginFileList.sort()
        
        # Strip out files in the plugins directory with .pyc or have a __init__py file (for packages) or ignore .swp files from vi :-)
        for pluginName in pluginFileList:
             plugin, ext = os.path.splitext(pluginName)
             if ext != ".pyc" and not plugin == "__init__" and not plugin[0] == '.':
                pluginList.append(plugin)
                
        # Import the plugins
        moduleInstances = map(__import__, pluginList)
        
        # Create instances of each new plugin and store the instances.
        for thisModule in moduleInstances:
             try:
                  thisPlugin = thisModule.AddHostPlugin()
                  myNodeInfo.addHostPlugins.append(thisPlugin)
             except:
                  print "Warning: Invalid plugin '%s'. Does not have a AddHostPlugin class.\nThis plugin will be IGNORED." % thisModule
    
    def nxor(self, *args):
        """nxor(varargs args)
        N-way function, only one condition may be true otherwise false.
        """
        
        return len([x for x in args if x]) == 1
        
    def run(self):
        """run()
        Run the application
        """
        
        screenList = []

        haveInterface = False
        haveNodegroup = False
        replaceMode = False

        # Parse command options
        self.parseargs()
        
        # Load addhost plugins
        self.loadPlugins()
        
        # Lists are special in Python, handle boolean differently.
        if self.options.remove == []:
            removeFlag = True
        else:
            removeFlag = bool(self.options.remove)
           
        # Don't allow option -n -p -e -u to be used together. Mututually Exclusive.
        if (not self.nxor(bool(self.options.nodegroup), bool(self.options.replace), bool(self.options.update), removeFlag)):
                    if (bool(self.options.nodegroup) == False and bool(self.options.replace) == False and bool(self.options.update) == False and removeFlag == False):
                        pass
                    else:
                        self.parser.error(self.kusuApp._("addhost_options_exclusive"))

        # Handle -r option
        if self.options.rack:
            myNodeInfo.nodeRackNumber = self.options.rack

        # Handle -i option
        if self.options.interface:
            if self.options.interface[0] == '-':
                self.parser.error(self.kusuApp._("addhost_options_interface_required"))
            else:
                checkDBConnection(self.kusuApp._("DB_Query_Error\n"), self.dbconnection)

                try:
                    self.dbconnection.execute("SELECT networks.device FROM networks, nics, nodes WHERE nodes.nid=nics.nid \
                                               AND nics.netid=networks.netid AND networks.device='%s' AND \
                                               nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller')" % self.options.interface)
                    result = self.dbconnection.fetchone()
                except:
                    i18nPrint(self.kusuApp._("DB_Query_Error\n"))
                    sys.exit(-1)

                try:
                    myNodeInfo.selectedInterface = result[0]
                    haveInterface = True
                except:
                    i18nPrint (self.kusuApp._("addhost_options_invalid_interface\n\n"))
                    sys.exit(-1)

        # Handle -n option
        if self.options.nodegroup:
            if self.options.nodegroup[0] == '-':
                self.parser.error(self.kusuApp._("addhost_options_nodegroup_required"))
            else:
                checkDBConnection(self.kusuApp._("DB_Query_Error\n"), self.dbconnection)

                # Check for valid nodegroup. if not return an error.
                try:
                    self.dbconnection.execute("SELECT ngid, ngname FROM nodegroups WHERE ngname = '%s'" % self.options.nodegroup)
                    result = self.dbconnection.fetchone()
                except:
                    i18nPrint(self.kusuApp._("DB_Query_Error\n"))
                    sys.exit(-1)

                try:
                    myNodeInfo.nodeGroupSelected = result[0]
                except:
                    i18nPrint(self.kusuApp._("addhost_options_invalid_nodegroup\n"))
                    sys.exit(-1)

                haveNodegroup = True
                
        # Handle -f -i -n options
        if (self.options.macfile and self.options.interface and self.options.nodegroup):
            
            # Check if the file specified exists.
            if not os.path.isfile(self.options.macfile):
                i18nPrint(self.kusuApp._("addhost_options_file_notfound\n"))
                sys.exit(-1)
                
            if haveNodegroup and not self.options.rack:
                checkHost = NodeInfo(rack=myNodeInfo.nodeRackNumber, nodegroup=myNodeInfo.nodeGroupSelected)
                checkHost.getNodeFormat()
                flag = 1
                if checkHost.isNodenameHasRack() and haveInterface:
                  while flag:
                      response = raw_input(self.kusuApp._("addhost_textprompt_rack"))
                      try:
                          result = int(response)
                          if result < 0:
                             print "Error: Cannot specify a negative number. Please try again"
                             flag = 1
                          else:
                             myNodeInfo.nodeRackNumber = result
                             #print "Setting Rack number to: %s" % myNodeInfo.nodeRackNumber
                             flag = 0
                      except:
                          print self.kusuApp._("Error: The value %s is not a number. Please try again" % response)
                          flag = 1
              
            # Read in list of mac addresses
            macfileList = open(self.options.macfile,'r').readlines()
            self.prepopulateNodes = NodeInfo(myNodeInfo.addHostPlugins, myNodeInfo.nodeRackNumber, myNodeInfo.nodeGroupSelected)
            for macaddr in macfileList:
                 macaddr = macaddr.lower().strip()
                 checkMacAddr = self.prepopulateNodes.findMACAddress(macaddr)
                 if checkMacAddr == False:
                     nodeName = self.prepopulateNodes.addNode(macaddr)
                     print "Adding Node: %s, %s" % (nodeName, macaddr)
                     # Ask all plugins to call added() function
                     myNode.plugins_add(nodeName)
                     myNodeInfo.nodesInstalled.append([nodeName, macaddr])
                 #else:
                     #print "Duplicate: %s, Ignoring" % macaddr
            sys.exit(0)
              
        if self.options.macfile:
            if not self.options.interface or not self.options.nodegroup:
               self.parser.error(self.kusuApp._("addhost_options_macfile_options_needed"))

        # Handle -p option
        if self.options.replace:
            if self.options.replace.strip().isdigit():
                self.parser.error(self.kusuApp._("addhost_options_invalid_node"))
            else:
                if self.options.replace[0] == '-':
                    self.parser.error(self.kusuApp._("addhost_options_replace_required"))
                else:
                    checkDBConnection(self.kusuApp._("DB_Query_Error\n"), self.dbconnection)

                    # Check for valid node to replace. if not return an error.
                try:
                    self.dbconnection.execute("SELECT nodes.name FROM nodes WHERE nodes.name = '%s'" % self.options.replace)
                    result = self.dbconnection.fetchone()
                except:
                    i18nPrint(self.kusuApp._("DB_Query_Error\n"))
                    sys.exit(-1)

                try:
                    checkvalNode = result[0]
                except:
                    i18nPrint(self.kusuApp._("The node %s is not found. Please try again\n" % self.options.replace))
                    sys.exit(-1)

                replaceMode = True
                myNodeInfo.optionReplaceMode = True
                myNodeInfo.replaceNodeName = self.options.replace
                if myNode.replaceNodeEntry(self.options.replace) == False:
                    sys.exit(-1)

        # Handle -e option
        if self.options.remove:
            for delnode in self.options.remove:
                 if delnode.strip().isdigit():
                     self.parser.error(self.kusuApp._("addhost_options_invalid_node"))
                 # Disallow options next to options.
                 if delnode[0] == '-':
                     self.parser.error(addhost_options_invalid_node)

                 # Ask all plugins to call removed() function
                 myNode.plugins_removed(delnode)

                 # Handle removing node from db.
                 myNode.deleteNode(delnode)                 
                 myNode.plugins_finished()
                
            sys.exit(-1)

        elif self.options.remove == []:
              self.parser.error(self.kusuApp._("addhost_options_invalid_node"))

        # Handle -u option
        if self.options.update:
            # Handle any local pending updates.
            myNode.doUpdates()

            # Ask all plugins to call updated() function
            myNode.plugins_updated()
            myNode.plugins_finished()
            sys.exit(-1)
    
        # If node group format has a Rack AND Rank, prompt for the rack number.
        if haveNodegroup and not self.options.rack and not self.options.macfile:
            checkHost = NodeInfo(rack=myNodeInfo.nodeRackNumber, nodegroup=myNodeInfo.nodeGroupSelected)
            checkHost.getNodeFormat()
            flag = 1
            if checkHost.isNodenameHasRack() and haveInterface:
                while flag:
                   response = raw_input(self.kusuApp._("addhost_textprompt_rack"))
                   try:
                       result = int(response)
                       if result < 0:
                          print "Error: Cannot specify a negative number. Please try again"
                          flag = 1
                       else:
                          myNodeInfo.nodeRackNumber = result
                          print "Setting Rack number to: %s" % myNodeInfo.nodeRackNumber
                          flag = 0
                   except:
                       print self.kusuApp._("Error: The value %s is not a number. Please try again" % response)
                       flag = 1

        # If nodegroup format and rack specified but node format does not have a rack AND rank. Ignore user set rack and use 0.
        if (haveNodegroup and self.options.rack):
            checkHost = NodeInfo(rack=myNodeInfo.nodeRackNumber, nodegroup=myNodeInfo.nodeGroupSelected)
            checkHost.getNodeFormat()
            if not checkHost.isNodenameHasRack():
                myNodeInfo.nodeRackNumber = 0

        # Screen ordering
        if replaceMode:
            screenList = [ WindowNodeStatus(self.dbconnection, self.kusuApp) ]

        elif haveInterface and haveNodegroup:
            screenList = [ WindowNodeStatus(self.dbconnection, self.kusuApp) ]

        elif haveNodegroup and not haveInterface:
            screenList = [ WindowSelectNode(self.dbconnection, self.kusuApp), WindowNodeStatus(self.dbconnection, self.kusuApp) ]

        else:
            screenList = [ NodeGroupWindow(self.dbconnection, self.kusuApp), 
                          WindowSelectNode(self.dbconnection, self.kusuApp),
                          WindowNodeStatus(self.dbconnection, self.kusuApp)
                         ]

        screenFactory = ScreenFactoryImpl(screenList)
        ks = screens.navigator.Navigator(screenFactory=screenFactory, screentitle="Add Hosts - Version 5.0", wizardmode=False)
        ks.run()

""" AddHostPlugin class
    This class is a virtual used to be implemented by plugins """

class AddHostPlugin:
    def __init__(self):
        """virtual"""
        pass
    
    def finish(self, dbconn):
        """virtual"""
        pass
    
    def added(self, dbconn, nodename, info):
        """virtual"""
        pass
    
    def deleted(self, dbconn, nodename, info):
        """virtual"""
        pass
    
    def replaced(self, dbconn, nodename, info):
        """virtual"""
        pass
        
    def updated(self, dbconn):
        """virtual"""
        pass
        
""" class nodeInfo
    This class handles adding, deleting, updating, replacing, it also provides functionality to generate a node name. """
class NodeInfo:
    def __init__(self, pluginlist=None, rack=0, nodegroup=None):
        self._rackNumber = rack  
        self._rankNumber = 0
        self._nodeGroupType = nodegroup
        self._nodeName = ""
        self._nodeList = []
        self._nodeFormat = ""
        self._rankCount = 0
        self._isMasterInstaller = False
        self._primaryInstallerName = ""
        self._dbReadonly = KusuDB()
        self._dbRWrite = KusuDB()
        self._pluginList = pluginlist
        self._newIPAddress = None
                
        # Do a try here
        self._dbReadonly.connect()
        self._dbRWrite.connect('kusudb', 'apache')

    def isNodenameHasRack(self):
        """isNodenameHasRack() - Public
        Checks if the node format has a Rack AND rank. If it does, returns true, else false
        """
        
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
        """getNodeFormat() - Public
        Gets and sets the node format from database.
        """
        
        self._dbReadonly.execute("select nameformat from nodegroups where ngid=%s" % self._nodeGroupType)
        self._nodeFormat = self._dbReadonly.fetchone()[0]

    def _hostNameParse(self):
        """_hostNameParse()
        Parses the node format and generates the appropriate node name
        """
        
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
        Gets the nodes from the database, returns a list of nodes and the conflicting node groups that share the same node format
        """
        
        self.getNodeFormat()
        self._dbReadonly.execute("SELECT ngid from nodegroups WHERE nameformat='%s'" % self._nodeFormat)
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
        gets and sets the primary installer name
        """
        
        self._primaryInstallerName = self._dbReadonly.getAppglobals('PrimaryInstaller')
                        
    def _getNodeID (self, nodename):
        """_getNodeID(nodename)
        Returns the node ID if found, otherwise false if nodename is the primary installer name, or not found in db
        """
        self._getPrimaryInstaller()
        if nodename.strip() == self._primaryInstallerName:
            self._isMasterInstaller = True
            return None
        try:
            self._dbReadonly.execute("SELECT nid from nodes WHERE nodes.name='%s'" % nodename)
            self._isMasterInstaller = False
            return self._dbReadonly.fetchone()[0]
        except:
             return None
    
    def _getNodeInformation(self, nodename):
        """_getNodeInformation(nodename)
        Returns node information: nodegroup id, node id, nic id, network id, ip address, mac address, node name
        """
        info = {}
        
        self._getPrimaryInstaller()
        if nodename.strip() == self._primaryInstallerName:
            self.isMasterInstaller = True
            return None
        self._dbReadonly.execute("SELECT nodes.ngid, nodes.nid, nodes.name, nics.netid, nics.ip, nics.mac FROM nodes, nics \
                                   WHERE nodes.name='%s' AND nodes.nid=nics.nid" % nodename)

        data = self._dbReadonly.fetchall()
        
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
        
    def addNode (self, macaddr):
        """newNode() - Public
        Returns a valid node not present in the kusu database. Use this function to create a new node.
        """
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
                     self._createNodeEntry(macaddr)
                     return self._nodeName

        # All existing nodes are consecutive, just create a new one (rank of 0).
        self._hostNameParse()
        self._createNodeEntry(macaddr)
        return self._nodeName

    def doUpdates(self):
        pass
    
    def deleteNode(self, nodename):
        """deleteNode(nodename) - Public
        Deletes node from database, and calls deleteDHCPLease() to delete the DHCP entry also.
        """
        
        # We can't be the master installer
        if not self._isMasterInstaller:
            nid = self._getNodeID(nodename)
            self._deleteDHCPLease(nodename)
            self._dbRWrite.execute("DELETE FROM nics where nid='%s'" % nid)
            self._dbRWrite.execute("DELETE FROM nodes where nid='%s'" % nid)

    def _isIPUsed(self, ipaddress):
        self._dbReadonly.execute("SELECT COUNT(*) FROM nics WHERE ip = '%s'" % ipaddress)
        result = self._dbReadonly.fetchone()[0]
        if int(result) == 0:
            return False
        return True
        
    def _createNodeEntry(self, macaddr):
        """createNodeEntry()
        Create a node in the database.
        """            
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
                      self._newIPAddress = ipfun.incrementIP(self._newIPAddress, IPincrement, subnetNetwork)
                 else:
                    break
                
             # We're a DHCP/boot interface
             if nicdev == myNodeInfo.selectedInterface:
                 self._createNICBootEntry(nodeID, networkID, self._newIPAddress, 1, macaddr)
                 self._writeDHCPLease(self._newIPAddress, macaddr)
             else:
             # Not a boot interface, just write out other info.
                 self._createNICBootEntry(nodeID, networkID, self._newIPAddress, 0)

    def replaceNodeEntry(self, nodename):
        """replaceNodeEntry(nodename)

        Replaces an existing node, first by deleting the existing DHCP entry for the node since it contains the old mac address. 
        Then setting the MAC address to NULL so a new DHCP request may be done. 
        """
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
        Replaces nics table containing new mac address for replaced node
        """
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
        will have its bootdhcp flag enabled. Otherwise, other network interfaces cannot be PXE booted from.
        """
        
        if macaddress:
            self._dbRWrite.execute("INSERT INTO nics (nid, netid, mac, ip, boot) VALUES ('%s', '%s', '%s', '%s', '%s')" % (nodeid, networkid, macaddress, ipaddress, bootflag))
        else:
            self._dbRWrite.execute("INSERT INTO nics (nid, netid, ip, boot) VALUES ('%s', '%s', '%s', '%s')" % (nodeid, networkid, ipaddress, bootflag))
   
    def _writeDHCPLease(self, ipaddr, macaddr):
        """writeDHCPLease(ipaddr, macaddr)
        Use DHCP's API to create a DHCP entry in the /var/lib/dhcpd/dhcpd.leases file
        """
        
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
        Use DHCP's API to delete a DHCP entry in the /var/lib/dhcpd/dhcpd.leases file
        """
        
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
        The dictionary uses the device name as its key item[1].
        """
        
        interfaceInfo = {}
        self._dbReadonly.execute("SELECT networks.netid, networks.device, networks.subnet, networks.startip, networks.inc FROM \
                                   networks,ng_has_net WHERE ng_has_net.netid=networks.netid AND ng_has_net.ngid = %s AND \
                                   networks.usingdhcp = 0" % self._nodeGroupType)
        data = self._dbReadonly.fetchall()
        for item in data:
             interfaceInfo[item[1]] = "%d %s %s %s" % (item[0], item[2], item[3], item[4])
        return interfaceInfo

    def findBootDevice(self, nodename):
        """findBootDevice() - Public
        Returns the boot device that has its boot flag set to 1
        """
        nid = self._getNodeID(nodename)
        self._dbReadonly.execute("SELECT networks.device FROM networks,nics WHERE networks.netid=nics.netid AND nics.nid=%s and nics.boot = 1" % nid)
        data = self._dbReadonly.fetchone()
        return data[0]

    # Plugin call actions
    def plugins_add(self, nodename):
        """plugins_add(nodename)
        Call all Add host plugins added() method
        """
        
        info = self._getNodeInformation(nodename)
        print "DEBUG: Calling added() method from plugins"
        for plugin in self._pluginList:
             # Does this AddHostPlugin instance have a added() method? If so, execute it.
             if callable(getattr(plugin, "added", None)):
                 plugin.added(self._dbReadonly, nodename, info)
         
    def plugins_removed(self, nodename):
        """plugins_removed(nodename)
        Call all Add host plugins removed() method
        """
        
        self._getPrimaryInstaller()
        info = self._getNodeInformation(nodename)
        # We can't remove the master installer
        print "DEBUG: Calling removed() method from plugins"
        if not self._isMasterInstaller:
            for plugin in self._pluginList:
                 # Does this AddHostPlugin instance have a removed() method? If so, execute it.
                 if callable(getattr(plugin, "removed", None)):
                     plugin.removed(self._dbReadonly, nodename, info)
        else:
            print "Error: You cannot remove the master installer!"
            
    def plugins_replaced(self, nodename):
        """plugins_replaced(nodename)
        Call all Add host plugins replaced() method
        """
        self._getPrimaryInstaller()
        info = self._getNodeInformation(nodename)
        
        # We can't replace the master installer
        print "DEBUG: Calling replaced() method from plugins"
        if not self._isMasterInstaller:
            for plugin in self._pluginList:
                 # Does this AddHostPlugin instance have a replaced() method If so, execute it.
                 if callable(getattr(plugin, "replaced", None)):
                     plugin.replace(self._dbReadonly, info)
        else:
            print "Error: You cannot replace the master installer itself!"
            
    def plugins_finished(self):
        """plugins_finished()
        Call all Add host plugins finished() method
        """
        print "DEBUG: Calling finished() method from plugins"
        for plugin in self._pluginList:
             # Does this AddHostPlugin instance have a finished() method If so, execute it.
             if callable(getattr(plugin, "finished", None)):
                 plugin.finished(self._dbReadonly)
    
    def plugins_updated(self):
        """plugins_updated()
        Call all Add host plugins updated() method
        """
        print "DEBUG: Calling updated() method from plugins"
        for plugin in self._pluginList:
             # Does this AddHostPlugin instance have a update() method If so, execute it.
             if callable(getattr(plugin, "update", None)):
                 plugin.updated(self._dbReadonly)

global myNode
myNode = NodeInfo(myNodeInfo.addHostPlugins)

class ScreenActions(screens.screenfactory.BaseScreen, screens.navigator.PlatformScreen):
        
    def hotkeyCallback(self):
        """ hotkeyCallback()
        Set callback function
        """
        
        self.ExitAction()
        
    def ExitAction(self, data=None):
        """ExitAction()
        Function Callback - Will pop up a quit dialog box if new nodes were added, otherwise quits without prompt
        """
        
        if myNodeInfo.quitPrompt:
            result = self.selector.popupDialogBox(self.kusuApp._("addhost_window_title_exit"), self.kusuApp._("addhost_instructions_exit"), 
                     (self.kusuApp._("addhost_yes_button"), self.kusuApp._("addhost_no_button")))
            if result == "no":
                return NAV_NOTHING
            if result == "yes":
                self.finish()  # Destroy the screens, exit
                sys.exit(0)
        else:
                self.finish()
                if len(myNodeInfo.nodesInstalled):
                    finishNodes = NodeInfo(myNodeInfo.addHostPlugins, myNodeInfo.nodeRackNumber, nodegroup=myNodeInfo.nodeGroupSelected)
                    finishNodes.plugins_finished()
                sys.exit(0)

class NodeGroupWindow(ScreenActions, screens.screenfactory.BaseScreen, screens.navigator.PlatformScreen):

    title = "addhost_window_title_nodegroup"
    #name = 'Node Group'   # used for wizardmode sidebar
    msg = "addhost_instruction_nodegroup"
    buttons = ['Exit']
    
    def setCallbacks(self):
        self.buttonsDict['Exit'].setCallback_(self.ExitAction)

    def drawImpl(self):
        """ Get list of node groups and allow a user to choose one """
        
        try:
            self.db.connect()
        except:
            self.finish()
            i18nPrint(self.kusuApp._("DB_Query_Error\n"))
            sys.exit(-1)

        query = "SELECT ngname,ngid FROM nodegroups"
        try:
            self.db.execute(query)
            nodeGroups = self.db.fetchall()
        except:
            self.finish()
            i18nPrint(self.kusuApp._("DB_Query_Error\n"))
            sys.exit(-1)
   
        self.screenGrid = snack.Grid(1, 2)
        instruction = snack.Textbox(40, 2, self.kusuApp._(self.msg), scroll=0, wrap=1)      
        self.listbox = snack.Listbox(5, scroll=1, returnExit=1)
        for ng,ngid in nodeGroups:
            self.listbox.append("%s" % ng, "%s" % ngid)

        self.screenGrid.setField(instruction, col=0, row=0, padding=(0,0,0,0), growx=0)
        self.screenGrid.setField(self.listbox, col=0, row=1, padding=(0,1,0,0), growx=0)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        myNodeInfo.nodeGroupSelected = self.listbox.current()
        #result = self.selector.popupStatus(self.kusuApp._("Debug Window"), self.kusuApp._("Debug: %s ") % nodeGroupSelected, 1)
        return True, 'Success'

    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """
        pass

class WindowSelectNode(ScreenActions, screens.screenfactory.BaseScreen, screens.navigator.PlatformScreen):

    title = "addhost_window_title_interface"
    msg = "addhost_instruction_interface"
    buttons = []
    selectedInterface = None

    def drawImpl(self):
        """" Get list of network interfaces and allow user to choose one"""
        
        networkList = []
        query = "SELECT networks.device, nics.ip FROM networks, nics, nodes WHERE nodes.nid=nics.nid AND \
                 nics.netid=networks.netid AND nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller') ORDER BY device"
        try:
            self.db.connect()
            self.db.execute(query)
            networks = self.db.fetchall()
        except:
            self.finish()
            i18nPrint(self.kusuApp._("DB_Query_Error\n"))
            sys.exit(-1)
        
        self.screenGrid = snack.Grid(1, 2)
        instruction = snack.Label(self.msg)
        instruction = snack.Textbox(40, 2, self.kusuApp._(self.msg), scroll=0, wrap=0) 
        defaultFlag = 1
        for networkInfo in networks:
            itemName = "%s  (%s)" % (networkInfo[0].ljust(4), networkInfo[1])
            if defaultFlag:
                networkList.append([itemName, networkInfo, 1 ])
            else:
                networkList.append([itemName, networkInfo, 0 ])
            defaultFlag = 0
 
        self.radioButtonList = snack.RadioBar(self.screenGrid, networkList)
            
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0,0,0,0), growx=0)
        self.screenGrid.setField(self.radioButtonList, col=0, row=1, padding=(0,1,0,1), growx=0)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        myNodeInfo.selectedInterface = self.radioButtonList.getSelection()[0]
        #result = self.selector.popupStatus(self.kusuApp._("Debug Window"), "Interface Selected: %s " % self.radioButtonList.getSelection()[0], 1)
        return True, 'Success'
    
    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """

        flag = 1
        filep = open("/var/log/messages", 'r')
        filep.seek(0, 2)
        #result = self.selector.popupStatus(self.kusuApp._("Debug Window"), "nodeRackNumber %s" % nodeRackNumber, 1)
        myNodeInfo.selectedInterface = self.radioButtonList.getSelection()[0]
        myNodeInfo.syslogFilePosition = filep.tell()
        filep.close()

        # Prompt for Rack Number if node format requires a rack number specified.
        if not myNodeInfo.nodeRackNumber:
           checkHost = NodeInfo(rack=myNodeInfo.nodeRackNumber, nodegroup=myNodeInfo.nodeGroupSelected)
           checkHost.getNodeFormat()
           if checkHost.isNodenameHasRack():
               while flag:
                 result = self.selector.popupInputBox(self.kusuApp._("addhost_window_title_rack"),
                    self.kusuApp._("addhost_instructions_rack"), [self.kusuApp._("addhost_gui_text_rack")], 
                    NOCANCEL, [self.kusuApp._("addhost_ok_button")], 40, 20)
                 try:
                     result = int(result[0])
                     if result < 0:
                         self.selector.popupStatus(self.kusuApp._("addhost_window_title_error"), 
                         self.kusuApp._("Error: Cannot specify a negative number. Please try again"), 2)
                         flag = 1
                     else:
                         myNodeInfo.nodeRackNumber = result
                         flag = 0
                 except:
                     self.selector.popupStatus(self.kusuApp._("addhost_window_title_error"), 
                            self.kusuApp._("Error: The value %s is not a number. Please try again" % result[0]), 2)
                     flag = 1

        return True, 'Success'
        
class WindowNodeStatus(ScreenActions, screens.screenfactory.BaseScreen, screens.navigator.PlatformScreen):
    title = "addhost_window_title_installing"
    buttons = []

    def drawImpl(self):
        self.currentScreen = self.selector.getCurrentScreen()
        self.listbox = snack.Listbox(10, scroll =1, returnExit = 1, width = 60, showCursor = 0)
        
        # We can't go back after we get here
        myNodeInfo.quitPrompt = False
        self.selector.disableBackButton()
        self.selector.endButtonTitle(self.kusuApp._("quit_button"))
        self.selector.setScreenTimer(500)
        self.screenGrid = snack.Grid(1, 2)
        self.screenGrid.setField(self.listbox, col=0, row=0, padding=(0,0,0,-1))

    def timerCallback(self):
        """timerCallback()
        Callback function - Cycle though /var/log/messages looking for nodes to add OR replace. Depends if optionReplaceMode is set from
        command line.
        """
        
        nodeName = None
        macAddress = None
        discoveryCheck = True

        if myNodeInfo.syslogFilePosition == None:
            filep = open("/var/log/messages", 'r')
            filep.seek(0, 2)
            myNodeInfo.syslogFilePosition = filep.tell()
            data = ""
        else:
            filep = open("/var/log/messages", 'r')
            filep.seek(myNodeInfo.syslogFilePosition, 0)
            data = filep.readlines()

# Mar 26 14:49:53 rocksfe2 dhcpd: DHCPDISCOVER from 00:0c:29:0a:04:38 via eth1
# Mar 26 14:49:53 rocksfe2 dhcpd: DHCPOFFER on 10.1.1.254 to 00:0c:29:0a:04:38 via eth1
# Mar 26 14:49:55 rocksfe2 dhcpd: DHCPREQUEST for 10.1.1.254 (10.1.1.1) from 00:0c:29:0a:04:38 via eth1
# Mar 26 14:49:55 rocksfe2 dhcpd: DHCPACK on 10.1.1.254 to 00:0c:29:0a:04:38 via eth1

        for line in data:
             if line.find("dhcpd:") >= 0:
                 tokens = line.split()
                 # Parse DHCPd lines from /var/log/messages, if we see DHCPDISCOVER, we might have a new node.
                 if len(tokens) > 5 and tokens[5] == "DHCPDISCOVER":
                    macAddress = tokens[7]
                    self.myNode = NodeInfo(myNodeInfo.addHostPlugins)
                    discoveryCheck = self.myNode.findMACAddress(macAddress)
                    # This is a new mac address to add to the database.
                    if discoveryCheck == False and (tokens[9][:-1] == myNodeInfo.selectedInterface or tokens[9] == myNodeInfo.selectedInterface) \
                        and not myNodeInfo.optionReplaceMode:
                        self.aNode = NodeInfo(myNodeInfo.addHostPlugins, myNodeInfo.nodeRackNumber, myNodeInfo.nodeGroupSelected)
                        nodeName = self.aNode.addNode(macAddress)
                        self.listbox.append("%s\t%s\t(Installing)" % (nodeName, macAddress), nodeName)
                        myNodeInfo.nodesInstalled.append([nodeName, macAddress])
                        del self.aNode
                    
                    if myNodeInfo.optionReplaceMode and discoveryCheck == False:
                       myNodeInfo.selectedInterface = self.myNode.findBootDevice(myNodeInfo.replaceNodeName)
                       # Check if the interface dhcp is PXEing from matches whats in the DB, if not don't bother trying to go further.
                       if (tokens[9][:-1] == myNodeInfo.selectedInterface or tokens[9] == myNodeInfo.selectedInterface):
                           self.selector.popupStatus(self.kusuApp._("Node Discovery"), "Discovered node: %s\nMac Address: %s" % (myNodeInfo.replaceNodeName, macAddress), 3)
                           self.myNode.replaceNICBootEntry (myNodeInfo.replaceNodeName, macAddress)
                           # Call Replace mode plugins
                           self.finish()
                           self.myNode.plugins_replaced(myNodeInfo.replaceNodeName)
                           self.myNode.plugins_finished()
                           sys.exit(0)
                    del self.myNode
        
        # Store current position of /var/log/messages
        myNodeInfo.syslogFilePosition = filep.tell()
        filep.close()

        # We must refresh or things will draw weird.
        self.currentScreen.refresh()
                                
    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        return True, 'Success'

    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """
        pass

def checkDBConnection(message, dbinst):
    """checkDBConnection(message, dbinst)
    Check if the database is present, otherwise, throw i18n error
    """
    
    try:
       dbinst.connect()
    except:
       i18nPrint(message)
       sys.exit(-1)

def i18nPrint(message, *args):
    """i18nPrint - Output messages to STDERR with Internationalization.
    Additional arguments will be used to substitute variables in the
    message output"""

    if len(args) > 0:
        mesg = message % args
    else:
        mesg = message
        sys.stderr.write(mesg)

            
class ScreenFactoryImpl(screens.screenfactory.ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the
       Navigator(or it's child) class.
    """

    def __init__(self, screenlist):
        screens.screenfactory.ScreenFactory.screens = screenlist

if __name__ == '__main__':
    app = AddHostApp()
    app.run()
