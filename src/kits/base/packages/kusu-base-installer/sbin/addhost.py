#!/usr/bin/python
#
# Kusu add host
#
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

# Author: Shawn Starr <sstarr@platform.com>

import os
import re
import sys
import time
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
import snack
from kusu.ui.text.USXscreenfactory import USXBaseScreen, ScreenFactory
from kusu.ui.text.USXnavigator import *
from kusu.ui.text.kusuwidgets import *
from kusu.nodefun import NodeFun
from kusu.util.errors import UserExitError
import kusu.util.log as kusulog
import kusu.ipfun

NOCANCEL    = 0
ALLOWCANCEL = 1

class NodeData:
    def __init__(self):
        # Public 
        self.nodeRackNumber = 0
        self.nodeGroupSelected = 0
        self.nodeList = []
        self.selectedInterface = None
        self.selectedNodeInterface = None
        self.syslogFilePosition = None
        self.optionReplaceMode = False
        self.optionStaticHostMode = False
        self.staticHostname = None
        self.staticIPAddress = None
        self.optionDHCPMode = False
        self.pluginLocation = "/opt/kusu/lib/plugins/addhost"
        self.forceQuitflag = False
        # We don't want to prompt the user to quit if we reached the last screen.
        self.quitPrompt = True

global kusuApp
kusuApp = KusuApp()

if os.geteuid() != 0:
   print kusuApp._("nonroot_execution\n")
   sys.exit(-1)

# Global Instance of data
global myNodeInfo
myNodeInfo = NodeData()

global myNode
myNode = kusu.nodefun.NodeFun()

global pluginActions
pluginActions = None


global database
database = KusuDB()

class AddHostApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

    def toolVersion(self, option, opt, value, parser):
        """ 
        toolVersion()
        Prints out the version of the tool to screen. 
        """
        
        print "Addhost Version %s\n" % self.version
        self.unlock()
        sys.exit(0)
        
    def parseargs(self):
        """
        parseargs()
        Parse the command line arguments. """

        self.parser.add_option("-v", "--version", action="callback",
                                callback=self.toolVersion, help=self._("addhost_version_usage"))
        self.parser.add_option("-n", "--nodegroup", action="store",
                                type="string", dest="nodegroup", help=self._("addhost_nodegroup_usage"))
        self.parser.add_option("-i", "--interface", action="store",
                                type="string", dest="interface", help=self._("addhost_interface_usage"))
        self.parser.add_option("-j", "--node-interface", action="store",
                                type="string", dest="nodeinterface", help=self._("addhost_nodeinterface_usage"))
        self.parser.add_option("-f", "--file", action="store",
                                type="string", dest="macfile", help=self._("addhost_macfile_usage"))
        self.parser.add_option("-e", "--remove", action="callback",
                                dest="remove", callback=self.varargs, help=self._("addhost_remove_usage"))
        self.parser.add_option("-p", "--replace", action="store",
                                type="string", dest="replace", help=self._("addhost_replace_usage"))
        self.parser.add_option("-r", "--rack", action="store",
                                type="int", dest="rack", help=self._("addhost_rack_usage"))
        self.parser.add_option("-u", "--update", action="store_true", 
                                dest="update", help=self._("addhost_update_usage"))
        self.parser.add_option("-s", "--static-host", action="store", 
                                dest="statichost", help=self._("addhost_statichost_usage"))
        self.parser.add_option("-x", "--ip-address", action="store", 
                                dest="ipaddr", help=self._("addhost_ipaddr_usage"))
        (self._options, self._args) = self.parser.parse_args(sys.argv[1:])

    def loadPlugins(self):
        """ loadPlugins()
        Loads all plugins for Add hosts. """
       
        global pluginActions
        global database
        pluginList = []
        pluginInstances = []
        moduleInstance = None

        # Make a connection to the database:
        try:
            database.connect()
        except:
            print self._("DB_Query_Error\n")
            self.unlock()
            sys.exit(-1)

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
             if ext == ".py":
                if not plugin == "__init__" and not plugin[0] == '.':
                    pluginList.append(plugin)
                
        # Import the plugins
        moduleInstances = map(__import__, pluginList)
        
        # Create instances of each new plugin and store the instances.
        for thisModule in moduleInstances:
             try:
                 thisPlugin = thisModule.AddHostPlugin(database)
	         if thisPlugin.enabled():
                    pluginInstances.append(thisPlugin)
             except:
                 print kusuApp._("Warning: Invalid plugin '%s'. Does not have a AddHostPlugin class.\nThis plugin will be IGNORED." % thisModule)
        pluginActions = PluginActions(pluginInstances)
    
    def nxor(self, *args):
        """nxor(varargs args)
        N-way function, only one condition may be true otherwise false. """
        
        return len([x for x in args if x]) == 1
        
    def run(self):
        """run()
        Run the application """
        
        screenList = []

        global kusuApp
        
        haveInterface = False
        haveNodeInterface = False
        haveNodegroup = False
        replaceMode = False

        # Check if nghosts is in use, if so abort running addhost.
        if os.path.isfile("/var/lock/subsys/nghosts"):
           print kusuApp._("addhost_nghosts_lock")
           sys.exit(-1)

        if self.islock():
           print kusuApp._("addhost_already_inuse")
           sys.exit(-1)

        kl = kusulog.getKusuLog()
        kl.addFileHandler("/tmp/kusu/kusu.log")

        # Parse command options
        self.parseargs()
       
        self.lock()
        # Load addhost plugins
        self.loadPlugins()
        
        # Lists are special in Python, handle boolean differently.
        if self._options.remove == []:
            removeFlag = True
        else:
            removeFlag = bool(self._options.remove)
           
        # Don't allow option -n -p -e -u -s to be used together. Mutually exclusive.
        if (not self.nxor(bool(self._options.nodegroup), bool(self._options.replace), bool(self._options.update), removeFlag, self._options.statichost)):
                    if (bool(self._options.nodegroup) == False and bool(self._options.replace) == False and bool(self._options.update) == False and removeFlag == False and bool(self._options.statichost) == False):
                        pass
                    else:
                        self.unlock()
                        self.parser.error(kusuApp._("addhost_options_exclusive"))

        # Handle -r option
        if self._options.rack:
            result = int(self._options.rack)
            if result < 0:
                self.unlock()
                self.parser.error(kusuApp._("rack_negative_number"))
            else:
                myNodeInfo.nodeRackNumber = self._options.rack

        # Handle -s option
        if self._options.ipaddr and self._options.statichost:
           if not kusu.ipfun.validIP(self._options.ipaddr):
              self.unlock()
              self.parser.error(kusuApp._("addhost_invalid_ip"))

           myNodeInfo.optionStaticHostMode = True
           myNode.setNodegroupByName("unmanaged")
           result, msg = myNode.addUnmanagedStaticDevice(self._options.statichost, ip=self._options.ipaddr)
           if not result:
              print "ERROR:  %s" % msg
              self.unlock()
              sys.exit(-1)

           if pluginActions:
              pluginActions.plugins_add(self._options.statichost.strip())
              pluginActions.plugins_finished()
           self.unlock()
           sys.exit(0)

        if self._options.statichost and not self._options.ipaddr:
	   self.unlock()
           self.parser.error(kusuApp._("addhost_unmanaged_no_ip"))
 
        # Handle -i option
        if self._options.interface:
            if self._options.interface[0] == '-':
                self.unlock()
                self.parser.error(kusuApp._("addhost_options_interface_required"))
            else:
                if myNode.validateInterface(self._options.interface, installer=True):
                    myNodeInfo.selectedInterface = self._options.interface
                    haveInterface = True
                else:
                    self.unlock()
                    self.parser.error(kusuApp._("addhost_options_invalid_interface"))

        if self._options.interface:
           if not self._options.nodegroup:
             self.unlock()
             self.parser.error(kusuApp._("addhost_options_interface_options_needed"))

        # Handle -j option needed for -f only
        if self._options.nodeinterface:
              myNodeInfo.selectedNodeInterface = self._options.nodeinterface
              haveNodeInterface = True
       
        if self._options.nodeinterface:
            if not self._options.macfile or not self._options.nodegroup:
               self.unlock()
               self.parser.error(kusuApp._("addhost_options_macfile_options_needed"))
   
        # Handle -n option
        if self._options.nodegroup:
            if self._options.nodegroup[0] == '-':
               self.unlock()
               self.parser.error(kusuApp._("addhost_options_nodegroup_required"))
            else:
                # Check for valid nodegroup. if not return an error.
                result, ngid = myNode.validateNodegroup(self._options.nodegroup)
                if result:
                    myNodeInfo.nodeGroupSelected = ngid
                    haveNodegroup = True
                else:
                    self.unlock()
                    self.parser.error(kusuApp._("options_invalid_nodegroup"))

        # Handle -f -j -n options
        if (self._options.macfile and self._options.nodeinterface and self._options.nodegroup):

            # Check if the node group's interfaces are valid. 
            if not myNode.validateInterface(self._options.nodeinterface, installer=False, nodegroup=myNodeInfo.nodeGroupSelected):
               self.unlock()
               self.parser.error(kusuApp._("addhost_options_invalid_interface"))

            # Check if the file specified exists.
            if not os.path.isfile(self._options.macfile):
                self.unlock()
                self.parser.error(kusuApp._("The file '%s' was not found" % self._options.macfile))
                
            myNode.setNodegroupByID(myNodeInfo.nodeGroupSelected)
            if haveNodegroup and not self._options.rack:
                if self._options.rack == 0:
                    myNodeInfo.nodeRackNumber = self._options.rack
                else:
                    flag = 1
                    if myNode.isNodenameHasRack() and haveNodeInterface:
                         while flag:
                            try:
                                response = raw_input(kusuApp._("prompt_for_rack"))
                            except KeyboardInterrupt, e:
                                print "\nAborted!"
                                self.unlock()
                                sys.exit(0)
                                 
                            try:
                               result = int(response)
                               if result < 0:
                                  print kusuApp._("rack_negative_number")
                                  flag = 1
                               else:
                                  myNodeInfo.nodeRackNumber = result
                                  myNode.setRackNumber(myNodeInfo.nodeRackNumber) 
                                  flag = 0
                            except:
                               print kusuApp._("Error: The value %s is not a number. Please try again" % response)
                               flag = 1
              
            # Read in list of mac addresses
            macfileList = [line for line in open(self._options.macfile,'r') if len(line.strip()) > 0]
            myNode.setRackNumber(myNodeInfo.nodeRackNumber)
            #myNode.setNodegroupByName(myNodeInfo.nodeGroupSelected)
            for macaddr in macfileList:
                 if not re.search("(?<![-0-9a-f:])([\da-fA-F]{2}[-:]){5}([\da-fA-F]{2})(?![-0-9a-f:])", macaddr):
                    print kusuApp._("Skipping '%s'. Not a MAC address" % macaddr.strip())
                    continue

                 macaddr = macaddr.lower().strip()
                 checkMacAddr = myNode.findMACAddress(macaddr)
                 if checkMacAddr == False:
                     nodeName = myNode.addNode(macaddr, myNodeInfo.selectedNodeInterface, installer=False)
                     print kusuApp._("Adding Node: %s, %s" % (nodeName, macaddr))
                     # Ask all plugins to call added() function
                     myNode.addUsedMAC(macaddr)
                     if pluginActions:
                         pluginActions.plugins_add(nodeName, True)
                     myNodeInfo.nodeList.append(nodeName)
                 else:
                     print kusuApp._("Duplicate: %s, Ignoring" % macaddr)
 
            if pluginActions:
                pluginActions.plugins_finished(True)
            self.unlock()
            sys.exit(0)
              
        if self._options.macfile:
            if not self._options.interface or not self._options.nodegroup:
               self.unlock()
               self.parser.error(kusuApp._("addhost_options_macfile_options_needed"))

        # Handle -p option
        if self._options.replace:
            if self._options.replace.strip().isdigit():
                self.unlock()
                self.parser.error(kusuApp._("addhost_options_invalid_node"))
            else:
                if self._options.replace[0] == '-':
                    self.unlock()
                    self.parser.error(kusuApp._("addhost_options_replace_required"))
                else:
                    if myNode.validateNode(self._options.replace):
                        replaceMode = True
                        myNodeInfo.optionReplaceMode = True
                        myNodeInfo.replaceNodeName = self._options.replace
                        if myNode.replaceNodeEntry(self._options.replace) == False:
                            self.unlock()
                            sys.exit(-1)
                    else:
                        print kusuApp._("The node %s is not found. Please try again\n" % self._options.replace)
                        self.unlock()
                        sys.exit(-1)

        # Handle -e option
        if self._options.remove:
            delflag = False
            for delnode in self._options.remove:
                 if delnode.strip().isdigit():
                     self.unlock()
                     self.parser.error(kusuApp._("addhost_options_invalid_node"))
                 # Disallow options next to options.
                 if delnode[0] == '-':
                     self.unlock()
                     self.parser.error(kusuApp._("addhost_options_invalid_node"))

                 # Ask all plugins to call removed() function
                 if pluginActions:
                    pluginActions.plugins_removed(delnode)
                 myNodeInfo.nodeList.append(delnode)

                 print kusuApp._("Removing Node: %s" % delnode)
                 # Handle removing node from db.
                 if myNode.deleteNode(delnode):
                    delflag = True
            if pluginActions and delflag:
               pluginActions.plugins_finished()
            self.unlock()
            sys.exit(0)

        elif self._options.remove == []:
              self.unlock()
              self.parser.error(kusuApp._("addhost_options_remove_required"))

        # Handle -u option
        if self._options.update:
            # Ask all plugins to call updated() function
            if pluginActions:
               pluginActions.plugins_updated()
               pluginActions.plugins_finished()
            self.unlock()
            sys.exit(0)
    
        # If node group format has a Rack AND Rank, prompt for the rack number.
        if haveNodegroup and not self._options.rack and not self._options.macfile:
            if self._options.rack == 0:
               myNodeInfo.nodeRackNumber = self._options.rack
            else:
               myNode.setRackNumber(myNodeInfo.nodeRackNumber)
               myNode.setNodegroupByID(myNodeInfo.nodeGroupSelected)
               flag = 1
               if myNode.isNodenameHasRack() and haveInterface:
                   while flag:
                      try:
                          response = raw_input(kusuApp._("prompt_for_rack"))
                      except KeyboardInterrupt, e:
                          print "\nAborted!"
                          self.unlock()
                          sys.exit(0)
                      try:
                          result = int(response)
                          if result < 0:
                             print kusuApp._("rack_negative_number")
                             flag = 1
                          else:
                             myNodeInfo.nodeRackNumber = result
                             flag = 0
                      except:
                          print kusuApp._("Error: The value %s is not a number. Please try again" % response)
                          flag = 1
        elif (haveNodegroup and self._options.macfile and self._options.interface):
             self.unlock()
             self.parser.error(kusuApp._("Cannot use -i with -f and -n options"))

        # If nodegroup format and rack specified but node format does not have a rack AND rank. Ignore user set rack and use 0.
        if (haveNodegroup and self._options.rack):
            myNode.setRackNumber(myNodeInfo.nodeRackNumber)
            myNode.setNodegroupByID(myNodeInfo.nodeGroupSelected)

            if not myNode.isNodenameHasRack():
                myNodeInfo.nodeRackNumber = 0

        # Screen ordering
        global database

        if replaceMode:
            screenList = [ WindowNodeStatus(database=database, kusuApp=kusuApp) ]

        elif haveInterface and haveNodegroup:
            screenList = [ WindowNodeStatus(database=database, kusuApp=kusuApp) ]

        elif haveNodegroup and not haveInterface:
            screenList = [ WindowSelectNode(database=database, kusuApp=kusuApp),
                           WindowNodeStatus(database=database, kusuApp=kusuApp) 
                         ]

        else:
            screenList = [ NodeGroupWindow(database=database, kusuApp=kusuApp), 
                          WindowSelectNode(database=database, kusuApp=kusuApp),
                          WindowNodeStatus(database=database, kusuApp=kusuApp)
                         ]

        screenFactory = ScreenFactoryImpl(screenList)
        ks = USXNavigator(screenFactory=screenFactory, screenTitle="Add Hosts - Version 5.0", showTrail=False)
        ks.run()

        if len(myNodeInfo.nodeList):
            if pluginActions:
               pluginActions.plugins_finished()

        self.unlock()
 
class PluginActions(object, KusuApp):
    def __init__(self, pluginInstances):
        KusuApp.__init__(self)
        self._pluginInstances = pluginInstances
        global myNode
        self._nodeHandler = myNode
        
    # Plugin call actions
    def plugins_add(self, nodename, prePopulateMode=False):
        """plugins_add(nodename)
        Call all Add host plugins added() method
        """
        
        #pt1=time.time()
        if self._nodeHandler.nodeIsPrimaryInstaller(nodename):
            print self._("add_primary_installer_error\n")
            return
            
        info = self._nodeHandler.getNodeInformation(nodename)

        for plugin in self._pluginInstances:
            #t1=time.time()
            plugin.added(nodename, info, prePopulateMode)
            #t2=time.time()
            #print "====> PLUGIN: %s: Time Spent: added(): %f" % (plugin, t2-t1)
      
        #t2=time.time() 
        #print "******** ALL added() Plugins Time Spent: %f" % (t2-pt1)
         
    def plugins_removed(self, nodename):
        """plugins_removed(nodename)
        Call all Add host plugins removed() method
        """
         
        #pt1=time.time()
        #print "DEBUG: Calling removed() method from plugins"
        info = self._nodeHandler.getNodeInformation(nodename)
        for plugin in self._pluginInstances:
            #t1=time.time()
            plugin.removed(nodename, info)
            #t2=time.time()
            #print "====> PLUGIN: %s: Time Spent: removed(): %f" % (plugin, t2-t1)

        #t2=time.time()
        #print "******** ALL removed() Plugins Time Spent: %f" % (t2-pt1)
            
    def plugins_replaced(self, nodename):
        """plugins_replaced(nodename)
        Call all Add host plugins replaced() method
        """
        
        #pt1=time.time()
        #print "DEBUG: Calling replaced() method from plugins"
        if not self._nodeHandler.nodeIsPrimaryInstaller(nodename):
            info = self._nodeHandler.getNodeInformation(nodename)
            for plugin in self._pluginInstances:
                #t1=time.time()
                plugin.replaced(nodename, info)
                #t2=time.time()
                #print "====> PLUGIN: %s: Time Spent: replaced(): %f" % (plugin, t2-t1)
        else:
            print self._("replace_primary_installer_error\n")
            self.unlock()
            sys.exit(-1)
        #t2=time.time()
        #print "******** ALL replaced() Plugins Time Spent: %f" % (t2-pt1)
            
    def plugins_finished(self, prePopulateMode=False):
        """plugins_finished()
        Call all Add host plugins finished() method
        """
	global myNodeInfo
        #pt1=time.time()
        #print "DEBUG: Calling finished() method from plugins"
        for plugin in self._pluginInstances:
            #t1=time.time()
            plugin.finished(myNodeInfo.nodeList, prePopulateMode)
            #t2=time.time()
            #print "====> PLUGIN: %s: Time Spent: finished(): %f" % (plugin, t2-t1)
        #t2=time.time()
        #print "******** ALL finished() Plugins Time Spent: %f" % (t2-pt1)
    
    def plugins_updated(self):
        """plugins_updated()
        Call all Add host plugins updated() method
        """
        #print "DEBUG: Calling updated() method from plugins"
        #pt1=time.time()
        for plugin in self._pluginInstances:
            #t1=time.time()
            plugin.updated()
            #t2=time.time()
            #print "====> PLUGIN: %s: Time Spent: updated(): %f" % (plugin, t2-t1)
        #t2=time.time()
        #print "******** ALL updated() Plugins Time Spent: %f" % (t2-pt1)

class NodeGroupWindow(USXBaseScreen):

    name = "addhost_window_title_nodegroup"
    msg = "addhost_instruction_nodegroup"
    buttons = ['next_button', 'exit_button']
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
	self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.\t%s" % self.kusuApp._("addhost_helpline_instructions"))

    def F12Action(self):
        if myNodeInfo.quitPrompt:
            result = self.selector.popupDialogBox(self.kusuApp._("addhost_window_title_exit"), self.kusuApp._("addhost_instructions_exit"), 
                    (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
            if result == "no":
                return NAV_NOTHING
            if result == "yes":
                return NAV_QUIT
        else:
            if len(myNodeInfo.nodeList):
                if pluginActions:
                   pluginActions.plugins_finished()
            return NAV_QUIT
 
    def exitAction(self, data=None):
        """ExitAction()
        Function Callback - Will pop up a quit dialog box if new nodes were added, otherwise quits without prompt
        """
        if len(myNodeInfo.nodeList):
            if pluginActions:
               pluginActions.plugins_finished()
        return NAV_QUIT

    def backAction(self):
        return NAV_BACK

    def nextAction(self):
        return NAV_FORWARD
        
    def setCallbacks(self):
        self.buttonsDict['next_button'].setCallback_(self.nextAction)
        self.buttonsDict['exit_button'].setCallback_(self.exitAction)

        self.hotkeysDict['F12'] = self.F12Action
	self.hotkeysDict['F8'] = self.nextAction
        
    def drawImpl(self):
        """ Get list of node groups and allow a user to choose one """
      
        try:
            self.database.connect()
        except:
           self.selector.popupMsg (self.kusuApp._("Error"), self.kusuApp._("DB_Query_Error\n"))
           self.screen.finish()
           raise UserExitError

        query = "SELECT ngname, ngid FROM nodegroups ORDER BY ngid"
        try:
            self.database.execute(query)
            nodeGroups = self.database.fetchall()
        except:
            self.selector.popupMsg (self.kusuApp._("Error"), self.kusuApp._("DB_Query_Error\n"))
            self.screen.finish()
            raise UserExitError
   
        self.screenGrid = snack.Grid(1, 2)
        instruction = snack.Textbox(40, 2, self.kusuApp._(self.msg), scroll=0, wrap=1)      
        self.listbox = snack.Listbox(5, scroll=1, returnExit=1)

        #value = snack.ListboxChoiceWindow(self.screen, self.kusuApp._(self.name), self.kusuApp._(self.msg), nodeGroups, buttons = ['Next', 'Exit'], width = 40, scroll=1, height=6, default=None, help=None)

        for ng,ngid in nodeGroups:
            self.listbox.append("%s" % ng, "%s" % ngid)
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0, 0, 0, 1), growx=1)
        self.screenGrid.setField(self.listbox, col=0, row=1, padding=(0, 0, 0, 1), growx=1)

        #self.screenGrid.setField(self.listbox, col=0, row=0, padding=(0, 0, 0, 1), growx=1)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        myNodeInfo.nodeGroupSelected = self.listbox.current()
        if myNode.getNodegroupNameByID(myNodeInfo.nodeGroupSelected) == 'unmanaged':
           myNodeInfo.optionStaticHostMode = True
           screenList = [ WindowUnmanaged(database=database, kusuApp=kusuApp) ]
           screenFactory = ScreenFactoryImpl(screenList)
           ks = USXNavigator(screenFactory=screenFactory, screenTitle="Add Hosts - Version 5.0", showTrail=False)
           result = ks.run()
           if not myNodeInfo.optionDHCPMode:
              raise UserExitError
        else:
           myNodeInfo.optionStaticHostMode = False
    
        return True, 'Success'

    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """
        pass

class WindowSelectNode(NodeGroupWindow):

    name = "addhost_window_title_interface"
    msg = "addhost_instruction_interface"
    buttons = ['next_button', 'previous_button']
    #selectedInterface = None

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.\t%s" % self.kusuApp._("addhost_helpline_instructions"))

    def setCallbacks(self):
        self.buttonsDict['previous_button'].setCallback_(self.backAction)
        self.buttonsDict['next_button'].setCallback_(self.nextAction)

        self.hotkeysDict['F12'] = self.F12Action
	self.hotkeysDict['F8'] = self.nextAction
	self.hotkeysDict['F5'] = self.backAction
        
    def drawImpl(self):
        """" Get list of network interfaces and allow user to choose one"""
       
        networkList = []
        validNets = []
        itemName = None
        # Get installer's available networks.
        try:
            self.database.connect()
            query = "SELECT DISTINCT networks.network, networks.subnet, networks.device, networks.gateway FROM networks, nics, nodes WHERE nodes.nid=nics.nid AND \
                     nics.netid=networks.netid AND networks.usingdhcp=0 AND nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller') AND networks.type = 'provision' ORDER BY device"
            self.database.execute(query)
            installerInfo = self.database.fetchall()

            # Get list of node group's available gateways.
            query = "SELECT networks.gateway FROM networks, ng_has_net WHERE ng_has_net.netid=networks.netid AND ng_has_net.ngid=%s AND networks.usingdhcp=0" % \
                    myNodeInfo.nodeGroupSelected
            self.database.execute(query) 
            ngInfo = self.database.fetchall()
        except:
            self.selector.popupMsg (self.kusuApp._("Error"), self.kusuApp._("DB_Query_Error\n"))
            self.screen.finish()
            raise UserExitError

        defaultFlag = 1
        # Static mode needs to see all the interfaces from the installer we don't care about if a network fits on any interface
        if myNodeInfo.optionStaticHostMode:
           for installer_network, installer_subnet, installer_device, installer_gateway in installerInfo:
               itemName = "%s  (%s)" % (installer_device.ljust(4), installer_gateway)
               if defaultFlag:
                  networkList.append([itemName, installer_device, 1 ])
               else:
                  networkList.append([itemName, installer_device, 0 ])
               defaultFlag = 0
        else:
           # Check if any node group networks match/fit in to the installer networks found if so display those only.
           for installer_network, installer_subnet, installer_device, installer_gateway in installerInfo:
               for ng_gateway in set(ngInfo):
                   if kusu.ipfun.onNetwork(installer_network, installer_subnet, ng_gateway[0]):
                      itemName = "%s  (%s)" % (installer_device.ljust(4), installer_gateway)
                      if defaultFlag:
                         networkList.append([itemName, installer_device, 1 ])
                      else:
                         networkList.append([itemName, installer_device, 0 ])
                      defaultFlag = 0
         
           if not networkList:
              self.selector.popupMsg (self.kusuApp._("Error"), "No network interfaces were associated to the selected node group. Unable to add nodes.")
              os.unlink("/var/lock/subsys/addhost")
              self.screen.finish()
              raise UserExitError

        self.screenGrid = snack.Grid(1, 2)

        if myNodeInfo.forceQuitflag == True:
           return NAV_QUIT

        instruction = snack.Label(self.msg)
        instruction = snack.Textbox(40, 2, self.kusuApp._(self.msg), scroll=0, wrap=0)
        self.radioButtonList = snack.RadioBar(self.screenGrid, networkList)
        self.screenGrid.setField(self.radioButtonList, col=0, row=1, padding=(0,0,0,2), growx=0)
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0,0,0,0), growx=1)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        myNodeInfo.selectedInterface = self.radioButtonList.getSelection()
        #result = self.selector.popupStatus(self.kusuApp._("Debug Window"), myNodeInfo.selectedInterface, 1)
        return True, 'Success'
    
    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """

        flag = 1
        filep = open("/var/log/messages", 'r')
        filep.seek(0, 2)
        myNodeInfo.selectedInterface = self.radioButtonList.getSelection()
        myNodeInfo.syslogFilePosition = filep.tell()
        filep.close()

        # Prompt for Rack Number if node format requires a rack number specified.
        if not myNodeInfo.nodeRackNumber:
           myNode.setRackNumber(myNodeInfo.nodeRackNumber)
           myNode.setNodegroupByID(myNodeInfo.nodeGroupSelected)
           if myNode.isNodenameHasRack():
               while flag:
                    buttonPressed, result = snack.EntryWindow(self.screen, self.kusuApp._("addhost_window_title_rack"),
                    self.kusuApp._("addhost_instructions_rack"), [self.kusuApp._("addhost_gui_text_rack")], 
                    NOCANCEL, 40, 20, [self.kusuApp._("ok_button")])
                    try:
                        result = int(result[0])
                        if result < 0:
                            self.selector.popupStatus(self.kusuApp._("Error"), 
                            "%s\n" % self.kusuApp._("rack_negative_number"), 2)
                            flag = 1
                        else:
                            myNodeInfo.nodeRackNumber = result
                            flag = 0
                    except:
                        self.selector.popupStatus(self.kusuApp._("Error"), 
                        self.kusuApp._("Error: The value %s is not a number. Please try again" % result[0]), 2)
                        flag = 1

        return True, 'Success'
       
class WindowUnmanaged(NodeGroupWindow):
    name = "addhost_window_title_unmanaged"
    buttons = ['ok_button', 'exit_button']

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
	self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.\t%s" % self.kusuApp._("addhost_helpline_instructions"))

    def F12Action(self):
        if myNodeInfo.quitPrompt:
            result = self.selector.popupDialogBox(self.kusuApp._("addhost_window_title_exit"), self.kusuApp._("addhost_instructions_exit"),
                    (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
            if result == "no":
                return NAV_IGNORE
            if result == "yes":
                raise UserExitError
        else:
            if len(myNodeInfo.nodeList):
                if pluginActions:
                   pluginActions.plugins_finished()
            raise UserExitError

    def exitAction(self):
        return NAV_QUIT
   
    def setCallbacks(self):
        self.buttonsDict['ok_button'].setCallback_(self.validateInfo)
        self.buttonsDict['exit_button'].setCallback_(self.exitAction)
        self.hotkeysDict['F12'] = self.F12Action

    def checkDHCPStatus(self):
        if self.dhcpCheck.value():
           self.IPEntry.setEnabled(False) # DHCP set
           myNodeInfo.optionDHCPMode = True
        else:
           self.IPEntry.setEnabled(True) # DHCP not set
           myNodeInfo.optionDHCPMode = False
        
    def drawImpl(self):
        instruction = snack.Textbox(50, 3, self.kusuApp._("addhost_unmanaged_instructions"), scroll=0, wrap=1)
        self.staticHostname = LabelledEntry(labelTxt=self.kusuApp._("addhost_hostname_label"), text="", width=20,
                password=0, returnExit = 0)

        self.dhcpCheck = snack.Checkbox(self.kusuApp._("netedit_field_dhcp"), isOn = 0)
        self.IPEntry = LabelledEntry(labelTxt=self.kusuApp._("addhost_ipaddr_label"), text="", width=20,
                password=0, returnExit = 0)
        self.dhcpCheck.setCallback(self.checkDHCPStatus)

        self.screenGrid = snack.Grid(1, 4)
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0,0,0,0))
        self.screenGrid.setField(self.staticHostname, col=0, row=1, padding=(-11,1,0,0))
        self.screenGrid.setField(self.dhcpCheck, col=0, row=2, padding=(-30,1,0,0))
        self.screenGrid.setField(self.IPEntry, col=0, row=3, padding=(-10,1,0,0))

    def validateInfo(self):
        # Validate if hostname is used or not.
        myNodeInfo.staticHostname = self.staticHostname.value().strip()
        myNodeInfo.staticIPAddress = self.IPEntry.value().strip()
        # The hostname is already used, try another one

        if len(myNodeInfo.staticHostname) == 0:
           self.selector.popupStatus(self.kusuApp._("Error"), 
           self.kusuApp._("Error: Must provide a hostname"), 3)
           return NAV_NOTHING

        if myNodeInfo.staticHostname.find(' ') > 0:
           self.selector.popupStatus(self.kusuApp._("Error"),
           self.kusuApp._("Error: Cannot have a space in the hostname"), 3)
           return NAV_NOTHING

        if myNode.validateNode(myNodeInfo.staticHostname):
           self.selector.popupStatus(self.kusuApp._("Error"),
           self.kusuApp._("Error: The hostname %s is already in use. Please another hostname" % myNodeInfo.staticHostname), 3)
           return NAV_NOTHING
       
        # Is what the user typed a valid IP address? 
        if not kusu.ipfun.validIP(myNodeInfo.staticIPAddress) and myNodeInfo.optionDHCPMode == False:
           self.selector.popupStatus(self.kusuApp._("Error"),
           self.kusuApp._("Error: '%s' is not a valid IP Address, try again" % myNodeInfo.staticIPAddress), 4)
           return NAV_NOTHING
        
        if myNode.isIPUsed(myNodeInfo.staticIPAddress):
           self.selector.popupStatus(self.kusuApp._("Error"),
           self.kusuApp._("Error: The IP '%s' is already in use. Try another" % myNodeInfo.staticIPAddress), 4)
           return NAV_NOTHING

        if  myNodeInfo.optionDHCPMode == False:
           result = self.selector.popupStatus(self.kusuApp._("Adding Device"), "Adding device: %s, IP: %s" % (myNodeInfo.staticHostname, myNodeInfo.staticIPAddress), 2)
           myNode.addUnmanagedStaticDevice(myNodeInfo.staticHostname.strip(), myNodeInfo.staticIPAddress.strip())
           myNodeInfo.forceQuitflag = True
           if pluginActions:
              pluginActions.plugins_add(myNodeInfo.staticHostname.strip())
              pluginActions.plugins_finished()
        return NAV_QUIT
 
class WindowNodeStatus(NodeGroupWindow):
    name = "addhost_window_title_installing"
    buttons = ['quit_button']

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setScreenTimer(500)

    def setCallbacks(self):
        self.buttonsDict['quit_button'].setCallback_(self.exitAction)
        self.hotkeysDict['F12'] = self.F12Action
    
    def drawImpl(self):
        self.listbox = snack.Listbox(10, scroll =1, returnExit = 0, width = 60, showCursor = 0)
        
        # We can't go back after we get here
        myNodeInfo.quitPrompt = False
        self.screenGrid = snack.Grid(1, 2)
        self.screenGrid.setField(self.listbox, col=0, row=0, padding=(0,0,0,0))

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

# Mar 26 14:49:53 host dhcpd: DHCPDISCOVER from 00:0c:29:0a:04:38 via eth1
# Mar 26 14:49:53 host dhcpd: DHCPOFFER on 10.1.1.254 to 00:0c:29:0a:04:38 via eth1
# Mar 26 14:49:55 host dhcpd: DHCPREQUEST for 10.1.1.254 (10.1.1.1) from 00:0c:29:0a:04:38 via eth1
# Mar 26 14:49:55 host dhcpd: DHCPACK on 10.1.1.254 to 00:0c:29:0a:04:38 via eth1

        for line in data:
             if line.find("dhcpd:") >= 0:
                 tokens = line.split()
                 # Parse DHCPd lines from /var/log/messages, if we see DHCPDISCOVER, we might have a new node.
                 if len(tokens) > 5 and tokens[5] == "DHCPDISCOVER":
                    macAddress = tokens[7]
                    self.myNode = kusu.nodefun.NodeFun()
                    discoveryCheck = self.myNode.findMACAddress(macAddress)
                    # This is a new mac address to add to the database.
                    if discoveryCheck == False and (tokens[9][:-1] == myNodeInfo.selectedInterface or tokens[9] == myNodeInfo.selectedInterface) \
                        and not myNodeInfo.optionReplaceMode and not myNodeInfo.optionStaticHostMode:
                        self.aNode = NodeFun(rack=myNodeInfo.nodeRackNumber, nodegroup=myNodeInfo.nodeGroupSelected)
                        nodeName = self.aNode.addNode(macAddress, myNodeInfo.selectedInterface, installer=True, snackInstance=self.screen)
                        self.listbox.append("%s\t%s\t(%s)" % (nodeName, macAddress, self.kusuApp._("addhost_installing_string")), nodeName)
                        self.listbox.setCurrent(nodeName)

                        if pluginActions:
                           pluginActions.plugins_add(nodeName)
                        myNodeInfo.nodeList.append(nodeName)
                        del self.aNode
                   
                    # Replace node  
                    if myNodeInfo.optionReplaceMode and discoveryCheck == False:
                       myNodeInfo.selectedInterface = self.myNode.findBootDevice(myNodeInfo.replaceNodeName)
                       # Check if the interface dhcp is PXEing from matches whats in the DB, if not don't bother trying to go further.
                       if (tokens[9][:-1] == myNodeInfo.selectedInterface or tokens[9] == myNodeInfo.selectedInterface):
                           self.selector.popupStatus(self.kusuApp._("addhost_node_discovery"), self.kusuApp._("Discovered node: %s\nMac Address: %s" % (myNodeInfo.replaceNodeName, macAddress)), 3)
                           self.myNode.replaceNICBootEntry (myNodeInfo.replaceNodeName, macAddress)
                           # Call Replace mode plugins
                           if pluginActions:
                              pluginActions.plugins_replaced(myNodeInfo.replaceNodeName)
                           return NAV_QUIT
 
                    # Adding a Static hostname w/ DHCP 
                    if myNodeInfo.optionStaticHostMode and myNodeInfo.optionDHCPMode and discoveryCheck == False:
                       if (tokens[9][:-1] == myNodeInfo.selectedInterface or tokens[9] == myNodeInfo.selectedInterface):
                          self.selector.popupStatus(self.kusuApp._("addhost_node_discovery"), self.kusuApp._("Adding Static device: %s" % myNodeInfo.staticHostname), 3)
                          self.myNode.addUnmanagedDHCPDevice(myNodeInfo.selectedInterface, myNodeInfo.staticHostname, macAddress)
                          
                          if pluginActions:
                             pluginActions.plugins_add(myNodeInfo.staticHostname)
                             pluginActions.plugins_finished()
                          return NAV_QUIT

                    del self.myNode
        
        # Store current position of /var/log/messages
        myNodeInfo.syslogFilePosition = filep.tell()
        filep.close()
        return NAV_IGNORE

        # We must refresh or things will draw weird.
        #self.selector.refresh()
                                
    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        return True, 'Success'

    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """
        pass

class ScreenFactoryImpl(ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the
       Navigator(or it's child) class.
    """
    def __init__(self, screenlist):
        ScreenFactory.screens = screenlist

if __name__ == '__main__':
    app = AddHostApp()
    app.run()
