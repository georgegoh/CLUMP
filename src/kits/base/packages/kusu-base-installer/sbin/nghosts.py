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
import sys
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
import snack
from kusu.ui.text.OCSscreenfactory import OCSBaseScreen
from kusu.ui.text.OCSnavigator import *
from kusu.ui.text.screenfactory import ScreenFactory
from kusu.ui.text.kusuwidgets import *
import kusu.ipfun

global database
global kusuApp
database = KusuDB()
kusuApp = KusuApp()
        
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
        global kusuApp

        self.parser.add_option("-v", "--version", action="callback",
                                callback=self.toolVersion, help=kusuApp._("nghosts_version_usage"))
        self.parser.add_option("-l", "--list-all-nodegroups", action="store_true",
                                dest="allnodegroups", help=kusuApp._("nghosts_list_all_nodegroups_usage"))
        self.parser.add_option("-g", "--list-nodegroup", action="store", 
                                type="string", dest="listnodegroup", help=kusuApp._("nghosts_list_a_nodegroup_usage"))
        self.parser.add_option("-f", "--from-group", action="store",
                                type="string", dest="fromgroup", help=kusuApp._("nghosts_from_group_usage"))
        self.parser.add_option("-t", "--to-group", action="store",
                                dest="string", dest="togroup", help=kusuApp._("nghosts_to_group_usage"))
        self.parser.add_option("-n", "--copy-hosts", action="store",
                                type="string", dest="copyhosts", help=kusuApp._("nghosts_copy_hosts_usage"))
        self.parser.add_option("-r", "--reinstall", action="store_true", dest="reinstall", help=kusuApp._("nghosts_reinstall_usage"))

        (self._options, self._args) = self.parser.parse_args(sys.argv[1:])

    def nxor(self, *args):
        """nxor(varargs args)
        N-way function, only one condition may be true otherwise false. """

        return len([x for x in args if x]) == 1

    def run(self):
        """run()
        Run the application """
        
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
                    
        # Handle -l option
        if self._options.allnodegroups:
            print "List all Nodes in each node group!"
            sys.exit(0)
            
        # Handle -g options - List specific nodegroup
        if self._options.listnodegroup:
            print "List specific node group"
            sys.exit(0)

        # Handle -t option - Copy to this node group.
        if bool(self._options.togroup):
            if not bool(self._options.fromgroup) and not bool(self._options.copyhosts):
                    print "Not enough options, use -f or -n only."
                    sys.exit(0)
            else:
                    if bool(self._options.fromgroup):
                            print "Copy from this Nodegroup!"
            
                    if bool(self._options.copyhosts):
                            print "Copy specific nodes only!"
                            
            sys.exit(0)
            
        # Handle -n without -t
        if bool(self._options.copyhosts) and not bool(self._options.togroup):
            print "need to specify -t"
            sys.exit(0)
        
        # Handle -f without -t
        if bool(self._options.fromgroup) and not bool(self._options.togroup):
            print "need to specify -t"
            sys.exit(0)
            
            
        if len(sys.argv[1:]) > 0:
            if (not bool(self._options.allnodegroups) or not self._options.listnodegroup or not bool(self._options.togroup)):
                self.parser.error(self._("nghosts_options_required_options"))
                
        # Screen ordering
        screenList = [ MembershipMainWindow(database=database, kusuApp=kusuApp) ]

        screenFactory = ScreenFactoryImpl(screenList)
        ks = OCSNavigator(screenFactory=screenFactory, screenTitle="Node Membership Editor - Version 5.0", showTrail=False)
        ks.run()

class SelectNodeWindow(OCSBaseScreen):
    name = "netedit_window_title_edit"
    msg = "netedit_instruction_edit"
    buttons = [ 'next_button', 'previous_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        OCSBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.")
    
    def nextAction(self):
        return NAV_FORWARD
        
    def previousButton(self):
        return NAV_BACK
            
    def setCallbacks(self):
        
        self.buttonsDict['ok_button'].setCallback_(self.nextAction)
        self.buttonsDict['previous_button'].setCallback_(self.previousButton)
    
        self.hotkeysDict['F5'] = self.cancelAction
        self.hotkeysDict['F8'] = self.okAction
    
    def drawImpl(self):
#        self.database.connect()
#        query = "SELECT network, subnet, gateway, device, startip, suffix, inc, options, netname, usingdhcp FROM networks WHERE netid = %d" % \
#                int(selectedNetwork.current()[0])

#        try:
#            self.database.execute(query)
#            self.networkRecord = list(self.database.fetchone())
#        except:
#            self.finish()
#            print self._("DB_Query_Error\n")
#            sys.exit(-1)
#            
        self.screenGrid  = snack.Grid(1, 2)
        
        instruction = snack.Textbox(60, 1, self.kusuApp._("Please edit any of the network information below."), scroll=0, wrap=0)
        
        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1))
    
    def validate(self):
        return True, 'Success'
        
class SelectNodeGroupWindow(OCSBaseScreen):

    name = "netedit_window_title_new"
    msg = "netedit_instruction_new"
    buttons = [ 'ok_button', 'cancel_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        OCSBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc\tInstructions: Press F5 to cancel screen, Press F8 to accept changes")
                            
    def setCallbacks(self):
        pass
        
    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        instruction = snack.Textbox(60, 1, self.kusuApp._("Please enter the network information below."), scroll=0, wrap=0)
    
    def validate(self):
        return True, 'Success'

class FinishWindow(OCSBaseScreen):

    name = "netedit_window_title_new"
    msg = "netedit_instruction_new"
    buttons = [ 'ok_button', 'cancel_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        OCSBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc\tInstructions: Press F5 to cancel screen, Press F8 to accept changes")
                            
    def setCallbacks(self):
        pass
        
    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        instruction = snack.Textbox(60, 1, self.kusuApp._("Please enter the network information below."), scroll=0, wrap=0)
    
    def validate(self):
        return True, 'Success'
        
class MembershipMainWindow(OCSBaseScreen):

    name = "nghosts_window_title_prompt"
    msg = "nghosts_instruction_prompt"
    buttons = [ 'next_button', 'quit_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        self.kusuApp = KusuApp()
        OCSBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc - Instructions: Select an option. Press F12 to quit, Press F8 to go next")

    def F12Action(self):
        result = self.selector.popupDialogBox(self.kusuApp._("netedit_window_title_exit"), self.kusuApp._("netedit_instructions_exit"), 
                (self.kusuApp._("yes_button"), self.kusuApp._("no_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            return NAV_QUIT
        else:
            return NAV_NOTHING
        
    def nextAction(self, data=None):
        global database
        global kusuApp
        
        # Check if the user selected no option. Pop up a msgbox with an error.
        if self.radioButtonList.getSelection() == None:
            self.selector.popupMsg(self.kusuApp._("No option selected"), "Please select an option to continue.")
            return NAV_NOTHING
        
        if self.radioButtonList.getSelection() == 0:
            ScreenFactory.screens = \
                            [ SelectNodeWindow(database=database, kusuApp=kusuApp),
                              SelectNodeGroupWindow(database=database,kusuApp=kusuApp),
                              FinishWindow(database=database,kusuApp=kusuApp)
                            ]
                            
        else:
            ScreenFactory.screens = \
                            [ SelectNodeGroupWindow(database=database, kusuApp=kusuApp),
                              FinishWindow(database=database,kusuApp=kusuApp)
                            ]
        
        ks = OCSNavigator(ScreenFactory,screenTitle="Node Membership Editor - Version 5.0", showTrail=False)
        ks.run()
        
    def exitAction(self, data=None):
        """ExitAction()
        Function Callback - Will pop up a quit dialog box if new nodes were added, otherwise quits without prompt
        """
        return NAV_QUIT
        
    def setCallbacks(self):
        pass
        # Button actions
        self.buttonsDict['next_button'].setCallback_(self.nextAction)
        self.buttonsDict['quit_button'].setCallback_(self.exitAction)
        
        self.hotkeysDict['F12'] = self.F12Action
        self.hotkeysDict['F8'] = self.nextAction
        
    def drawImpl(self):
        """ Get list of node groups and allow a user to choose one """
    
        self.screenGrid = snack.Grid(1, 3)
        instruction = snack.Textbox(80, 3, self.kusuApp._("Welcome to the Node Membership Editor. Please choose one of the options below."), scroll=0, wrap=0)
        
        defaultFlag = 1
        selectionOption = []
        selectionOption.append(["Copy individual nodes from a Node group", 0, 0])
        selectionOption.append(["Copy alll nodes from a node group", 1, 0])
        self.radioButtonList = snack.RadioBar(self.screenGrid, selectionOption)
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0, 0, 0, 0), growx=1)
        self.screenGrid.setField(self.radioButtonList, col=0, row=1, padding=(0,0,0,2), growx=0)

    def validate(self):
        self.selector.popupStatus(self._("Debug Window"), "Debug: %s" % radioButtonList.getselection(), 3)
        
class ScreenFactoryImpl(ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the
       Navigator(or it's child) class.
    """

    def __init__(self, screenlist):
        ScreenFactory.screens = screenlist

if __name__ == '__main__':
    app = NodeMemberApp()
    app.run()

