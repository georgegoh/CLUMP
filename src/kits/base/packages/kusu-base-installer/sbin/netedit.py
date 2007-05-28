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

class NetworkData(object):
    def __init__(self):
        self.networkListbox = None
    
global dataGlobal
dataGlobal = NetworkData()
    
class NetEditApp(object, KusuApp):

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

        # Don't allow option -a -d -c to be used together. Mutually Exclusive.
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

class NetworkEditWindow(kusu.screens.screenfactory.BaseScreen, kusu.screens.navigator.PlatformScreen):
    title = "netedit_window_title_edit"
    #name = 'Network Edit'   # used for showtrail sidebar
    msg = "netedit_instruction_edit"
    buttons = [ 'ok_button', 'cancel_button' ]
    helptext = "Copyright(C) 2007 Platform Computing Inc\tInstructions: Please edit the network information"
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        kusu.screens.screenfactory.BaseScreen.__init__(self, database, kusuApp=kusuApp, gridWidth=45)
        self.noValidate = 1
    
    def hotkeyCallback(self):
        return NAV_QUIT
    
    def cancelAction(self):
        self.noValidate = 0
        return NAV_QUIT
            
    def setCallbacks(self):
        self.buttons = [ self._('ok_button'), self._('cancel_button') ]
        self.buttonsDict[self.buttons[1]].setCallback_(self.cancelAction)
    
    def guessIPandGateway(self):
        # First check if the values are valid IP address notation
        net = self.newNetwork.value()
        sub = self.newSubnet.value()
        
        if kusu.ipfun.validIP(net) and kusu.ipfun.validIP(sub):
            calcnet = kusu.ipfun.ip2number(net)
            calcsub = kusu.ipfun.ip2number(sub)
        
        # Fill in missing fields as needed
            if not self.newStartIP.value():
                # Calculate the new IP Address
                xip = (((calcsub >> 1) ^ calcsub) & 0xfffffff) | calcnet
                self.newStartIP.setEntry(kusu.ipfun.number2ip(xip))
            
            if not self.newGateway.value():
                yip = calcnet | (( ~calcsub) -1)
                self.newGateway.setEntry(kusu.ipfun.number2ip(yip))
                        
    def drawImpl(self):
        global dataGlobal
        netInfo = dataGlobal.networkListbox.current()[0]
        self.networkRecord = None   
        # Get the record to edit
        query = "SELECT network, subnet, gateway, device, startip, suffix, inc, options, netname, usingdhcp FROM networks WHERE netid = %d" % \
                int(netInfo)

        try:
            self.database.execute(query)
            self.networkRecord = list(self.database.fetchone())
        except:
            print self._("DB_Query_Error\n")
            sys.exit(-1)

        self.selector.disableQuitButton()
        self.screenGrid  = snack.Grid(1, 11)
        
        instruction = snack.Textbox(60, 1, self._("Please edit any of the network information below."), scroll=0, wrap=0)
        
        self.newNetwork= kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Network: ".rjust(13), text=self.networkRecord[0], width=30, 
                password=0, returnExit = 0)
        self.newSubnet = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Subnet: ".rjust(13), text=self.networkRecord[1], width=30, 
                    password=0, returnExit = 0)
        self.newGateway= kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Gateway: ".rjust(13), text=self.networkRecord[2], width=30, 
                    password=0, returnExit = 0)
        newDevice = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Device: ".rjust(13), text=self.networkRecord[3], width=30, 
                    password=0, returnExit = 0)
        self.newStartIP = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Starting IP: ".rjust(10), text=self.networkRecord[4], width=30, 
                    password=0, returnExit = 0)
        newSuffix = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Suffix: ".rjust(13), text=self.networkRecord[5], width=30, 
                    password=0, returnExit = 0)
        newInc = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Increment: ".rjust(13), text="%s" % self.networkRecord[6], width=30, 
                    password=0, returnExit = 0)
        newOpt = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Options: ".rjust(13), text=self.networkRecord[7], width=30, 
                    password=0, returnExit = 0, scroll=1)
        newDesc = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Description: ".rjust(10), text=self.networkRecord[8], width=30, 
                    password=0, returnExit = 0)

        dhcpCheck = snack.Checkbox("Use DHCP", isOn = int(self.networkRecord[9]))
        
        # Set hot text callback, when tabbing or moving cursor away from field, it will prepopulate other fields when needed.
        self.newNetwork.setCallback(self.guessIPandGateway)
        self.newSubnet.setCallback(self.guessIPandGateway)

        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1))
        self.screenGrid.setField(self.newNetwork, 0, 1, padding=(0,0,0,0))
        self.screenGrid.setField(self.newSubnet, 0, 2, padding=(0,0,0,0))
        self.screenGrid.setField(self.newGateway, 0, 3, padding=(0,0,0,0)) # anchorLeft=1
        self.screenGrid.setField(newDevice, 0, 4, padding=(0,0,0,0))
        self.screenGrid.setField(self.newStartIP, 0, 5, padding=(0,0,0,0))
        self.screenGrid.setField(newSuffix, 0, 6, padding=(0,0,0,0))
        self.screenGrid.setField(newInc, 0, 7, padding=(0,0,0,0))
        self.screenGrid.setField(newOpt, 0, 8, padding=(0,0,0,0))
        self.screenGrid.setField(newDesc, 0, 9, padding=(0,0,0,1))
        self.screenGrid.setField(dhcpCheck, 0, 10, padding=(0, 0, 0, -2), anchorLeft=1)
        self.popWindow()
    
    def validate(self):
        self.badFields = 0
        
        if self.noValidate:
            # Validate if the value is in IP format. 
            if not kusu.ipfun.validIP(self.newNetwork.value()): 
                #self.selector.popupStatus(self._("Debug Window"), "Validate a new network record: '%s'" % type(self.networkRecord[0]), 2)
                self.newNetwork.setEntry('')
                self.badFields  = 1
   
            if not kusu.ipfun.validIP(self.newSubnet.value()):    
                self.newSubnet.setEntry('')
                self.badFields  = 1
   
            if not kusu.ipfun.validIP(self.newGateway.value()):
                self.newGateway.setEntry('')
                self.badFields  = 1 
   
            if not kusu.ipfun.validIP(self.newStartIP.value()): 
                self.newStartIP.setEntry('')
                self.badFields  = 1
            
            if self.badFields:
                self.popWindow()
                return False, 'Some fields were invalid. Please reenter these values. They have been reset.\n\n'
        return True, 'Success'
        
class NetworkNewWindow(kusu.screens.screenfactory.BaseScreen):

    title = "netedit_window_title_new"
    #name = 'Network Edit'   # used for showtrail sidebar
    msg = "netedit_instruction_new"
    buttons = [ 'ok_button', 'cancel_button' ]
    helptext = "Copyright(C) 2007 Platform Computing Inc.\tInstructions: Please enter the new network information"
    
    def hotkeyCallback(self):
        return NAV_QUIT
        
    def cancelAction(self):
        return NAV_QUIT
    
    def guessIPandGateway(self):
        # First check if the values are valid IP address notation
        net = self.newNetwork.value()
        sub = self.newSubnet.value()

        if kusu.ipfun.validIP(net) and kusu.ipfun.validIP(sub):
            calcnet = kusu.ipfun.ip2number(net)
            calcsub = kusu.ipfun.ip2number(sub)
        
        # Fill in missing fields as needed
            if not self.newStartIP.value():
                # Calculate the new IP Address
                xip = (((calcsub >> 1) ^ calcsub) & 0xfffffff) | calcnet
                self.newStartIP.setEntry(kusu.ipfun.number2ip(xip))
            
            if not self.newGateway.value():
                yip = calcnet | (( ~calcsub) -1)
                self.newGateway.setEntry(kusu.ipfun.number2ip(yip))
                
    def setCallbacks(self):
        self.buttons = [ self._('ok_button'), self._('cancel_button') ]
        self.buttonsDict[self.buttons[0]].setCallback_(self.validate)
        self.buttonsDict[self.buttons[1]].setCallback_(self.cancelAction)

    def drawImpl(self):
    
        self.selector.disableQuitButton()
        self.screenGrid = snack.Grid(1, 11)
        instruction = snack.Textbox(60, 1, self._("Please enter the network information below."), scroll=0, wrap=0)
        self.newNetwork= kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Network: ".rjust(13), width=30, password=0, returnExit = 0)
        self.newSubnet = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Subnet: ".rjust(13), width=30, password=0, returnExit = 0)
        self.newGateway= kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Gateway: ".rjust(13), width=30, password=0, returnExit = 0)
        newDevice = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Device: ".rjust(13), width=30, password=0, returnExit = 0)
        self.newStartIP = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Starting IP: ".rjust(10), width=30, password=0, returnExit = 0)
        newSuffix = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Suffix: ".rjust(13), width=30, password=0, returnExit = 0)
        newInc = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Increment: ".rjust(13), width=30, password=0, returnExit = 0)
        newOpt = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Options: ".rjust(13), width=30, password=0, returnExit = 0, scroll=1)
        newDesc = kusu.screens.kusuwidgets.LabelledEntry(labelTxt="Description: ".rjust(10), width=30, password=0, returnExit = 0)
        dhcpCheck = snack.Checkbox("Use DHCP", isOn = 0)
        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1), growx=1, anchorLeft=1)
        self.screenGrid.setField(self.newNetwork, 0, 1, padding=(0,0,0,0))
        self.screenGrid.setField(self.newSubnet, 0, 2, padding=(0,0,0,0))
        self.screenGrid.setField(self.newGateway, 0, 3, padding=(0,0,0,0)) # anchorLeft=1
        self.screenGrid.setField(newDevice, 0, 4, padding=(0,0,0,0))
        self.screenGrid.setField(self.newStartIP, 0, 5, padding=(0,0,0,0))
        self.screenGrid.setField(newSuffix, 0, 6, padding=(0,0,0,0))
        self.screenGrid.setField(newInc, 0, 7, padding=(0,0,0,0))
        self.screenGrid.setField(newOpt, 0, 8, padding=(0,0,0,0))
        self.screenGrid.setField(newDesc, 0, 9, padding=(0,0,0,1))
        self.screenGrid.setField(dhcpCheck, 0, 10, padding=(0, 0, 0, -2), anchorLeft=1)
        
        # Set hot text callback, when tabbing or moving cursor away from field, it will prepopulate other fields when needed.
        self.newNetwork.setCallback(self.guessIPandGateway)
        self.newSubnet.setCallback(self.guessIPandGateway)
        
    def checkForm(self):
        self.selector.popupStatus(self._("Debug Window"), "Validate a new network record", 1)
        return True, 'Success'

class NetworkMainWindow(kusu.screens.screenfactory.BaseScreen, kusu.screens.navigator.PlatformScreen):

    title = "netedit_window_title_network"
    #name = 'Network Edit'   # used for showtrail sidebar
    msg = "netedit_instruction_network"
    buttons = [ 'new_button', 'edit_button', 'delete_button', 'quit_button' ]

    def __init__(self, database, kusuApp=None, gridWidth=45):
        self.kusuApp = KusuApp()
        kusu.screens.screenfactory.BaseScreen.__init__(self, database, kusuApp=self.kusuApp, gridWidth=45)
        self.buttons = [self._('new_button'), self._('edit_button'), self._('delete_button'), self._('quit_button')]

    def hotkeyCallback(self):
        self.exitAction()
        
    def newAction(self, data=None):
        kusu.screens.screenfactory.ScreenFactory.screens = \
                        [ NetworkNewWindow(self.database, self.kusuApp) ]
                        
        ks = kusu.screens.navigator.Navigator(screenFactory=kusu.screens.screenfactory.ScreenFactory,screentitle="Network Edit - Version 5.0", showTrail=False)
        ks.run()
        return NAV_NOTHING    
    
    def editAction(self, data=None):
        kusu.screens.screenfactory.ScreenFactory.screens = \
                        [ NetworkEditWindow(self.database, self.kusuApp) ]
                        
        ks = kusu.screens.navigator.Navigator(screenFactory=kusu.screens.screenfactory.ScreenFactory,screentitle="Network Edit - Version 5.0", showTrail=False)
        ks.run()
        return NAV_NOTHING
    
    def deleteAction(self, data=None):
        self.database.connect('kusudb', 'apache')
        # Check if the network selected is not in use.
        netuse = 0
        global dataGlobal
        netInfo = dataGlobal.networkListbox.current().split()
        query = "SELECT COUNT(*) FROM ng_has_net WHERE netid = %d" % int(netInfo[0])

        try:
            self.database.execute(query)
            netuse = self.database.fetchone()[0]
        except: 
            self.finish()
            print self._("DB_Query_Error\n")
            sys.exit(-1)

        if int(netuse) == 0:
            # Prompt for delete dialog.
            result = self.selector.popupDialogBox(self._("netedit_window_title_delete"), 
                    self._("Do you want to delete the network '%s'?") % netInfo[1], (self._("yes_button"), self._("no_button")))
            if result == "no":
                return NAV_NOTHING
            if result == "yes":
                self.database.execute("DELETE FROM networks WHERE netid = %d" % int(netInfo[0]))
                return NAV_NOTHING
        else:
            self.selector.popupMsg(self._("netedit_window_title_delete"), 
            self._("The Network '%s' is in use. If you wish to delete this, please use the node group editor.\n\n" % netInfo[1]))
            return NAV_NOTHING
            
    def exitAction(self, data=None):
        """ExitAction()
        Function Callback - Will pop up a quit dialog box if new nodes were added, otherwise quits without prompt
        """

        result = self.selector.popupDialogBox(self._("netedit_window_title_exit"), self._("netedit_instructions_exit"), 
                 (self._("yes_button"), self._("no_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            self.finish()
            sys.exit(0)
        else:
            return NAV_NOTHING
        
    def setCallbacks(self):
        # Edit action
        self.buttonsDict[self.buttons[0]].setCallback_(self.newAction)
        self.buttonsDict[self.buttons[1]].setCallback_(self.editAction) 
        self.buttonsDict[self.buttons[2]].setCallback_(self.deleteAction)
        self.buttonsDict[self.buttons[3]].setCallback_(self.exitAction)
        
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

        query = "SELECT netid, network, subnet, netname FROM networks ORDER BY netid"
        try:
            self.database.execute(query)
            networkInfo = self.database.fetchall()
        except:
            self.finish()
            print self._("DB_Query_Error\n")
            return
            sys.exit(-1)

        self.screenGrid = snack.Grid(1, 2)
        instruction = snack.Textbox(80, 3, self._(self.msg), scroll=0, wrap=0)
        dataGlobal.networkListbox = snack.Listbox(height=8, scroll=1, width=80, returnExit=1, showCursor=0)
        for nid, net,sub,netname in networkInfo:
            # If string is too long, show ellipsis.
            if len(netname) > 46: 
               netname = netname[:43] + "..."

            dataGlobal.networkListbox.append("%s %s %s" % (net.ljust(14), sub.ljust(15), netname.ljust(10)), "%s %s" % (nid, net))
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0, 0, 0, 0), growx=1)
        self.screenGrid.setField(dataGlobal.networkListbox, col=0, row=1, padding=(0, 0, 0, 0), growx=1)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""
        return True, 'Success'

class ScreenFactoryImpl(kusu.screens.screenfactory.ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the
       Navigator(or it's child) class.
    """

    def __init__(self, screenlist):
        kusu.screens.screenfactory.ScreenFactory.screens = screenlist

if __name__ == '__main__':
    app = NetEditApp()
    app.run()

