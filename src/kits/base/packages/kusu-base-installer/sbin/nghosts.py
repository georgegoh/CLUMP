#!/usr/bin/python
#
# Kusu nghosts
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
import tempfile
import string
import sys
from sets import Set
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
import snack
from kusu.ui.text.USXscreenfactory import USXBaseScreen
from kusu.ui.text.USXnavigator import *
from kusu.ui.text.screenfactory import ScreenFactory
from kusu.ui.text.kusuwidgets import *
import kusu.ipfun
from kusu.syncfun import syncfun
from kusu.nodefun import NodeFun

global database
global kusuApp
global reallyQuit
database = KusuDB()
kusuApp = KusuApp()
reallyQuit = False
        
NOCANCEL    = 0
ALLOWCANCEL = 1

class NodeMemberApp(object, KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

    def toolVersion(self, option, opt, value, parser):
        """ 
        toolVersion()
        Prints out the version of the tool to screen. 
        """

        print "Nghosts Version %s\n" % self.version
        sys.exit(0)

    def parseargs(self):
        """
        parseargs()
        Parse the command line arguments. """

        global database

        self.parser.add_option("-v", "--version", action="callback",
                                callback=self.toolVersion, help=kusuApp._("nghosts_version_usage"))
        self.parser.add_option("-l", "--list-all-nodegroups", action="store_true",
                                dest="allnodegroups", help=kusuApp._("nghosts_list_all_nodegroups_usage"))
        self.parser.add_option("-g", "--list-nodegroup", action="store", 
                                type="string", dest="listnodegroup", help=kusuApp._("nghosts_list_a_nodegroup_usage"))
        self.parser.add_option("-f", "--from-group", action="callback",
                                callback=self.varargs, dest="movegroups", help=self._("nghosts_from_group_usage"))
        self.parser.add_option("-t", "--to-group", action="store",
                                type="string", dest="togroup", help=kusuApp._("nghosts_to_group_usage"))
        self.parser.add_option("-n", "--copy-hosts", action="callback",
                                callback=self.varargs, dest="copyhosts", help=kusuApp._("nghosts_copy_hosts_usage"))
        self.parser.add_option("-r", "--reinstall", action="store_true", dest="reinstall", help=kusuApp._("nghosts_reinstall_usage"))
        self.parser.add_option("-a", "--rack", type="int", action="store", dest="racknumber", help=kusuApp._("nghosts_rack_usage"))

        (self._options, self._args) = self.parser.parse_args(sys.argv[1:])

    def nxor(self, *args):
        """nxor(varargs args)
        N-way function, only one condition may be true otherwise false. """

        return len([x for x in args if x]) == 1

    def run(self):
        """run()
        Run the application """
       
        global database
 
        # Parse command options
        self.parseargs()
            
        # Don't allow option -l -g -t to be used together. Mutually Exclusive.
        if (not self.nxor(bool(self._options.allnodegroups), bool(self._options.listnodegroup), bool(self._options.togroup))):
                    if (bool(self._options.allnodegroups) == False and bool(self._options.listnodegroup) == False \
                        and bool(self._options.togroup) == False):
                        pass
                    else:
                        self.parser.error(self._("nghosts_options_exclusive"))

        # Non required values, if not set default to these            
        if not bool(self._options.reinstall):
                self._options.reinstall = False
        else:
                self._options.reinstall = True
        
        # Handle -a option
        if self._options.racknumber:
            result = int(self._options.racknumber)
            if result < 0:
                self.parser.error(self._("rack_negative_number"))

        # Handle -r option
        if not bool(self._options.reinstall):
                self._options.reinstall = False
        else:
                self._options.reinstall = True
          
        # Handle -l option
        if self._options.allnodegroups:
            str= self._("Node Group Names")
            print str
            print "=" * len(str)
            print "\n"
            # Get a list of all node groups to iterate though:
            database.connect()
            database.execute("SELECT ngid,ngname FROM nodegroups")
            ng = database.fetchall()
            for groupid, groupname in ng:
                database.execute("select nodes.name, nodes.state from nodes WHERE NOT nodes.name=(SELECT kvalue FROM appglobals \
                                  WHERE kname='PrimaryInstaller' AND nodes.ngid=%s ORDER BY name)" % groupid)
                nodes = database.fetchall()
                if len(nodes):
                    print "%s".ljust(10) % groupname
                    print "%s".ljust(10) % ("-" * len(groupname))
                    for node,state in nodes:
                        print "%s".ljust(5) % node + "%s".rjust(1) % state
                    print "\n"
            sys.exit(0)
            
        # Handle -g options - List specific nodegroup
        if self._options.listnodegroup:
            database.connect()
            database.execute("SELECT ngid FROM nodegroups WHERE ngname='%s'" % self._options.listnodegroup)
            try:
                ngid = database.fetchall()[0][0]
                str= self._("Node Group")
                print str
                print "-" * len(str)
                print "\n"
                database.execute("select nodes.name from nodes WHERE NOT nodes.name=(SELECT kvalue FROM appglobals \
                                  WHERE kname='PrimaryInstaller' AND nodes.ngid=%s ORDER BY name)" % ngid)
                nodes = database.fetchall()
                if len(nodes):
                    print "%s" % self._options.listnodegroup
                    print "%s" % "-" * len(self._options.listnodegroup)
                    for node in nodes:
                       print "%s" % node
                    print "\n"
            except:
                self.parser.error("%s\n" % self._("options_invalid_nodegroup"))
            sys.exit(0)

        # Handle -t option - Copy to this node group.
        if bool(self._options.togroup):
            if not bool(self._options.movegroups) and not bool(self._options.copyhosts):
                    self.parser.error("%s\n" % self._("nghosts_options_togroup_options_needed"))
            else:
                    flag = 1
                    badnodes = []
                    nodesList = []
                    moveIPList = []
                    macsList = {}
                    myinterface = ""
                    nodeRecord = NodeFun()
                    nodeRecord.setNodegroupByName(self._options.togroup)
                    nodeRecord.getNodeFormat()
                    # Check if the selected node format has a rack if so, prompt for it.
                    if nodeRecord.isNodenameHasRack() and not bool(self._options.racknumber):
                       # Prompt user for Rack
                       while flag:
                          response = raw_input(kusuApp._("prompt_for_rack"))
                          try:
                              result = int(response)
                              if result < 0:
                                  print self._("rack_negative_number")
                                  flag = 1
                              else:
                                  self._options.racknumber = result
                                  nodeRecord.setRackNumber(result)
                                  flag = 0
                          except:
                              print self._("Error: The value %s is not a number. Please try again" % response)
                              flag = 1

                    if bool(self._options.movegroups):
                        moveList, ipList, macList, badList, interface = nodeRecord.moveNodegroups(self._options.movegroups, self._options.togroup)
                        nodesList += moveList 
                        moveIPList += ipList
                        myinterface = interface
                        macsList.update(macList)
           
		    if bool(self._options.copyhosts):
                        for node in self._options.copyhosts:
                            if not nodeRecord.validateNode(node):
                               print self._("Node not found: %s" % node)
                               badnodes.append(node)

                        for node in badnodes:
                               self._options.copyhosts.remove(node)

                        if not self._options.copyhosts:
                           print self._("There are no valid nodes to move to the node group '%s'" % self._options.togroup)
                           sys.exit(-1)
                        else:
                           moveList, ipList, macList, badList, interface = nodeRecord.moveNodes(self._options.copyhosts, self._options.togroup, self._options.racknumber)
                           nodesList += moveList
                           moveIPList += ipList
                           if interface:
                              myinterface = interface
                           macsList.update(macList)

                    if nodesList:
                        print self._("Will move the following hosts: [%s] to the node group '%s'" % (string.join(Set(nodesList), ", "), self._options.togroup))

                    if not nodesList:
                       print self._("Could not move the requested nodes to the '%s' node group. They may be already in the same node group or do not have a valid network to associate them to the new node group." % self._options.togroup)
                       sys.exit(0)
                    else:
                       if badList:
                          print self._("Only can move %d nodes because other nodes do not have a valid network boot device. Could not move %d nodes (%s) to the node group '%s'." % (len(nodesList), len(badList), string.join(badList, " "), self._options.togroup))

                    # Create Temp file
                    (fd, tmpfile) = tempfile.mkstemp()
                    tmpname = os.fdopen(fd, 'w')
                    for node in Set(nodesList):
                       tmpname.write("%s\n" % macsList[node])
                    tmpname.close()

                    print self._("nghosts_moving_nodes_progress")
                    os.system("/opt/kusu/sbin/addhost --remove %s" % string.join(Set(nodesList), ' '))
               
                    # Add these back using mac file
                    if self._options.racknumber >= 0:
                        os.system("/opt/kusu/sbin/addhost --file=%s --node-interface=%s --nodegroup='%s' --rack=%s" % (tmpfile, interface, self._options.togroup, self._options.racknumber))
                    else:
                        os.system("/opt/kusu/sbin/addhost --file=%s --node-interface=%s --nodegroup='%s'>&2 /dev/null" % (tmpfile, interface, self._options.togroup))

                    # If the user wants to reinstall the nodes check if the option is selected or not.
                    if bool(self._options.reinstall):
                        print self._("nghosts_reinstall_nodes_progress")
                        # Call PDSH here
                        rn = syncfun()
                        rn.runPdsh(list(Set(moveIPList)), "reboot")
                    os.remove(tmpfile)
                    sys.exit(0)
            
        # Handle -n without -t
        if bool(self._options.copyhosts) and not bool(self._options.togroup):
            self.parser.error(self._("nghosts_options_missing_togroup"))
        
        # Handle -f without -t
        if bool(self._options.movegroups) and not bool(self._options.togroup):
            self.parser.error(self._("nghosts_options_missing_togroup"))
            
        elif self._options.copyhosts == []:
            self.parser.error(self._("nghosts_options_nodes_missing"))

        elif self._options.movegroups == []:
            self.parser.error(self._("nghosts_options_groups_missing"))
            
        if len(sys.argv[1:]) > 0:
            if (not bool(self._options.allnodegroups) or not self._options.listnodegroup or not bool(self._options.togroup)):
                self.parser.error(self._("nghosts_options_required_options"))
                
        # Screen ordering
        screenList = [ MembershipMainWindow(database=database, kusuApp=kusuApp) ]

        screenFactory = ScreenFactoryImpl(screenList)
        ks = USXNavigator(screenFactory=screenFactory, screenTitle="Node Membership Editor - Version 5.0", showTrail=False)
        ks.run()

class SelectNodesWindow(USXBaseScreen):
    name = "nghosts_window_title_select_node"
    msg = "nghosts_instruction_select_node"
    buttons = [ 'move_button', 'previous_button', 'quit_button' ]
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.\t%s" % self.kusuApp._("helpline_instructions"))
        self.nodegroupDict = {}
        self.nodeGroupNames = []

 
    def F12Action(self):
        result = self.selector.popupDialogBox(self.kusuApp._("nghosts_window_title_exit"), self.kusuApp._("nghosts_instructions_exit"),
                (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            global reallyQuit
            reallyQuit = True
	    return NAV_QUIT
        else:
            return NAV_NOTHING

    def quitAction(self):
        global reallyQuit
        reallyQuit = True
        return NAV_QUIT
 
    def moveAction(self):
        flag = 1
        rack = 0
        needRack = False
        nodeRecord = NodeFun()

        if self.nodeCheckbox.getSelection() == [] or self.nodegroupRadio.getSelection() == None:
            self.selector.popupMsg(self.kusuApp._("Error"), self.kusuApp._("nghosts_nothing_selected"))
            return NAV_NOTHING

        result = self.selector.popupDialogBox(self.kusuApp._("nghosts_window_title_move_prompt"), \
                 self.kusuApp._("nghosts_instructions_move_nodes"), (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            moveList, moveIPList, macList, badList, interface = nodeRecord.moveNodes(self.nodeCheckbox.getSelection(), self.nodegroupRadio.getSelection())

            # None of the nodes could be moved at all. This maybe because the nodes are already in the node group or the nodes networks do not map
            # to the new destination node group.
            if not moveList:
               self.selector.popupMsg(self.kusuApp._("Notice"), self.kusuApp._("Could not move the selected nodes to the '%s' node group. They may be already in the same node group or do not have a valid network to associate them to the new node group.") % self.nodegroupRadio.getSelection())

            else:
               nodeRecord.setNodegroupByName(self.nodegroupRadio.getSelection())
               nodeRecord.getNodeFormat()
               # Check if the selected node format has a rack if so, prompt for it.
               if nodeRecord.isNodenameHasRack():
                   # Prompt user for Rack
                   needRack = True
                   while flag:
                      buttonPressed, result = snack.EntryWindow(self.screen, self.kusuApp._("addhost_window_title_rack"),
                      self.kusuApp._("addhost_instructions_rack"), [self.kusuApp._("addhost_gui_text_rack")],
                      NOCANCEL, 40, 20, [self.kusuApp._("ok_button")])
                      try:
                          result = int(result[0])
                          if result < 0:
                              self.selector.popupStatus(self.kusuApp._("Error"),
                              self.kusuApp._("Error: Cannot specify a negative number. Please try again"), 2)
                              flag = 1
                          else:
                              rack = result
                              nodeRecord.setRackNumber(rack)
                              flag = 0
                      except:
                          self.selector.popupStatus(self.kusuApp._("Error"),
                          self.kusuApp._("Error: The value %s is not a number. Please try again" % result[0]), 2)
                          flag = 1

               if badList and len(moveList) > 0:
                  self.selector.popupMsg(self.kusuApp._("Notice"), self.kusuApp._("Only can move %d nodes because other nodes do not have a valid network boot device. Could not move %d nodes (%s) to the node group '%s'.") % (len(moveList), len(badList), string.join(badList, " "), self.nodegroupRadio.getSelection()))

               # Create Temp file
               (fd, tmpfile) = tempfile.mkstemp()
               tmpname = os.fdopen(fd, 'w')
               for node in moveList:
                  tmpname.write("%s\n" % macList[node])
               tmpname.close()

               # Call addhosts to delete these nodes
               progDialog = ProgressDialogWindow(self.screen, self.kusuApp._("nghosts_moving_nodes"), self.kusuApp._("nghosts_moving_nodes_progress"))

               os.system("/opt/kusu/sbin/addhost --remove %s >&2 /dev/null >& /dev/null" % string.join(moveList, ' '))

               # Add these back using mac file
               if needRack:
                  os.system("/opt/kusu/sbin/addhost --file=%s --node-interface=%s --nodegroup='%s' --rack=%s >&2 /dev/null >& /dev/null" % (tmpfile, interface, self.nodegroupRadio.getSelection(), rack))
               else:
                  os.system("/opt/kusu/sbin/addhost --file=%s --node-interface=%s --nodegroup='%s'>&2 /dev/null >& /dev/null" % (tmpfile, interface, self.nodegroupRadio.getSelection()))

               # Remove temp file
               os.remove(tmpfile)
               progDialog.close()

               # If the user wants to reinstall the nodes check if the option is selected or not.
               if self.reinstcheckbox.value():
                  progDialog = ProgressDialogWindow(self.screen, self.kusuApp._("nghosts_reinstalling_nodes"), \
                               self.kusuApp._("nghosts_reinstall_nodes_progress"))
                  # Call PDSH here
                  rn = syncfun()
                  rn.runPdsh(moveIPList, "reboot")
                  progDialog.close()
            self.screen.refresh()
        return NAV_NOTHING
        
    def previousAction(self):
        return NAV_QUIT

    def setCallbacks(self):
        self.buttonsDict['move_button'].setCallback_(self.moveAction)        
        self.buttonsDict['previous_button'].setCallback_(self.previousAction)
        self.buttonsDict['quit_button'].setCallback_(self.quitAction)

        self.hotkeysDict['F12'] = self.F12Action
        self.hotkeysDict['F8'] = self.moveAction
        self.hotkeysDict['F5'] = self.previousAction
    
    def drawImpl(self):
        count = 0
        nodegroupList = []
        self.screenGrid  = snack.Grid(1, 6)
        self.nodeCheckbox = snack.CheckboxTree(height=8, width=30, scroll=1)
        instruction = snack.Textbox(65, 1, self.kusuApp._(self.msg), scroll=0, wrap=1)
        labeltokens = self.kusuApp._("nghosts_nodegroup_label").split(',')
        label = snack.Label(self.kusuApp._("%s %s" % (labeltokens[0].ljust(25),labeltokens[1])))
        self.reinstcheckbox = snack.Checkbox(self.kusuApp._("Reinstall Nodes"), isOn = 0)
        query = 'SELECT ngname, ngid FROM nodegroups WHERE NOT ngname = "unmanaged" ORDER BY ngid'
        
        try:
            self.database.connect()
            self.database.execute(query)
            nodegroups = self.database.fetchall()
        except:
            self.screen.finish()
            print self.kusuApp._("DB_Query_Error\n")
            sys.exit(-1)
    
        for nodegroup in nodegroups:
            query = "SELECT nodes.name FROM nodes,nodegroups WHERE nodes.ngid=nodegroups.ngid AND NOT \
            nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller') AND \
            nodegroups.ngname = '%s' ORDER BY nodes.name" % nodegroup[0]
        
            try:
                self.database.connect()
                self.database.execute(query)
                nodes = self.database.fetchall()
            except:
                self.screen.finish()
                print self.kusuApp._("DB_Query_Error\n")
                sys.exit(-1)

            # If the node group is empty don't display it.
            if len(nodes) > 0:
                self.nodeCheckbox.append(nodegroup[0])
                self.nodeGroupNames.append(nodegroup[0])
                self.nodegroupDict[nodegroup[0]] = []
            
            for node in nodes:
                self.nodeCheckbox.addItem(node[0], (count, snack.snackArgs['append']))
                self.nodegroupDict[nodegroup[0]].append(node[0])

            if len(nodes) > 0:
                count += 1
 
        for group in nodegroups:
            nodegroupList.append([group[0].ljust(27), group[0], 0])
       
        self.nodegroupRadio = snack.RadioBar(self.screenGrid, nodegroupList) 
        
        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1))
        self.screenGrid.setField(label, 0, 1, padding=(6,0,0,0), anchorLeft=1)
        self.screenGrid.setField(self.nodeCheckbox, 0, 2, padding=(0,0,30,0))
        self.screenGrid.setField(self.nodegroupRadio, 0, 3, padding=(33,-8,0,0))
        self.screenGrid.setField(self.reinstcheckbox, 0, 4, padding=(0,1,0,0), anchorLeft=1)
                
class SelectNodegroupsWindow(USXBaseScreen):
    name = "nghosts_window_title_select_nodegroup"
    msg = "nghosts_instruction_select_nodegroup"

    buttons = [ 'move_button', 'previous_button', 'quit_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.\t%s" % self.kusuApp._("helpline_instructions"))
          
    def F12Action(self):
        result = self.selector.popupDialogBox(self.kusuApp._("nghosts_window_title_exit"), self.kusuApp._("nghosts_instructions_exit"),
                (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            global reallyQuit
            reallyQuit = True
	    return NAV_QUIT

        else:
            return NAV_NOTHING
    
    def quitAction(self):
        global reallyQuit
        reallyQuit = True
        return NAV_QUIT

    def moveAction(self):
        flag = 1
        rack = 0
        needRack = False
        nodeRecord = NodeFun()

        if self.srcNodegroupsCheckbox.getSelection() == [] or self.destNodegroupRadio.getSelection() == None:
            self.selector.popupMsg(self.kusuApp._("Error"), self.kusuApp._("nghosts_nothing_selected_groups"))
            return NAV_NOTHING

        result = self.selector.popupDialogBox(self.kusuApp._("nghosts_window_title_move_prompt"), \
                 self.kusuApp._("nghosts_instructions_move_nodegroups"), (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            moveList, moveIPList, macList, badList, interface = nodeRecord.moveNodegroups(self.srcNodegroupsCheckbox.getSelection(), self.destNodegroupRadio.getSelection())

            # None of the nodes could be moved at all. This maybe because the nodes are already in the node group or the nodes networks do not map
            # to the new destination node group.
            if not moveList:
                self.selector.popupMsg(self.kusuApp._("Error"), self.kusuApp._("Could not move the selected nodes to the '%s' node group. They may be already in the same node group or do not have a valid network to associate them to the new node group.") % self.destNodegroupRadio.getSelection())

            else:
                nodeRecord.setNodegroupByName(self.destNodegroupRadio.getSelection())
                nodeRecord.getNodeFormat()
                # Check if the selected node format has a rack if so, prompt for it.
                if nodeRecord.isNodenameHasRack():
                    # Prompt user for Rack
                    needRack = True
                    while flag:
                       buttonPressed, result = snack.EntryWindow(self.screen, self.kusuApp._("addhost_window_title_rack"),
                       self.kusuApp._("addhost_instructions_rack"), [self.kusuApp._("addhost_gui_text_rack")],
                       NOCANCEL, 40, 20, [self.kusuApp._("ok_button")])
                       try:
                          result = int(result[0])
                          if result < 0:
                              self.selector.popupStatus(self.kusuApp._("Error"),
                              self.kusuApp._("Error: Cannot specify a negative number. Please try again"), 2)
                              flag = 1
                          else:
                              rack = result
                              flag = 0
                       except:
                          self.selector.popupStatus(self.kusuApp._("Error"),
                          self.kusuApp._("Error: The value %s is not a number. Please try again" % result[0]), 2)
                          flag = 1

            if badList and len(moveList) > 0:
                self.selector.popupMsg(self.kusuApp._("Notice"), self.kusuApp._("Only can move %d nodes because other nodes do not have a valid network boot device. Could not move %d nodes (%s) to the node group '%s'.") % (len(moveList), len(badList), string.join(badList, " "), self.destNodegroupRadio.getSelection()))

            if len(moveList) > 0:
                # Create Temp file
                (fd, tmpfile) = tempfile.mkstemp()
                tmpname = os.fdopen(fd, 'w')
                for node in moveList:
                   tmpname.write("%s\n" % macList[node])
                tmpname.close()

                # Call addhosts to delete these nodes
                progDialog = ProgressDialogWindow(self.screen, self.kusuApp._("nghosts_moving_nodes"), self.kusuApp._("nghosts_moving_nodes_progress"))
                os.system("/opt/kusu/sbin/addhost --remove %s >&2 /dev/null >& /dev/null" % string.join(moveList, ' '))

                # Add these back using mac file
                if needRack:
                   os.system("/opt/kusu/sbin/addhost --file=%s --node-interface=%s --nodegroup='%s' --rack=%s >&2 /dev/null >& /dev/null" % (tmpfile, interface, self.destNodegroupRadio.getSelection(), rack))
                else:
                   os.system("/opt/kusu/sbin/addhost --file=%s --node-interface=%s --nodegroup='%s'>&2 /dev/null >& /dev/null" % (tmpfile, interface, self.destNodegroupRadio.getSelection()))

                # Remove temp file
                os.remove(tmpfile)
                progDialog.close()
 
                # If the user wants to reinstall the nodes check if the option is selected or not.
                if self.reinstcheckbox.value():
                    progDialog = ProgressDialogWindow(self.screen, self.kusuApp._("nghosts_reinstalling_nodes"), \
                                 self.kusuApp._("nghosts_reinstall_nodes_progress"))
                    # Call PDSH here
                    rn = syncfun()
                    rn.runPdsh(moveIPList, "reboot")
                    progDialog.close()
            self.screen.refresh()
        return NAV_NOTHING
 
    def previousAction(self):
        return NAV_QUIT

    def setCallbacks(self):
        self.buttonsDict['move_button'].setCallback_(self.moveAction)
        self.buttonsDict['previous_button'].setCallback_(self.previousAction)
        self.buttonsDict['quit_button'].setCallback_(self.quitAction)

        self.hotkeysDict['F12'] = self.F12Action
        self.hotkeysDict['F8'] = self.moveAction
        self.hotkeysDict['F5'] = self.previousAction

        
    def drawImpl(self):
        nodegroupList = []
        self.screenGrid  = snack.Grid(1, 7)
        self.srcNodegroupsCheckbox = snack.CheckboxTree(height=8, width=30, scroll=1)
        instruction = snack.Textbox(65, 1, self.kusuApp._(self.msg), scroll=0, wrap=1)
        labeltokens = self.kusuApp._("nghosts_source_label").split(',')
        label = snack.Label(self.kusuApp._("%s %s" % (labeltokens[0].ljust(25),labeltokens[1])))
        self.reinstcheckbox = snack.Checkbox(self.kusuApp._("Reinstall Nodes"), isOn = 0)
        query = 'SELECT ngname, ngid FROM nodegroups WHERE NOT ngname = "unmanaged" ORDER BY ngid'

        try:
            self.database.connect()
            self.database.execute(query)
            nodegroups = self.database.fetchall()
        except:
            self.screen.finish()
            print self.kusuApp._("DB_Query_Error\n")
            sys.exit(-1)

        for group in nodegroups:
           nodegroupList.append([group[0].ljust(23), group[0], 0])
           query = "SELECT COUNT(*) from nodes,nodegroups WHERE nodes.ngid=nodegroups.ngid AND nodegroups.ngname='%s'" % group[0]
           try:
               self.database.connect()
               self.database.execute(query)
               nodes = self.database.fetchall()[0]
               test = nodes[0]
           except:
               self.screen.finish()
               print self.kusuApp._("DB_Query_Error\n")
               sys.exit(-1)
 
           # Only display node groups that are not empty when moving.
           # Installer is special case, we can't move the installer group if there's only the master installer left.
           if group[1] == 1:  
              if not int(nodes[0]) == 1:
                  self.srcNodegroupsCheckbox.append(group[0])
           else:     
               if int(nodes[0]) > 0: 
                  self.srcNodegroupsCheckbox.append(group[0])

        self.destNodegroupRadio = snack.RadioBar(self.screenGrid, nodegroupList)

        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1))
        self.screenGrid.setField(label, 0, 1, padding=(7,0,0,0), anchorLeft=1)
        self.screenGrid.setField(self.srcNodegroupsCheckbox, 0, 2, padding=(3,0,0,0), anchorLeft=1)
        self.screenGrid.setField(self.destNodegroupRadio, 0, 3, padding=(0,-8,4,0), anchorRight=1)
        self.screenGrid.setField(self.reinstcheckbox, 0, 4, padding=(0,1,0,0), anchorLeft=1)


    def validate(self):
        return True, 'Success'

class MembershipMainWindow(USXBaseScreen):

    name = "nghosts_window_title_prompt"
    msg = "nghosts_instruction_prompt"
    buttons = [ 'next_button', 'quit_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        self.kusuApp = KusuApp()
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.\t%s" % self.kusuApp._("nghosts_helpline_intro"))

    def F12Action(self):
        result = self.selector.popupDialogBox(self.kusuApp._("nghosts_window_title_exit"), self.kusuApp._("nghosts_instructions_exit"),
                (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
	    self.screen.finish()
            return NAV_QUIT
        else:
            return NAV_NOTHING
        
    def nextAction(self, data=None):
        global database
        global kusuApp
        global reallyQuit
        
        # Check if the user selected no option. Pop up a msgbox with an error.
        if self.radioButtonList.getSelection() == None:
            self.selector.popupMsg(self.kusuApp._("No option selected"), self.kusuApp._("nghosts_window_select_option"))
            return NAV_NOTHING
        
        if self.radioButtonList.getSelection() == 0:
            ScreenFactory.screens = \
                            [ SelectNodesWindow(database=database, kusuApp=kusuApp) ]
        else:
            ScreenFactory.screens = \
                            [ SelectNodegroupsWindow(database=database, kusuApp=kusuApp) ]
        
        ks = USXNavigator(screenFactory=ScreenFactory, screenTitle="Node Membership Editor - Version 5.0", showTrail=False)
        ks.run()
        if reallyQuit:
           return NAV_QUIT
        else:
           return NAV_NOTHING
        
    def exitAction(self, data=None):
        return NAV_QUIT
        
    def setCallbacks(self):
        # Button actions
        self.buttonsDict['next_button'].setCallback_(self.nextAction)
        self.buttonsDict['quit_button'].setCallback_(self.exitAction)
        
        self.hotkeysDict['F12'] = self.F12Action
        self.hotkeysDict['F8'] = self.nextAction

        
    def drawImpl(self):
        """ Get list of node groups and allow a user to choose one """
    
        self.screenGrid = snack.Grid(1, 3)
        instruction = snack.Textbox(70, 3, self.kusuApp._(self.msg), scroll=0, wrap=1)
        
        defaultFlag = 1
        selectionOption = []
        selectionOption.append([self.kusuApp._("nghosts_copy_selected_nodes"), 0, 0])
        selectionOption.append([self.kusuApp._("nghosts_copy_nodegroup"), 1, 0])
        self.radioButtonList = snack.RadioBar(self.screenGrid, selectionOption)
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0, 0, 0, 0), growx=1)
        self.screenGrid.setField(self.radioButtonList, col=0, row=1, padding=(0,0,0,2), growx=0)

class ScreenFactoryImpl(ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the
       Navigator(or it's child) class.
    """

    def __init__(self, screenlist):
        ScreenFactory.screens = screenlist

if __name__ == '__main__':
    app = NodeMemberApp()
    app.run()

