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

import sys
import os
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
import snack
from kusu.ui.text.USXscreenfactory import USXBaseScreen
from kusu.ui.text.USXnavigator import *
from kusu.ui.text.screenfactory import ScreenFactory
from kusu.ui.text.kusuwidgets import *
from kusu.util.errors import UserExitError
import kusu.ipfun

global selectedNetwork
selectedNetwork = None

global networkInUse
networkInUse = False

global database
global kusuApp
database = KusuDB()
kusuApp = KusuApp()
        
class NetworkRecord(object):        
    def __init__(self, networkentryinfo=None, windowInstance=None):
    
        if networkentryinfo:
            self._network_field = networkentryinfo[0]
            self._subnet_field = networkentryinfo[1]
            self._gateway_field = networkentryinfo[2]
            self._startip_field = networkentryinfo[3]
            self._inc_field = networkentryinfo[4]
            self._device_field = networkentryinfo[5]
            self._suffix_field = networkentryinfo[6]
            self._option_field = networkentryinfo[7]
            self._description_field = networkentryinfo[8]
            self._dhcp_checkbox = networkentryinfo[9]
            self._type_field = networkentryinfo[10]
    
        if windowInstance:
            self._thisWindow = windowInstance
            self._ = self._thisWindow.kusuApp._  # get i18n handle.
        else:
            self._thisWindow = None
        self._database = KusuDB()
       
    def validateIPAddress(self, ip, network, subnet):
        if kusu.ipfun.validIP(ip):
           if kusu.ipfun.onNetwork(network, subnet, ip):
                 return True
           else:
                 return False
        else:
           return False
  
    def validateNetworkEntry(self):
        # Validate if the value is in IP format. 

        if self._thisWindow:
           if self._thisWindow.dhcpCheck.value() == False:
              if not kusu.ipfun.validIP(self._network_field):
                 self._thisWindow.networkEntry.setEntry('')
                 return False, 'netedit_validate_network'
        else:
           if not kusu.ipfun.validIP(self._network_field):
              return False, 'netedit_validate_network'
         
        if self._thisWindow:
           if self._thisWindow.dhcpCheck.value() == False:
              if not kusu.ipfun.validIP(self._subnet_field):
                 self._thisWindow.subnetEntry.setEntry('')
                 return False, 'netedit_validate_subnet'
        else:
           if not kusu.ipfun.validIP(self._subnet_field):
              return False, 'netedit_validate_subnet'
   
        if self._gateway_field:
            if not kusu.ipfun.validIP(self._gateway_field):
                if not self._network_field and not self._subnet_field and self._thisWindow:
                   self._thisWindow.gatewayEntry.setEntry('')
                   return False, 'netedit_validate_gateway'
 
        if self._thisWindow:
           if self._thisWindow.dhcpCheck.value() == False:
              if not kusu.ipfun.validIP(self._startip_field):
                 if not self._network_field and not self._subnet_field:
                    self._thisWindow.startIPEntry.setEntry('')
                    return False, 'netedit_validate_startip'
        else:
             if not kusu.ipfun.validIP(self._startip_field):
                 if not self._network_field and not self._subnet_field:
                    return False, 'netedit_validate_startip'
            
        # Check if the Increment is a number.
        try:
            result = int(self._inc_field)
            if result == 0:
               if self._thisWindow:
                   if self._thisWindow.dhcpCheck.value() == False:
                      self._thisWindow.incEntry.setEntry('')
                   return False, 'netedit_validate_inc_not_zero'
               else:
                   return False, 'netedit_validate_inc_not_zero'
             
        except:
            if len(self._inc_field) == 0:
               if self._thisWindow and self._thisWindow.dhcpCheck.value() == False:
                  self._thisWindow.incEntry.setEntry('')
                  return False, 'netedit_validate_inc_not_empty'
               else:
                  return False, 'netedit_validate_inc_not_number'
            
        # Device field cannot be empty.
        if not self._device_field:
            return False, 'netedit_validate_device'
          
        if not self._description_field:
            return False, 'netedit_validate_description'

        # Validate if IP and gateway exist on the new network entered.        
        if not self._network_field == "" and not self._gateway_field == "": # If no gateway specified, don't bother to validate it.
           if not kusu.ipfun.onNetwork(self._network_field, self._subnet_field, self._gateway_field):
              return False, 'netedit_validate_gateway_on_network'


        if self._thisWindow:
           if self._thisWindow.dhcpCheck.value() == False:
              if not self._subnet_field == "":
                 if not kusu.ipfun.onNetwork(self._network_field, self._subnet_field, self._startip_field):
                    return False, 'netedit_validate_startip_on_network'
        else:
              if not kusu.ipfun.onNetwork(self._network_field, self._subnet_field, self._startip_field):
                 return False, 'netedit_validate_startip_on_network'

        # Check if DHCP mode is on
        if self._thisWindow.dhcpCheck.value() == True:
           if self._network_field or self._subnet_field or self._gateway_field or self._startip_field:
              return False, 'Cannot specify Network, Subnet, Gateway or Starting IP when using DHCP'

        return True, 'Success'
                    
    def updateNetworkEntry(self, currentItem):
        query = "UPDATE networks SET network='%s',subnet='%s',device='%s',suffix='%s',gateway='%s',options='%s',netname='%s', \
                 startip='%s',inc=%d,usingdhcp=%d,type='%s' WHERE netid=%d" % (self._network_field, self._subnet_field, \
                 self._device_field, self._suffix_field, self._gateway_field, self._option_field, \
                 self._description_field, self._startip_field, int(self._inc_field), \
                 int(self._dhcp_checkbox), self._type_field, int(currentItem))
        try:
           self._database.connect('kusudb', 'apache')
           self._database.execute(query)
           return True, 'Success'
        except:
           if self._thisWindow:
              return False, 'DB_Query_Error\n'
           else:
              print kusuApp._("DB_Query_Error\n")
              kusuApp.unlock()
              sys.exit(-1)
        return True, 'Success'
       
    def insertNetworkEntry(self):

        if not self._inc_field:
           self._inc_field = 1

        if not self._subnet_field and not self._network_field and not self._startip_field:
           query = "INSERT INTO networks (device, suffix, options, netname, inc, usingdhcp, type) VALUES \
                ('%s', '%s', '%s', '%s', '%d', '%d', '%s')" % (self._device_field, self._suffix_field, self._option_field, \
                self._description_field, 1, 1, self._type_field)
        else:
           query = "INSERT INTO networks (network, subnet, device, suffix, gateway, options, netname, startip, inc, usingdhcp, type) VALUES \
                ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%d', '%d', '%s')" % (self._network_field, \
                self._subnet_field, self._device_field, self._suffix_field, self._gateway_field, self._option_field, \
                self._description_field, self._startip_field, int(self._inc_field), int(self._dhcp_checkbox), self._type_field)
        try:
           self._database.connect('kusudb', 'apache')
           self._database.execute(query)
           return True, 'Success'
        except:
            if self._thisWindow:
                #self._thisWindow.screen.finish()
                return False, 'DB_Duplicate_Error\n'
            else:
                print kusuApp._("DB_Duplicate_Error\n")
                kusuApp.unlock()
                sys.exit(-1)
        
    def checkNetworkEntry(self, networkid):
        # Check if the network selected is not in use.
        netuse = 0
        query = "SELECT COUNT(*) FROM ng_has_net WHERE netid = %d" % int(networkid)
        try:
           self._database.connect('kusudb', 'apache')
           self._database.execute(query)
           netuse = self._database.fetchone()[0]
        except:
           if self._thisWindow:
              #self._thisWindow.screen.finish()
              print kusuApp._("DB_Query_Error\n")
              raise UserExitError
           else:
              print kusuApp._("DB_Query_Error\n")
              self.unlock()
              sys.exit(-1)
            
        if int(netuse) >= 1:
                return True
        else:
            return False
            
    def getNetworkList(self):   
        networkInfo = None
        query = "SELECT netid, network, subnet, netname, device, type FROM networks ORDER BY netid"
        try:
           self._database.connect()
           self._database.execute(query)
           networkInfo = self._database.fetchall()
           return networkInfo
        except:
           if self._thisWindow:
              self._thisWindow.screen.finish()
              print kusuApp._("DB_Query_Error\n")
              raise UserExitError
           else:
              print kusuApp._("DB_Query_Error\n")
              self.unlock()
              sys.exit(-1)
    
class NetEditApp(object, KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

    def toolVersion(self, option, opt, value, parser):
        """ 
        toolVersion()
        Prints out the version of the tool to screen. 
        """

        print "Netedit Version %s\n" % self.version
        self.unlock()
        sys.exit(0)

    def parseargs(self):
        """
        parseargs()
        Parse the command line arguments. """

        global database

        self.parser.add_option("-v", "--version", action="callback",
                                callback=self.toolVersion, help=self._("netedit_version_usage"))
        self.parser.add_option("-l", "--list-networks", action="store_true",
                                dest="listnetworks", help=self._("netedit_listnetworks_usage"))
        self.parser.add_option("-d", "--delete", action="store",
                                type="int", dest="delete", help=self._("netedit_delete_usage"))
        self.parser.add_option("-a", "--add", action="store_true",
                                dest="add", help=self._("netedit_add_usage"))
        self.parser.add_option("-c", "--change", action="store",
                                type="int", dest="change", help=self._("netedit_change_usage"))

        self.parser.add_option("-n", "--network", action="store", dest="network", help=self._("netedit_network_usage"))
        self.parser.add_option("-s", "--subnet", action="store", dest="subnet", help=self._("netedit_subnet_usage"))
        self.parser.add_option("-i", "--interface", action="store", dest="interface", help=self._("netedit_interface_usage"))
        self.parser.add_option("-r", "--increment", action="store", type="int", dest="increment", help=self._("netedit_increment_usage"))
        self.parser.add_option("-t", "--starting-ip", action="store", dest="startip", help=self._("netedit_startip_usage"))
        self.parser.add_option("-x", "--name-suffix", action="store", dest="suffix", help=self._("netedit_suffix_usage"))
        self.parser.add_option("-g", "--gateway", action="store", dest="gateway", help=self._("netedit_gateway_usage"))
        self.parser.add_option("-o", "--options", action="store", dest="opt", help=self._("netedit_options_usage"))
        self.parser.add_option("-e", "--description", action="store", dest="desc", help=self._("netedit_description_usage"))
        self.parser.add_option("-p", "--dhcp", action="store_true", dest="dhcp", help=self._("netedit_dhcp_usage"))
        self.parser.add_option("-w", "--change-used-network", action="store",
                               type="int", dest="changeused", help=self._("netedit_changeused_usage"))
        self.parser.add_option("-y", "--provision-type", action="store_true", dest="provision", help=self._("netedit_provision_usage"))
        self.parser.add_option("-z", "--public-type", action="store_true", dest="public", help=self._("netedit_public_usage"))
        (self._options, self._args) = self.parser.parse_args(sys.argv[1:])

    def nxor(self, *args):
        """nxor(varargs args)
        N-way function, only one condition may be true otherwise false. """

        return len([x for x in args if x]) == 1

    def run(self):
        """run()
        Run the application """
        global database

        if os.geteuid() != 0:
            print self._("nonroot_execution\n")
            sys.exit(-1)

        if self.islock():
           print self._("netedit_already_inuse")
           sys.exit(-1)
        
        # Parse command options
        self.parseargs()

        self.lock()

        # Don't allow option -a -d -c -l to be used together. Mutually Exclusive.
        if (not self.nxor(bool(self._options.add), bool(self._options.delete), bool(self._options.change), bool(self._options.listnetworks))):
                    if (bool(self._options.add) == False and bool(self._options.delete) == False and bool(self._options.change) == False \
                    and bool(self._options.listnetworks) == False):
                        pass
                    else:
		        self.unlock()
                        self.parser.error(self._("netedit_options_exclusive"))

        # Non required values, if not set default to these
        if bool(self._options.increment) == False:  # and bool(self._options.change) == False
            self._options.increment = 1
        
        if not self._options.suffix:
            self._options.suffix = ""
                            
        if not self._options.opt:
            self._options.opt = ""
            
        if not self._options.gateway:
            self._options.gateway = ""
            
        if not bool(self._options.dhcp):
           self._options.dhcp = False
        else:
           self._options.dhcp = True

        # Handle -l option
        if self._options.listnetworks:
            netrec = NetworkRecord()
            networkList = netrec.getNetworkList()
            print 

            netid_field = self._("netedit_list_networkid_field")
            network_field = self._("netedit_list_network_field")
            subnet_field = self._("netedit_list_subnet_field")
            desc_field = self._("netedit_list_description_field")
            dev_field = self._("netedit_list_device_field")
            type_field = self._("netedit_interface_label")
            print "%s %s %s %s %s %s" % (netid_field.ljust(10), dev_field.ljust(12), network_field.ljust(13), subnet_field.ljust(15),desc_field.ljust(40), type_field)

            print "%s".ljust(3) % (("=") * len(netid_field)) + "%s".ljust(9) % (("=") * len(dev_field)) + "%s".ljust(9) % (("=") * \
                  len(network_field)) + "%s".ljust(12) % (("=") * len(subnet_field)) + "%s".ljust(24) % (("=") * len(desc_field)) + "%s" % (("=") * len(type_field))

            for nid,net,sub,netname,devname,type in networkList:
                if not net:
                   net = "DHCP"
                if not sub:
                   sub = "DHCP"

                print "%s %s %s %s %s %s" % (str(nid).ljust(10), devname.ljust(12), net.ljust(13), sub.ljust(15), netname.ljust(40), type)
            self.unlock()
            sys.exit(0)
            
        # Handle Adding a network with DHCP is turned OFF
        # Handle -a, -n -s, -i, -t, -e options - Adding network
        if (self._options.add and self._options.network and self._options.subnet and self._options.startip and self._options.interface and self._options.desc):
            nettype = None
            # Next verify the record
            networkEntryInfo = []

            networkEntryInfo.append(self._options.network.strip())
            networkEntryInfo.append(self._options.subnet.strip())
            networkEntryInfo.append(self._options.gateway.strip())
            networkEntryInfo.append(self._options.startip.strip())
            networkEntryInfo.append(self._options.increment)
            networkEntryInfo.append(self._options.interface.strip())
            networkEntryInfo.append(self._options.suffix.strip())
            networkEntryInfo.append(self._options.opt.strip())

            if len(self._options.desc.strip()) == 0:
               self.unlock()
               self.parser.error(self._("netedit_missing_description"))
            else:
               networkEntryInfo.append(self._options.desc.strip())

            networkEntryInfo.append(int(self._options.dhcp))

            # Check for conflicting options:
            if self._options.provision and self._options.public:
               self.unlock()
               self.parser.error(self._("netedit_provision_conflict"))

            if self._options.provision:
               nettype = 'provision'

            if self._options.public:
               nettype = 'public'

            if not nettype:
               nettype = 'provision'

            networkEntryInfo.append(nettype)
            
            networkrecord = NetworkRecord(networkEntryInfo, None)            
            result, errorMsg = networkrecord.validateNetworkEntry()
            if not result: 
                self.unlock()
                self.parser.error(self._(errorMsg))

            networkrecord.insertNetworkEntry()
            self.unlock()
            sys.exit(0)

        # DHCP Mode
        if self._options.add and self._options.dhcp and self._options.interface and self._options.desc:
           nettype = None
           networkEntryInfo = []

           networkEntryInfo.append(None)
           networkEntryInfo.append(None)
           networkEntryInfo.append(None)
           networkEntryInfo.append(None)
           networkEntryInfo.append(self._options.increment)
           networkEntryInfo.append(self._options.interface.strip())
           networkEntryInfo.append(self._options.suffix.strip())
           networkEntryInfo.append(self._options.opt.strip())
           #result, errorMsg = networkrecord.validateNetworkEntry()

           if self._options.subnet or self._options.network or self._options.startip or self._options.gateway:
              print "When using DHCP, you cannot specify a subnet, network, starting ip or gateway\n"
              self.unlock()
              sys.exit(-1)

           if len(self._options.desc.strip()) == 0:
              self.unlock()
              self.parser.error(self._("netedit_missing_description"))
           else:
              networkEntryInfo.append(self._options.desc.strip())

           networkEntryInfo.append(True)

           # Check for conflicting options:
           if self._options.provision and self._options.public:
              self.unlock()
              self.parser.error(self._("netedit_provision_conflict"))

           if self._options.provision:
              nettype = 'provision'

           if self._options.public:
              nettype = 'public'

           if not nettype:
              nettype = 'public'

           networkEntryInfo.append(nettype)

           networkrecord = NetworkRecord(networkEntryInfo, None)
           networkrecord.insertNetworkEntry()
           self.unlock()
           sys.exit(0)
        elif self._options.add == True:
           if not self._options.network or not self._options.subnet or not self._options.interface or not self._options.gateway \
                or not self._options.startip or not self._options.desc and not self._options.dhcp == True:
               self.unlock()
               self.parser.error(self._("netedit_options_add_options_needed"))

        # Handle -d  - Deleting network
        if (self._options.delete):
            result = None
            invalidID = True
            networkrecord = NetworkRecord()
            networkInfo = list(networkrecord.getNetworkList())
            for network in networkInfo:
                if network[0] == self._options.delete:
                    invalidID = False
                    # We found this ID, let's check if it's in use or not.
                    result = networkrecord.checkNetworkEntry(self._options.delete)
                    if result:
                        print self._("The network '%s' is in use. If you wish to delete this, please use the node group editor\n" % network[1])
                        self.unlock()
                        sys.exit(0)
                    else:
                        try:
                            database.connect('kusudb', 'apache')
                            database.execute("DELETE FROM networks WHERE netid = %d" % int(self._options.delete))
                            if not network[1]:
                               print self._("Deleting DHCP network: %s\n" % self._options.delete)
                            else:
                               print self._("Deleting network: %s\n" % network[1])

                        except:
                            print self._("DB_Query_Error\n")
                            self.unlock()
                            sys.exit(-1)
            if invalidID: 
                self.unlock()
                self.parser.error(self._("netedit_error_invalid_id"))
            self.unlock()
            sys.exit(0)

        # Handle -w: -t|-e|-r|-o|-y|-z - Changing non-destructive values
        if (self._options.changeused):
            database.connect('kusudb', 'apache')
            if (self._options.startip or self._options.desc or self._options.opt or self._options.increment or self._options.public or self._options.provision) and not (self._options.network or self._options.subnet or self._options.gateway or self._options.interface or self._options.dhcp):

                # Check for conflicting options:
                if self._options.provision and self._options.public:
                   self.unlock()
                   self.parser.error(self._("netedit_options_conflict_type"))
 
                networkrecord = NetworkRecord()
                networkInfo = list(networkrecord.getNetworkList())
                invalidID = True
                for network in networkInfo:
                    if network[0] == self._options.changeused:
                       invalidID = False
                       database.connect('kusudb', 'apache')
                       # Get the node group's network and subnet for the specified ID.
                       database.execute("SELECT networks.network, networks.subnet FROM networks WHERE netid = %d" % int(self._options.changeused))
                       changeinfo = database.fetchone()

                       if self._options.startip:
                          if networkrecord.validateIPAddress(self._options.startip.strip(), changeinfo[0], changeinfo[1]):
                             database.execute("UPDATE networks SET startip = '%s' WHERE netid = %d" % (self._options.startip.strip(), int(self._options.changeused)))
                          else:
                             self.unlock()
                             self.parser.error(self._("netedit_validate_startip"))
                        
                       if self._options.desc:
                          if len(self._options.desc.strip()) > 0:
                             database.execute("UPDATE networks SET netname = '%s' WHERE netid = %d" % (self._options.desc.strip(), int(self._options.changeused)))
                          else:
                             self.unlock()
                             self.parser.error(self._("netedit_empty_description"))

                       if self._options.opt:
                          database.execute("UPDATE networks SET options = '%s' WHERE netid = %d" % (self._options.opt.strip(), int(self._options.changeused)))

                       if self._options.increment:
                          changeflag = 1
                          database.execute("UPDATE networks SET inc = %d WHERE netid =%d" % (self._options.increment, int(self._options.changeused)))

                       if self._options.provision:
                          #print "Changing Network to 'provision'"
                          database.execute("UPDATE networks SET type = '%s' WHERE netid =%d" % ('provision', int(self._options.changeused)))
                       if self._options.public:
                          #print "Changing Network to 'public'"
                          database.execute("UPDATE networks SET type = '%s' WHERE netid =%d" % ('public', int(self._options.changeused)))
   
                if invalidID:
                   self.unlock()
                   self.parser.error(self._("netedit_error_invalid_id"))

                self.unlock()
                sys.exit(0)

            else:
                 self.unlock()
                 self.parser.error(self._("netedit_options_illegal_usednetwork"))

        if (self._options.change):
            # Handle -c, -n, -s, -g, -t, -i, -e (minimal options) - Changing network - Destructive
            # Check whole network if it's not in use
            if (self._options.network and self._options.subnet and self._options.startip and self._options.gateway and self._options.interface and self._options.desc):

                # Check for conflicting options:
                if self._options.provision and self._options.public:
                   self.unlock()
                   self.parser.error(self._("netedit_options_conflict_type"))

                result = None
                invalidID = True
                networkrecord = NetworkRecord()
                networkInfo = list(networkrecord.getNetworkList())
                for network in networkInfo:
                    if network[0] == self._options.change:
                        invalidID = False
                        # We found this ID, let's check if it's in use or not.
                        result = networkrecord.checkNetworkEntry(self._options.change)

                        if result:
                           self.unlock()
                           self.parser.error(self._("The network '%s' is in use. To change non-destructive properties use the -w option") % network[1])
                        else:
                            # First, validate the record we want to replace.
                            networkEntryInfo = []
                            networkEntryInfo.append(self._options.network.strip())
                            networkEntryInfo.append(self._options.subnet.strip())
                            networkEntryInfo.append(self._options.gateway.strip())
                            networkEntryInfo.append(self._options.startip.strip())
                            networkEntryInfo.append(self._options.increment)
                            networkEntryInfo.append(self._options.interface.strip())
    
                            # If user didn't specify suffix 'guess it'
                            if not self._options.suffix:
                               self._options.suffix = "-%s" % self._options.interface.strip()

                            networkEntryInfo.append(self._options.suffix.strip())
                            networkEntryInfo.append(self._options.opt.strip())
                            networkEntryInfo.append(self._options.desc.strip())
                            networkEntryInfo.append(int(self._options.dhcp))
                             
                            if self._options.provision:
                               networkEntryInfo.append('provision')
                            if self._options.public:
                               networkEntryInfo.append('public')

                            if not self._options.public or self._options.provision:
                               networkEntryInfo.append('provision')

                            del networkrecord
                            networkrecord = NetworkRecord(networkEntryInfo, None)
                            result, errorMsg = networkrecord.validateNetworkEntry()
                            if not result:
                                    self.unlock()
                                    self.parser.error(self._(errorMsg))
                                    
                            networkrecord.updateNetworkEntry(self._options.change) 
                            self.unlock()
                            sys.exit(0)
                        
                if invalidID:
                    self.unlock()
                    self.parser.error(self._("netedit_error_invalid_id"))

            else:
                self.unlock()
                self.parser.error(self._("netedit_options_change_options_needed"))
        
        if len(sys.argv[1:]) > 0:
            if (not bool(self._options.add) or not self._options.delete or not bool(self._options.change)):
                self.unlock()
                self.parser.error(self._("netedit_options_required_options"))
                
        # Screen ordering
        screenList = [ NetworkMainWindow(database=database, kusuApp=kusuApp) ]

        screenFactory = ScreenFactoryImpl(screenList)
        ks = USXNavigator(screenFactory=screenFactory, screenTitle="Network Edit - Version 5.0", showTrail=False)
        ks.run()
        self.unlock()

class NetworkEditWindow(USXBaseScreen):
    name = "netedit_window_title_edit"
    msg = "netedit_instruction_edit"
    buttons = [ 'ok_button', 'cancel_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.hasGateway = None
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.\t%s" % self.kusuApp._("helpline_instructions"))
    
    def okAction(self):
        return NAV_FORWARD
        
    def cancelAction(self):
        return NAV_QUIT
            
    def setCallbacks(self):
        
        self.buttonsDict['ok_button'].setCallback_(self.okAction)
        self.buttonsDict['cancel_button'].setCallback_(self.cancelAction)
    
        self.hotkeysDict['F5'] = self.cancelAction
        self.hotkeysDict['F8'] = self.okAction
        
    def guessIPandGateway(self):
        # First check if the values are valid IP address notation
        net = self.networkEntry.value()
        sub = self.subnetEntry.value()
        
        if kusu.ipfun.validIP(net) and kusu.ipfun.validIP(sub):
            calcnet = kusu.ipfun.ip2number(net)
            calcsub = kusu.ipfun.ip2number(sub)
        
        # Fill in missing fields as needed
            if not self.startIPEntry.value():
                # Calculate the new IP Address
                xip = (((calcsub >> 1) ^ calcsub) & 0xfffffff) | calcnet
                self.startIPEntry.setEntry(kusu.ipfun.number2ip(xip))
            
            if self.hasGateway:
                if not self.gatewayEntry.value():
                    yip = calcnet | (( ~calcsub) -1)
                    self.gatewayEntry.setEntry(kusu.ipfun.number2ip(yip))
                
    def guessDeviceSuffix(self):
        # Get the value of the device name.
        dev = self.deviceEntry.value()
        
        if not self.suffixEntry.value():
            if not dev == "":
                # Generate new suffix based on device name.
                self.suffixEntry.setEntry("-%s" % dev)
    
    def drawImpl(self):
        global selectedNetwork
        global networkInUse
        self.networkRecord = None
        # Get the record to edit
        self.database.connect()

        query = "SELECT network, subnet, gateway, device, startip, suffix, inc, options, netname, usingdhcp, type FROM networks WHERE netid = %d" % \
                int(selectedNetwork)

        try:
            self.database.execute(query)
            self.networkRecord = list(self.database.fetchone())
        except:
            self.screen.finish()
            print self.kusuApp._("DB_Query_Error\n")
            self.unlock()
            sys.exit(-1)
            

        self.screenGrid  = snack.Grid(1, 13)
        
        instruction = snack.Textbox(60, 1, self.kusuApp._("netedit_instruction_edit"), scroll=0, wrap=0)
        self.typeLabel = snack.Label(self.kusuApp._("netedit_interface_label"))
        self.typeList = snack.Listbox(height=2, scroll=0, width=15, returnExit=0, showCursor=0)
      
        if self.networkRecord[7] == None:
           self.networkRecord[7] = ""

        if networkInUse:
           enableFlag = False
        else:
           enableFlag = True

        if self.networkRecord[0] == None:
           self.networkRecord[0] = ""
        
        self.networkEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_network").rjust(13), text=self.networkRecord[0], width=30, 
                password=0, returnExit = 0)
        self.networkEntry.setEnabled(enableFlag)

        if self.networkRecord[1] == None:
           self.networkRecord[1] = ""

        self.subnetEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_subnet").rjust(13), text=self.networkRecord[1], width=30, 
                    password=0, returnExit = 0)
        self.subnetEntry.setEnabled(enableFlag)

        if self.networkRecord[2] == None:
           self.networkRecord[2] = ""

        self.gatewayEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_gateway").rjust(13), text=self.networkRecord[2], width=30, 
                    password=0, returnExit = 0)
        self.gatewayEntry.setEnabled(enableFlag)
        
        self.deviceEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_device").rjust(13), text=self.networkRecord[3], width=30, 
                    password=0, returnExit = 0)
        self.deviceEntry.setEnabled(enableFlag)

        if self.networkRecord[4] == None:
           self.networkRecord[4] = ""

        self.startIPEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_startip").rjust(10), text=self.networkRecord[4], width=30, 
                    password=0, returnExit = 0)

        self.suffixEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_suffix").rjust(13), text=self.networkRecord[5], width=30, 
                    password=0, returnExit = 0)
        self.suffixEntry.setEnabled(enableFlag)

        self.incEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_increment").rjust(13), text="%s" % self.networkRecord[6], width=30, 
                    password=0, returnExit = 0)

        self.optionEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_options").rjust(13), text=self.networkRecord[7], width=30, 
                    password=0, returnExit = 0, scroll=1)

        self.descEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_description").rjust(10), text=self.networkRecord[8], width=30, 
                    password=0, returnExit = 0)

        self.typeList.append("public","public")
        self.typeList.append("provision","provision")

        if self.networkRecord[10] == "provision":
           self.typeList.setCurrent("provision")
        else:
           self.typeList.setCurrent("public")

        self.dhcpCheck = snack.Checkbox(self.kusuApp._("netedit_field_dhcp"), isOn = int(self.networkRecord[9]))

        if networkInUse:
           self.dhcpCheck.setFlags(snack.FLAG_DISABLED, snack.FLAGS_SET)
        else:
           self.dhcpCheck.setFlags(snack.FLAG_DISABLED, snack.FLAGS_RESET)

        # Set hot text callback, when tabbing or moving cursor away from field, it will prepopulate other fields when needed.
        if not self.networkRecord[2] == "":  # If there was no gateway set, don't force one on the user.
            self.hasGateway = False
            
        self.networkEntry.setCallback(self.guessIPandGateway)
        self.subnetEntry.setCallback(self.guessIPandGateway)
        self.deviceEntry.setCallback(self.guessDeviceSuffix)
        
        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1))
        self.screenGrid.setField(self.networkEntry, 0, 1, padding=(0,0,0,0))
        self.screenGrid.setField(self.subnetEntry, 0, 2, padding=(0,0,0,0))
        self.screenGrid.setField(self.gatewayEntry, 0, 3, padding=(0,0,0,0)) # anchorLeft=1
        self.screenGrid.setField(self.deviceEntry, 0, 4, padding=(0,0,0,0))
        self.screenGrid.setField(self.startIPEntry, 0, 5, padding=(0,0,0,0))
        self.screenGrid.setField(self.suffixEntry, 0, 6, padding=(0,0,0,0))
        self.screenGrid.setField(self.incEntry, 0, 7, padding=(0,0,0,0))
        self.screenGrid.setField(self.optionEntry, 0, 8, padding=(0,0,0,0))
        self.screenGrid.setField(self.descEntry, 0, 9, padding=(0,0,0,0))
        self.screenGrid.setField(self.dhcpCheck, 0, 10, padding=(8, 1, 0, 0), anchorLeft=1)
        self.screenGrid.setField(self.typeLabel, 0, 11, padding=(-2,-1,0,0))
        self.screenGrid.setField(self.typeList, 0, 12, padding=(0,0,0,-1))

    
    def validate(self):

        networkEntryInfo = []
        networkEntryInfo.append(self.networkEntry.value().strip())
        networkEntryInfo.append(self.subnetEntry.value().strip())
        if self.gatewayEntry:
           networkEntryInfo.append(self.gatewayEntry.value().strip())
        else:
           networkEntryInfo.append(None)

        if self.startIPEntry:
           networkEntryInfo.append(self.startIPEntry.value().strip())
        else:
           networkEntryInfo.append(None)

        networkEntryInfo.append(self.incEntry.value().strip())
        networkEntryInfo.append(self.deviceEntry.value().strip())
        networkEntryInfo.append(self.suffixEntry.value().strip())
        networkEntryInfo.append(self.optionEntry.value().strip())

        if self.descEntry.value() == "":
           networkEntryInfo.append("") 
        else:
           networkEntryInfo.append(self.descEntry.value())

        networkEntryInfo.append(self.dhcpCheck.value())
        networkEntryInfo.append(self.typeList.current())
            
        modifiedRecord = NetworkRecord(networkEntryInfo, self)
        
        result, errorMsg = modifiedRecord.validateNetworkEntry()
        # Validate if the value is in IP format. 
        if not result:
            #self.popWindow()
            return False, self.kusuApp._(errorMsg)  
        
        # Validate if DHCP is unchecked subnet/network must be filled out!
        if self.dhcpCheck.value() == False:
           if len(self.networkEntry.value()) < 1 or len(self.subnetEntry.value()) < 1:
              return False, "ERROR: Cannot have subnet and network empty when not using DHCP!"

        global selectedNetwork
        result, errorMsg = modifiedRecord.updateNetworkEntry(selectedNetwork)            
        if not result:
           return False, self.kusuApp._(errorMsg)

        return True, 'Success'
        
class NetworkNewWindow(USXBaseScreen):

    name = "netedit_window_title_new"
    msg = "netedit_instruction_new"
    buttons = [ 'ok_button', 'cancel_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2007 Platform Computing Inc.\t%s" % self.kusuApp._("helpline_instructions"))
                
    def okAction(self):
        return NAV_FORWARD
        
    def cancelAction(self):
        return NAV_QUIT
   
    def guessIPandGateway(self):
        # First check if the values are valid IP address notation
        net = self.networkEntry.value()
        sub = self.subnetEntry.value()

        if kusu.ipfun.validIP(net) and kusu.ipfun.validIP(sub):
            calcnet = kusu.ipfun.ip2number(net)
            calcsub = kusu.ipfun.ip2number(sub)
        
        # Fill in missing fields as needed
            if not self.startIPEntry.value():
                # Calculate the new IP Address
                xip = (((calcsub >> 1) ^ calcsub) & 0xfffffff) | calcnet
                self.startIPEntry.setEntry(kusu.ipfun.number2ip(xip))
            
            if not self.gatewayEntry.value():
                yip = calcnet | (( ~calcsub) -1)
                self.gatewayEntry.setEntry(kusu.ipfun.number2ip(yip))
                
    def guessDeviceSuffix(self):
        # Get the value of the device name.
        dev = self.deviceEntry.value()
        
        if not self.suffixEntry.value():
            # Generate new suffix based on device name.
            if not dev == "":
                self.suffixEntry.setEntry("-%s" % dev)
            
    def setCallbacks(self):
        self.buttonsDict['ok_button'].setCallback_(self.okAction)
        self.buttonsDict['cancel_button'].setCallback_(self.cancelAction)

        self.hotkeysDict['F5'] = self.cancelAction
        self.hotkeysDict['F8'] = self.okAction
        
    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 13)
        instruction = snack.Textbox(60, 1, self.kusuApp._("netedit_instruction_new"), scroll=0, wrap=0)
        self.typeList = snack.Listbox(height=2, scroll=0, width=15, returnExit=0, showCursor=0)
        self.typeLabel = snack.Label(self.kusuApp._("netedit_interface_label"))
        self.networkEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_network").rjust(13), width=30, password=0, returnExit = 0)
        self.subnetEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_subnet").rjust(13), width=30, password=0, returnExit = 0)
        self.gatewayEntry= LabelledEntry(labelTxt=self.kusuApp._("netedit_field_gateway").rjust(13), width=30, password=0, returnExit = 0)
        self.deviceEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_device").rjust(13), width=30, password=0, returnExit = 0)
        self.startIPEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_startip").rjust(10), width=30, password=0, returnExit = 0)
        self.suffixEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_suffix").rjust(13), width=30, password=0, returnExit = 0)
        self.incEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_increment").rjust(13), text="1", width=30, password=0, \
            returnExit = 0)
        self.optionEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_options").rjust(13), width=30, password=0, \
            returnExit = 0, scroll=1)
        self.descEntry = LabelledEntry(labelTxt=self.kusuApp._("netedit_field_description").rjust(10), width=30, password=0, returnExit = 0)
        self.dhcpCheck = snack.Checkbox(self.kusuApp._("netedit_field_dhcp"), isOn = 0)
        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1), growx=1)
        self.screenGrid.setField(self.networkEntry, 0, 1, padding=(0,0,0,0))
        self.screenGrid.setField(self.subnetEntry, 0, 2, padding=(0,0,0,0))
        self.screenGrid.setField(self.gatewayEntry, 0, 3, padding=(0,0,0,0)) # anchorLeft=1
        self.screenGrid.setField(self.deviceEntry, 0, 4, padding=(0,0,0,0))
        self.screenGrid.setField(self.startIPEntry, 0, 5, padding=(0,0,0,0))
        self.screenGrid.setField(self.suffixEntry, 0, 6, padding=(0,0,0,0))
        self.screenGrid.setField(self.incEntry, 0, 7, padding=(0,0,0,0))
        self.screenGrid.setField(self.optionEntry, 0, 8, padding=(0,0,0,0))
        self.screenGrid.setField(self.descEntry, 0, 9, padding=(0,0,0,0))
        self.screenGrid.setField(self.dhcpCheck, 0, 10, padding=(8, 1, 0, 0), anchorLeft=1)
        self.screenGrid.setField(self.typeLabel, 0, 11, padding=(-2,-1,0,0))
        self.screenGrid.setField(self.typeList, 0, 12, padding=(0,0,0,-1))

        self.typeList.append("public","public")
        self.typeList.append("provision","provision")

        # Set hot text callback, when tabbing or moving cursor away from field, it will prepopulate other fields when needed.
        self.networkEntry.setCallback(self.guessIPandGateway)
        self.subnetEntry.setCallback(self.guessIPandGateway)
        self.deviceEntry.setCallback(self.guessDeviceSuffix)
        
    def validate(self):
        networkEntryInfo = []
        networkEntryInfo.append(self.networkEntry.value().strip())
        networkEntryInfo.append(self.subnetEntry.value().strip())
        networkEntryInfo.append(self.gatewayEntry.value().strip())
        networkEntryInfo.append(self.startIPEntry.value().strip())
        networkEntryInfo.append(self.incEntry.value().strip())
        networkEntryInfo.append(self.deviceEntry.value().strip())
        networkEntryInfo.append(self.suffixEntry.value().strip())
        networkEntryInfo.append(self.optionEntry.value().strip())
        networkEntryInfo.append(self.descEntry.value().strip())
        networkEntryInfo.append(self.dhcpCheck.value())
        networkEntryInfo.append(self.typeList.current())
            
        modifiedRecord = NetworkRecord(networkEntryInfo, self)
            
        result, errorMsg = modifiedRecord.validateNetworkEntry()
        # Validate if the value is in IP format. 
        if not result:
            return False, self.kusuApp._(errorMsg)
        
        result, errorMsg = modifiedRecord.insertNetworkEntry()
        if not result:
           return False, self.kusuApp._(errorMsg)
            
        return True, 'Success'

class NetworkMainWindow(USXBaseScreen):

    name = "netedit_window_title_network"
    msg = "netedit_instruction_network"
    buttons = [ 'new_button', 'edit_button', 'delete_button', 'quit_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        self.kusuApp = KusuApp()
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)

    def F12Action(self):
        result = self.selector.popupDialogBox(self.kusuApp._("netedit_window_title_exit"), self.kusuApp._("netedit_instructions_exit"), 
                (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            return NAV_QUIT
        else:
            return NAV_NOTHING
        
    def newAction(self, data=None):
        global database
        global kusuApp

        ScreenFactory.screens = \
                        [ NetworkNewWindow(database=database, kusuApp=kusuApp) ]
                        
        ks = USXNavigator(ScreenFactory,screenTitle="Network Edit - Version 5.0", showTrail=False)
        ks.run()
        return NAV_NOTHING    
    
    def editAction(self, data=None):

        global database
        global kusuApp
        global selectedNetwork 
        global networkInUse

        networkList = NetworkRecord(windowInstance=self)
        currNetwork = self.networkListbox.current().split()
        selectedNetwork = currNetwork[0]

        result = networkList.checkNetworkEntry(currNetwork[0])
        if result:
           networkInUse = True
           self.selector.popupMsg(self.kusuApp._("netedit_window_title_edit"), "%s\t\t\n\n" %
           (self.kusuApp._("The network '%s' is in use. Only some fields may be changed") % currNetwork[1]))
        else:
           networkInUse = False
   
        ScreenFactory.screens = \
                        [ NetworkEditWindow(database=database, kusuApp=kusuApp) ]
                        
        ks = USXNavigator(ScreenFactory,screenTitle="Network Edit - Version 5.0", showTrail=False)
        ks.run()
        return NAV_NOTHING
    
    def deleteAction(self, data=None):
        networkList = NetworkRecord(windowInstance=self)
        currNetwork = self.networkListbox.current().split()
        result = networkList.checkNetworkEntry(currNetwork[0])
        if result:
            self.selector.popupMsg(self.kusuApp._("netedit_window_title_delete"), \
            self.kusuApp._("The network '%s' is in use. If you wish to delete this, please use the node group editor\n\n" % currNetwork[1]))
        else:
            prompt = self.selector.popupDialogBox(self.kusuApp._("netedit_window_title_delete"), 
                    self.kusuApp._("Do you want to delete the network '%s'?") % currNetwork[1], (self.kusuApp._("no_button"), \
                    self.kusuApp._("yes_button")))
            if prompt == "no":
                flag = 0                    
            elif prompt == "yes":
                self.database.connect('kusudb', 'apache')
                self.database.execute("DELETE FROM networks WHERE netid = %d" % int(currNetwork[0]))

        return NAV_NOTHING
            
    def exitAction(self, data=None):
        """ExitAction()
        Function Callback - Will pop up a quit dialog box if new nodes were added, otherwise quits without prompt
        """
        return NAV_QUIT
        
    def setCallbacks(self):
        # Button actions
        self.buttonsDict['new_button'].setCallback_(self.newAction)
        self.buttonsDict['edit_button'].setCallback_(self.editAction) 
        self.buttonsDict['delete_button'].setCallback_(self.deleteAction)
        self.buttonsDict['quit_button'].setCallback_(self.exitAction)
        
        self.hotkeysDict['F12'] = self.F12Action
        
    def drawImpl(self):
        """ Get list of node groups and allow a user to choose one """
        
        networkList = NetworkRecord(windowInstance=self)
        networkInfo = networkList.getNetworkList()

        self.screenGrid = snack.Grid(1, 3)
        instruction = snack.Textbox(60, 3, self.kusuApp._(self.msg), scroll=0, wrap=0)
        labeltokens = self.kusuApp._("netedit_item_labels").split()
        listboxlabel = snack.Label("%s %s %s %s" % (labeltokens[0].ljust(11), labeltokens[1].ljust(14), labeltokens[2].ljust(15),labeltokens[3].ljust(10)))
        self.networkListbox = snack.Listbox(height=8, scroll=1, width=70, returnExit=1, showCursor=0)
        #selectedNetwork = self.networkListbox.current()
        for nid,net,sub,netname,device,type in networkInfo:
            # If string is too long, show ellipsis.
            if len(netname) > 43: 
               netname = netname[:22] + "..."

            if not net:
               net = "DHCP"
            if not sub:
               sub = "DHCP"
            self.networkListbox.append("%s %s %s %s" % (device.ljust(11), net.ljust(14), sub.ljust(15), netname.ljust(10)), "%s %s" % (nid, net))
        self.screenGrid.setField(instruction, col=0, row=0, padding=(0, 0, 0, -1), anchorLeft=1)
        self.screenGrid.setField(listboxlabel, col=0, row=1, padding=(0, 0, 0, 0), anchorLeft=1)
        self.screenGrid.setField(self.networkListbox, col=0, row=2, padding=(0, 0, 0, 0), growx=1)

class ScreenFactoryImpl(ScreenFactory):
    """The ScreenFactory is defined by the programmer, and passed on to the
       Navigator(or it's child) class.
    """

    def __init__(self, screenlist):
        ScreenFactory.screens = screenlist

if __name__ == '__main__':
    app = NetEditApp()
    app.run()

