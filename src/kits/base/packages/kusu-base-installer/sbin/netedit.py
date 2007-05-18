#!/usr/bin/python
#
# Kusu netedit
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
import string
import gettext
import time
import popen2
from kusu.app import KusuApp
from kusu.db import KusuDB
import snack
import kusu.screens.screenfactory
import kusu.screens.navigator
import kusu.screens.kusuwidgets
import kusu.nodefun
import kusu.ipfun

NAV_NOTHING = -1
NAV_FORWARD = 0
NAV_BACK = 1
NAV_QUIT = 2

NOCANCEL    = 0
ALLOWCANCEL = 1

class NetEditApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)
        self._database = KusuDB()
        self._kusuApp = KusuApp()

    def toolVersion(self, option, opt, value, parser):
        """ 
        toolVersion()
        Prints out the version of the tool to screen. 
        """
        
        print "Netedit Version %s\n" % self.version
        sys.exit(0)
        
    def parseargs(self):
        """
        parseargs()
        Parse the command line arguments. """

        self.parser.add_option("-v", "--version", action="callback",
                                callback=self.toolVersion, help=self._kusuApp._("netedit_version_usage"))
        self.parser.add_option("-l", "--list-networks", action="store",
                                type="string", dest="listnetworks", help=self._kusuApp._("netedit_listnetworks_usage"))
        self.parser.add_option("-d", "--delete", action="store_true",
                                dest="delete", help=self._kusuApp._("netedit_delete_usage"))
        self.parser.add_option("-a", "--add", action="store_true",
                                dest="add", help=self._kusuApp._("netedit_add_usage"))
        self.parser.add_option("-c", "--change", action="store_true",
                                dest="change", help=self._kusuApp._("netedit_change_usage"))

        self.parser.add_option("-w", "--old-network", action="store",
                                type="string", dest="oldnet", help=self._kusuApp._("netedit_oldnet_usage"))
        self.parser.add_option("-u", "--old-subnet", action="store",
                                type="string", dest="oldsubnet", help=self._kusuApp._("netedit_oldsubnet_usage"))
        self.parser.add_option("-n", "--network", action="store", dest="network", help=self._kusuApp._("netedit_network_usage"))
        self.parser.add_option("-s", "--subnet", action="store", dest="subnet", help=self._kusuApp._("netedit_subnet_usage"))
        self.parser.add_option("-i", "--interface", action="store", dest="interface", help=self._kusuApp._("netedit_interface_usage"))
        self.parser.add_option("-x", "--name-suffix", action="store", dest="suffix", help=self._kusuApp._("netedit_suffix_usage"))
        self.parser.add_option("-g", "--gateway", action="store", dest="gateway", help=self._kusuApp._("netedit_gateway_usage"))
        self.parser.add_option("-o", "--options", action="store", dest="opt", help=self._kusuApp._("netedit_options_usage"))
        self.parser.add_option("-e", "--description", action="store", dest="desc", help=self._kusuApp._("netedit_description_usage"))
        self.parser.add_option("-p", "--dhcp", action="store_true", dest="dhcp", help=self._kusuApp._("netedit_dhcp_usage"))

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
        
        # Don't allow option -a -d -c to be used together. Mututually Exclusive.
        if (not self.nxor(bool(self._options.add), bool(self._options.delete), bool(self._options.change))):
                    if (bool(self._options.add) == False and bool(self._options.delete) == False and bool(self._options.change) == False):
                        pass
                    else:
                        self.parser.error(self._kusuApp._("netedit_options_exclusive"))

        # Handle -w option
        if self._options.oldnet:
            print "DEBUG: OLD NETWORK: %s" % self._options.oldnet

        # Handle -u option
        if self._options.oldsubnet:
            print "DEBUG: OLD SUBNET: %s" % self._options.oldsubnet

        # Handle -n option
        if self._options.network:
            print "DEBUG: NETWORK: %s" % self._options.network

        # Handle -s option
        if self._options.subnet:
            print "DEBUG: SUBNET: %s" % self._options.subnet

        # Handle -i option
        if self._options.interface:
            print "DEBUG: INTERFACE NAME: %s" % self._options.interface

        # Handle -x option
        if self._options.suffix:
            print "DEBUG: SUFFIX: %s" % self._options.suffix

        # Handle -g option
        if self._options.gateway:
            print "DEBUG: GATEWAY: %s" % self._options.gateway
      
        # Handle -o option
        if self._options.opt:
            print "DEBUG: OPTIONS: %s" % self._options.opt

        # Handle -e option
        if self._options.desc:
            print "DEBUG: DESCRIPTION: %s" % self._options.desc

        # Handle -p option
        if self._options.dhcp:
           print "DEBUG: DHCP FLAG: %s" % bool(self._options.dhcp)
        elif bool(self._options.dhcp) == False:
           print "DEBUG: DHCP FLAG: %s" % bool(self._options.dhcp)

        # Handle -a -n -s -i and -x options - Adding network
        if (self._options.add and self._options.network and self._options.subnet and self._options.interface and self._options.suffix):
            print "*** MODE: Adding network mode!!!!!!!!!!!!!"
            # do something
            sys.exit(0)

        if self._options.add == True:
            if not self._options.network or not self._options.subnet or not self._options.interface or not self._options.suffix:
                self.parser.error(self._kusuApp._("netedit_options_add_options_needed"))

        # Handle -d -n -s - Deleting network
        if (self._options.delete and self._options.network and self._options.subnet):
           print "*** MODE: Deleting network mode!!!!!!!!!!!!"
           # do something
           sys.exit(0)

        if self._options.delete == True:
            if not self._options.network or not self._options.subnet:
                self.parser.error(self._kusuApp._("netedit_options_delete_options_needed"))

        # Handle -c -w -u - Changing network
        if (self._options.change and self._options.oldnet and self._options.oldsubnet):
           print "*** MODE: Changing network mode!!!!!!!!!!!!"
           # do something
           sys.exit(0)

        if self._options.change == True:
            if not self._options.oldnet or not self._options.oldsubnet:
                self.parser.error(self._kusuApp._("netedit_options_change_options_needed"))
 
        if len(sys.argv[1:]) > 0:
            print "Check if -a -d -c used otherwise usage()!"
            if (not bool(self._options.add) or not bool(self._options.delete) or not bool(self._options.change)):
                self.parser.error(self._kusuApp._("netedit_options_required_options"))
 
        # Screen ordering
        screenList = [ NetworkMainWindow(self._database, self._kusuApp) ]

        screenFactory = ScreenFactoryImpl(screenList)
        ks = kusu.screens.navigator.Navigator(screenFactory=screenFactory, screentitle="Network Edit - Version 5.0", showTrail=False)
        ks.run()

class ScreenActions(kusu.screens.screenfactory.BaseScreen, kusu.screens.navigator.PlatformScreen):
        
    def hotkeyCallback(self):
        """ hotkeyCallback()
        Set callback function
        """
        
        self.exitAction()
        
    def exitAction(self, data=None):
        """ExitAction()
        Function Callback - Will pop up a quit dialog box if new nodes were added, otherwise quits without prompt
        """
       
        result = self.selector.popupDialogBox(self._("netedit_window_title_exit"), self._("netedit_instructions_exit"), 
                 (self._("yes_button"), self._("no_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            self.finish()  # Destroy the screens, exit
            sys.exit(0)
            
    def newAction(self, data=None):
        flag = 1
        myScreen = snack.SnackScreen()
        g1 = snack.Grid(1, 12)
        instruction = snack.Textbox(60, 1, self._("Please enter the network information below."), scroll=0, wrap=0)
        newNetwork= kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Network: ".rjust(13), width=30, password=0, returnExit = 0)
        newSubnet = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Subnet: ".rjust(13), width=30, password=0, returnExit = 0)
        newGateway= kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Gateway: ".rjust(13), width=30, password=0, returnExit = 0)
        newDevice = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Device: ".rjust(13), width=30, password=0, returnExit = 0)
        newStartIP = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Starting IP: ".rjust(10), width=30, password=0, returnExit = 0)
        newSuffix = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Suffix: ".rjust(13), width=30, password=0, returnExit = 0)
        newInc = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Increment: ".rjust(13), width=30, password=0, returnExit = 0)
        newOpt = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Options: ".rjust(13), width=30, password=0, returnExit = 0, scroll=1)
        newDesc = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Description: ".rjust(10), width=30, password=0, returnExit = 0)
        dhcpCheck = snack.Checkbox("Use DHCP", isOn = 0)
        buttonBar1 = snack.ButtonBar(self.selector.getCurrentScreen(), (("OK", "Cancel")))
        g1.setField(instruction, 0, 0, padding=(0,0,0,1), growx=1)
        g1.setField(newNetwork, 0, 1, padding=(0,0,0,0))
        g1.setField(newSubnet, 0, 2, padding=(0,0,0,0))
        g1.setField(newGateway, 0, 3, padding=(0,0,0,0)) # anchorLeft=1
        g1.setField(newDevice, 0, 4, padding=(0,0,0,0))
        g1.setField(newStartIP, 0, 5, padding=(0,0,0,0))
        g1.setField(newSuffix, 0, 6, padding=(0,0,0,0))
        g1.setField(newInc, 0, 7, padding=(0,0,0,0))
        g1.setField(newOpt, 0, 8, padding=(0,0,0,0))
        g1.setField(newDesc, 0, 9, padding=(0,0,0,1))
        g1.setField(dhcpCheck, 0, 10, padding=(13, 0, 0, 1), anchorLeft=1)
        g1.setField(buttonBar1, 0, 11, (0, 0, 0, 0))
        myScreen.gridWrappedWindow(g1, "New Network Entry")
        f1 = snack.Form()
        f1.add(g1)
        
        while flag:
            result = f1.run()
            if newNetwork.value() != "172.25.244.0":
                self.selector.popupStatus("Wrong Text", "You didn't type 172.25.244.0", 1)
                newNetwork.setEntry('')
                flag = 1
            else:
                self.selector.popupStatus("Wrong Text", "Valid Network!", 1)
                flag = 0
                
        return NAV_NOTHING
    
class NetworkMainWindow(ScreenActions, kusu.screens.screenfactory.BaseScreen, kusu.screens.navigator.PlatformScreen):

    title = "netedit_window_title_network"
    #name = 'Network Edit'   # used for showtrail sidebar
    msg = "netedit_instruction_network"
    buttons = [ 'new_button', 'edit_button', 'delete_button', 'quit_button' ]
    def setCallbacks(self):
        self.buttons = [self._('new_button'), self._('edit_button'), self._('delete_button'), self._('quit_button')]

        # Quit action
        self.buttonsDict[self.buttons[3]].setCallback_(self.exitAction)
        
        # New action
        self.buttonsDict[self.buttons[0]].setCallback_(self.newAction)

    def drawImpl(self):
        """ Get list of node groups and allow a user to choose one """

        # Disable Navigator 'Finish' button, since it's in wrong button order.
        self.selector.disableQuitButton()
 
        try:
            self.database.connect()
        except:
            self.finish()
            print self._("DB_Query_Error\n")
            sys.exit(-1)

        query = "SELECT netid, network, subnet, netname FROM networks"
        try:
            self.database.execute(query)
            networkInfo = self.database.fetchall()
        except:
            self.finish()
            print self._("DB_Query_Error\n")
            sys.exit(-1)

        self.screenGrid = snack.Grid(1, 2)
        instruction = snack.Textbox(80, 3, self._(self.msg), scroll=0, wrap=0)
        self.listbox = snack.Listbox(height=8, scroll=1, width=80, returnExit=1, showCursor=0)
        for nid, net,sub,netname in networkInfo:
            # If string is too long, show elipsis.
            if len(netname) > 46: 
               netname = netname[:43] + "..."

            self.listbox.append("%s %s %s" % (net.ljust(14), sub.ljust(15), netname.ljust(10)), "%s" % nid)
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0, 0, 0, 0), growx=1)
        self.screenGrid.setField(self.listbox, col=0, row=1, padding=(0, 0, 0, 0), growx=1)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        #result = self.selector.popupStatus(self._("Debug Window"), self._("Debug: %s ") % nodeGroupSelected, 1)
        return True, 'Success'

    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """
        pass

class ScreenFactoryImpl(kusu.screens.screenfactory.ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the
       Navigator(or it's child) class.
    """

    def __init__(self, screenlist):
        kusu.screens.screenfactory.ScreenFactory.screens = screenlist

if __name__ == '__main__':
    app = NetEditApp()
    app.run()
