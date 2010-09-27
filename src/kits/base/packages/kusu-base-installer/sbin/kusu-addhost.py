#!/usr/bin/python -u
#
# Kusu add host
#
# Copyright (C) 2010 Platform Computing Inc.

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
import signal
from IPy import IP
import traceback
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
from kusu.core import database
import snack
from kusu.ui.text.USXscreenfactory import USXBaseScreen, ScreenFactory
from kusu.ui.text.USXnavigator import *
from kusu.ui.text.kusuwidgets import *
from kusu.nodefun import NodeFun
from kusu.util.errors import UserExitError
from kusu.util.errors import KusuError
from kusu.util.errors import ConflictingOptionError
import kusu.util.log as kusulog
import kusu.ipfun

NOCANCEL    = 0
ALLOWCANCEL = 1

ADDHOST_LISTEN = 0x01
ADDHOST_ADD_STATIC_IP = 0x02
ADDHOST_IMPORT_MACS = 0x04
ADDHOST_DEL = 0x08
ADDHOST_UPDATE = 0x10
ADDHOST_IMPORT_UNMANAGED_HOSTS_FILE = 0x20

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


class NodeData:
    def __init__(self):
        # Public
        self.nodeRackNumber = -1
        self.nodeRankNumber = 0
        self.ngid = 0
        self.ngname = None
        self.nodeList = []
        self.selectedInterface = None
        self.selectedNodeInterface = None
        self.syslogFilePosition = None
        self.optionReplaceMode = False
        self.replaceNodeName = None
        self.optionStaticHostMode = False
        self.staticHostname = None
        self.staticIPAddress = None
        # static IP address for managed nodes
        self.staticIPAddrOfManagedNode = None
        self.optionDHCPMode = False
        self.pluginLocation = "/opt/kusu/lib/plugins/addhost"
        self.inuseRank = -1
        self.forceQuitflag = False
        # We don't want to prompt the user to quit if we reached the last screen.
        self.quitPrompt = True
        self.batchMode = False
        self.signal = None
        self.file = None

global kusuApp
kusuApp = KusuApp()

global tuiMode
tuiMode = None

if os.geteuid() != 0:
   kusuApp.stderrMessage(kusuApp._("nonroot_execution\n"))
   kusuApp.exitFailedAndUnlock()

# Global Instance of data
global myNodeInfo
myNodeInfo = NodeData()

global myNode
myNode = kusu.nodefun.NodeFun()

global pluginActions
pluginActions = None

global kl

# Define Signal Handler for batch mode
def handleSignal(sig,frame):
    myNodeInfo.forceQuitflag = True
    myNodeInfo.signal = sig

signal.signal(signal.SIGINT, handleSignal)
signal.signal(signal.SIGTERM, handleSignal)


# TODO: dirty hack to get things working again (line 291)
# this should be refactored out of here and nghosts.py
# into a util class.
def getNodegroupType(db, ngname):
    ng = db.NodeGroups.selectfirst_by(ngname=ngname)
    return ng.type.lower()


class AddHostApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

        self._db = createDB()
        self.__db = KusuDB()
        self.action = ADDHOST_LISTEN
        self.haveInterface = False
        self.haveNodeInterface = False
        self.haveNodegroup = False
        self.replaceMode = False
        self.staticHostMode = False
        self.removeList = []

        self.parser.add_option("-v", "--version", action="callback",
                                callback=self.toolVersion, help=self._("addhost_version_usage"))
        self.parser.add_option("-n", "--nodegroup", action="store",
                                type="string", dest="nodegroup", help=self._("addhost_nodegroup_usage"))
        self.parser.add_option("-i", "--interface", action="store",
                                type="string", dest="interface", help=self._("addhost_interface_usage"))
        self.parser.add_option("-j", "--node-interface", action="store",
                                type="string", dest="nodeinterface", help=self._("addhost_nodeinterface_usage"))
        self.parser.add_option("-f", "--file", action="store",
                                type="string", dest="file", help=self._("addhost_file_usage"))
        self.parser.add_option("-e", "--remove", action="callback",
                                dest="remove", callback=self.varargs, help=self._("addhost_remove_usage"))
        self.parser.add_option("-p", "--replace", action="store",
                                type="string", dest="replace", help=self._("addhost_replace_usage"))
        self.parser.add_option("-r", "--rack", action="store",
                                type="int", dest="rack", help=self._("addhost_rack_usage"))
        self.parser.add_option("-c", "--rank", action="store",
                                type="int", dest="rank", help=self._("addhost_change_rank_usage"))
        self.parser.add_option("-u", "--update", action="store_true",
                                dest="update", help=self._("addhost_update_usage"))
        self.parser.add_option("-s", "--static-host", action="store",
                                dest="statichost", help=self._("addhost_statichost_usage"))
        self.parser.add_option("-x", "--ip-address", action="store",
                                dest="ipaddr", help=self._("addhost_ipaddr_usage"))
        self.parser.add_option("-b", "--batch", action="store_true",
                                dest="batch", help=self._("addhost_batch_usage"))

    def toolVersion(self, option, opt, value, parser):
        """
        toolVersion()
        Prints out the version of the tool to screen.
        """

        self.stdoutMessage("kusu-addhost version %s\n", self.version)
        sys.exit(0)

    def parse(self):
        """
        parse()
        Parse the command line arguments. """

        (self._options, self._args) = self.parser.parse_args(sys.argv[1:])

        # Lists are special in Python, handle boolean differently.
        if self._options.remove == []:
            removeFlag = True
        else:
            removeFlag = bool(self._options.remove)

        # === Verify options have required sub-options ===

        ## -n, -p, -e, -u, -s are mututally exclusive
        if not len([x for x in [bool(self._options.nodegroup),
                                bool(self._options.replace),
                                bool(self._options.update),
                                removeFlag,
                                self._options.statichost] if x]) <= 1:
            self.parser.error(kusuApp._("addhost_options_exclusive"))

        ## -i option (when not used with -s) requires -n
        if self._options.interface and not self._options.statichost:
            if not len([x for x in [bool(self._options.nodegroup)] if x]) == 1:
                self.parser.error(kusuApp._("addhost_options_interface_options_needed"))

        ## -f option requires -n
        ## -f option requires -j when -n specifies a managed nodegroup
        if self._options.file:
            if not bool(self._options.nodegroup):
                self.parser.error(kusuApp._("addhost_options_file_nodegroup_needed"))

            if self._options.nodegroup == 'unmanaged':
                if bool(self._options.nodeinterface):
                    self.parser.error(kusuApp._("addhost_options_file_interface_invalid"))
            elif not bool(self._options.nodeinterface):
                self.parser.error(kusuApp._("addhost_options_file_interface_needed"))

        ## -s option requires -x or -i
        if self._options.statichost:
            if not len([x for x in [bool(self._options.ipaddr),
                                    bool(self._options.interface)] if x]) == 1:
                self.parser.error(kusuApp._("addhost_options_static_option_conflict"))


        # === Verify sub-options are used with correct options ===

        ## -j should only be used with -f
        if self._options.nodeinterface and not self._options.file:
            self.parser.error(kusuApp._("addhost_options_macfile_suboptions_error"))

        ## -x should only be used with -s or -n
        if self._options.ipaddr and not (self._options.statichost or self._options.nodegroup):
            self.parser.error(kusuApp._("addhost_options_static_suboptions_error"))

        ## -x should not be used with -f
        if self._options.ipaddr and self._options.file:
            self.parser.error(kusuApp._("addhost_options_static_suboptions_error"))

        # === Process individual options ===

        ## Handle -b option
        if self._options.batch:
            myNodeInfo.batchMode = True

        ## Handle -r option
        if isinstance(self._options.rack,int) :
            result = int(self._options.rack)
            if result < 0:
                self.parser.error(kusuApp._("rack_negative_number"))
            else:
                myNodeInfo.nodeRackNumber = result
                myNode.setRackNumber(myNodeInfo.nodeRackNumber)

        ## Handle -c option
        if isinstance(self._options.rank,int) :
            result = int(self._options.rank)
            if result < 0:
                self.parser.error(kusuApp._("rank_negative_number"))
            else:
                myNodeInfo.nodeRankNumber = result
                myNode.setRankNumber(myNodeInfo.nodeRankNumber)

        ## Handle -i option
        if self._options.interface:
            if self._options.interface[0] == '-':
                self.parser.error(kusuApp._("addhost_options_interface_required"))

            # Check the provided interface is associated with provisioning network
            interface = self._options.interface.strip()
            # Retieve networks currently associated with the installer nodegroup
            ng_has_nets = self._db.NGHasNet.select_by(ngid=self._db.NodeGroups.selectfirst_by(type='installer').ngid)
            # Retrieve provisioning networks associated with the target device
            provision_nets = self._db.Networks.select_by(device=interface, type='provision')

            ng_net_nets_ids = [ x.netid for x in ng_has_nets ]
            provision_nets_ids = [ x.netid for x in provision_nets ]
            # If no provisioning network associated, then print proper error message.
            if not set(ng_net_nets_ids) & set(provision_nets_ids):
                self.parser.error(kusuApp._("addhost_options_provision_interface_required"))

            myNodeInfo.selectedInterface = interface
            self.haveInterface = True

        ## Handle -n option
        if self._options.nodegroup:
            if self._options.nodegroup[0] == '-':
               self.parser.error(kusuApp._("addhost_options_nodegroup_required"))

            # Save the node group name, and convert to id later
            myNodeInfo.ngname = self._options.nodegroup.strip()
            self.haveNodegroup = True

            ngtype = getNodegroupType(self._db, myNodeInfo.ngname )
            if ngtype == 'installer':
                self.logErrorEvent(kusuApp._("Nodes cannot be added to installer nodegroups"))
                self.exitFailedAndUnlock(-1)

            if self._options.ipaddr:
                myNodeInfo.staticIPAddrOfManagedNode = self._options.ipaddr.strip()

        ## Handle -s option
        if self._options.statichost:

            myNodeInfo.staticHostname = self._options.statichost.strip().lower()
            myNodeInfo.optionStaticHostMode = True
            self.staticHostMode = True

            if len(myNodeInfo.staticHostname) == 0:
               self.parser.error(kusuApp._("addhost_static_device_no_host_error"))

            # Handle -x option
            if self._options.ipaddr:
                self.action = ADDHOST_ADD_STATIC_IP
                myNode.setNodegroupByName("unmanaged")
                myNodeInfo.staticIPAddress = self._options.ipaddr.strip()

            # Handle -i option
            elif self._options.interface:
                myNodeInfo.optionDHCPMode = True

        ## Handle -j option
        if self._options.nodeinterface:
              myNodeInfo.selectedNodeInterface = self._options.nodeinterface.strip()
              self.haveNodeInterface = True

        ## Handle -f option
        if self._options.file:
            if self._options.nodeinterface:
                self.action = ADDHOST_IMPORT_MACS
                myNodeInfo.macfile = self._options.file.strip()
            else:
                self.action = ADDHOST_IMPORT_UNMANAGED_HOSTS_FILE
                myNodeInfo.hostsfile = self._options.file.strip()

        ## Handle -p option
        if self._options.replace:
            if self._options.replace.strip().isdigit():
                self.parser.error(kusuApp._("addhost_options_invalid_node"))

            if self._options.replace[0] == '-':
                self.parser.error(kusuApp._("addhost_options_replace_required"))

            self.replaceMode = True
            myNodeInfo.optionReplaceMode = True
            myNodeInfo.replaceNodeName = self._options.replace.strip()

        ## Handle -e option
        if self._options.remove:
            self.action = ADDHOST_DEL
            self.removeList = self._options.remove

        elif self._options.remove == []:
            self.parser.error(kusuApp._("addhost_options_remove_required"))

        ## Handle -u option
        if self._options.update:
            self.action = ADDHOST_UPDATE

        ## Handle for plugin options
        global pluginActions
        if pluginActions:
            pluginActions.plugins_parse(self._options)

    def loadPlugins(self):
        """ loadPlugins()
        Loads all plugins for addhost. """

        try:
            self.__db.connect(user='apache', dbname='kusudb')
        except Exception,msg:
            raise KusuError, 'Problems establishing database connection. Error: %s' %msg

        global pluginActions
        pluginList = []
        pluginInstances = []
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
             if ext == ".py":
                if not plugin == "__init__" and not plugin[0] == '.':
                    pluginList.append(plugin)

        # Import the plugins
        moduleInstances = map(__import__, pluginList)

        # Create instances of each new plugin and store the instances.
        for thisModule in moduleInstances:
            try:
                thisPlugin = thisModule.AddHostPlugin(self.__db)
                if thisPlugin.enabled():
                    pluginInstances.append(thisPlugin)
                    thisPlugin.registerOptions(self.parser)
            except ConflictingOptionError:
                self.stdoutMessage(kusuApp._("Warning: Found option conflict in plugin '%s'. This plugin's options will be IGNORED.\n"),thisModule)
            except:
                msg = "Warning: Invalid plugin '%s'. Does not have a AddHostPlugin class.\nThis plugin will be IGNORED.\n"
                self.stdoutMessage(kusuApp._(msg), thisModule)
                kl.error(msg, thisModule)
        pluginActions = PluginActions(pluginInstances)

    def nxor(self, *args):
        """nxor(varargs args)
        N-way function, only one condition may be true otherwise false. """

        return len([x for x in args if x]) == 1

    def initAction(self):
        """Test DB, lock, then load plugins. Throws KusuError.
        """
        try:
            self.__db.connect(user='apache', dbname='kusudb')
        except Exception,msg:
            raise KusuError, 'Problems establishing database connection. Error: %s' %msg

        # Check if nghosts is in use, if so abort running addhost.
        if os.path.isfile("/var/lock/subsys/kusu-nghosts"):
            raise KusuError, kusuApp._("addhost_nghosts_lock")

        # Check if repoman is in use, if so abort running addhost.
        if os.path.isfile("/var/lock/subsys/kusu-repoman"):
            raise KusuError, kusuApp._("ERROR:   Cannot run kusu-addhost because kusu-repoman is running. Please wait for kusu-repoman to finish first")

        # Check if repopatch is in use, if so abort running addhost.
        if os.path.isfile("/var/lock/subsys/kusu-repopatch"):
            raise KusuError, kusuApp._("ERROR:   Cannot run kusu-addhost because kusu-repopatch is running. Please wait for kusu-repopatch to finish first")

        if self.islock():
            raise KusuError, kusuApp._("program_already_inuse") % ('Kusu-addhost', 'kusu-addhost') # (program name, lock file name)

        self.lock()
        ## init plugins
        global pluginActions
        if pluginActions:
            pluginActions.plugins_init()

    def getRackNumberFromUser(self):

        if myNodeInfo.nodeRackNumber < 0:

            while True:
                try:
                    response = raw_input(kusuApp._("prompt_for_rack"))
                except (KeyboardInterrupt, EOFError), e:
                    self.stdoutMessage("\n" + kusuApp._("addhost_cmd_abort") + "\n")
                    return False

                try:
                   result = int(response)
                   if result < 0:
                      self.stdoutMessage(kusuApp._("rack_negative_number") + "\n")
                   else:
                      myNodeInfo.nodeRackNumber = result
                      break
                except:
                   self.stdoutMessage(kusuApp._("addhost_non_numeric_rack_number_error") + "\n", response)

        myNode.setRackNumber(myNodeInfo.nodeRackNumber)
        return True


    def doListenAction(self):
        """Action to start the addhost listener. Assumes that lock is acquired.
        """

        # Validate static hostname
        if myNodeInfo.staticHostname:
            if myNode.validateNode(myNodeInfo.staticHostname):
                msg = kusuApp._("addhost_options_hostname_in_use")
                return False, msg

        # Validate replaced hostname
        if myNodeInfo.replaceNodeName:
            if not myNode.validateNode(myNodeInfo.replaceNodeName):
                msg = kusuApp._("addhost_replace_node_not_found") % myNodeInfo.replaceNodeName
                return False, msg

        # Validate listening interface
        if myNodeInfo.selectedInterface:
            if not myNode.validateInterface(myNodeInfo.selectedInterface, installer=True):
                msg = kusuApp._("addhost_options_invalid_interface")
                return False, msg

        dhcp_enabled = int(self.__db.getAppglobals('InstallerServeDHCP'))

        if not dhcp_enabled:
            ## -b not allowed with external dhcp
            if myNodeInfo.batchMode:
                print "Error: Option '-b/--batch' is not allowed with external DHCP server."
                self.exitFailedAndUnlock()

            if self.haveNodegroup and myNodeInfo.ngname != 'unmanaged':
                print "Error: Action not allowed. You can only add nodes to 'unmanaged' nodegroup with external DHCP server."
                self.exitFailedAndUnlock()
            elif myNodeInfo.staticHostname or myNodeInfo.replaceNodeName:
                print "Error: This action is not allowed with external DHCP server."
                self.exitFailedAndUnlock()

        # Validate node group name and rack number
        if myNodeInfo.ngname:

            result, ngid = myNode.validateNodegroup(myNodeInfo.ngname)
            if result:
                myNodeInfo.ngid = ngid
            else:
                msg = kusuApp._("options_invalid_nodegroup")
                return False, msg

            myNode.setNodegroupByID(myNodeInfo.ngid)

            if myNodeInfo.staticIPAddrOfManagedNode:
                # Validate IP address for manually specified IP:
                if not kusu.ipfun.validIP(myNodeInfo.staticIPAddrOfManagedNode):
                    msg = kusuApp._("addhost_invalid_ip")
                    return False, msg
                # If IP is already in use by some node:
                if myNode.isIPUsed(myNodeInfo.staticIPAddrOfManagedNode):
                    msg = kusuApp._("addhost_ip_conflict") % myNodeInfo.staticIPAddrOfManagedNode
                    return False, msg
                # Validate if the specified IP in provisioning networks.
                validIPFlag = False
                for netrecord in myNode.getNGNetworks():
                    provnet = IP(netrecord[1]).make_net(netrecord[2])
                    if IP(myNodeInfo.staticIPAddrOfManagedNode) in provnet and \
                       IP(myNodeInfo.staticIPAddrOfManagedNode) != provnet[0] and \
                       IP(myNodeInfo.staticIPAddrOfManagedNode) != provnet[-1]:
                        validIPFlag = True
                        break;
                if not validIPFlag:
                    msg =  kusuApp._("addhost_ip_notin_network") % (myNodeInfo.staticIPAddrOfManagedNode,\
                                                                    myNodeInfo.ngname)
                    return False, msg

            if myNode.isNodenameHasRack():
                if not self.getRackNumberFromUser():
                    # User decided to quit...
                    return True, 'Success'

        # Run batch steps or TUI screens
        if (myNodeInfo.batchMode):
            self.runBatchSteps(self.replaceMode,
                               self.haveInterface,
                               self.haveNodegroup,
                               self.staticHostMode)
        else:
            self.runTUIScreens(self.replaceMode,
                               self.haveInterface,
                               self.haveNodegroup,
                               self.staticHostMode)

        if len(myNodeInfo.nodeList):
            if pluginActions:
                pluginActions.plugins_finished()

        return True, 'Success'


    def doAddStaticIPAction(self):

        if not kusu.ipfun.validIP(myNodeInfo.staticIPAddress):
            msg = kusuApp._("addhost_invalid_ip")
            return False, msg

        result, msg = myNode.addUnmanagedStaticDevice(myNodeInfo.staticHostname, ip=myNodeInfo.staticIPAddress)
        if not result:
            return False, msg

        if pluginActions:
            pluginActions.plugins_add(myNodeInfo.staticHostname)
            pluginActions.plugins_finished()

        return True, 'Success'

    def doImportMacs(self):

        # Check if the file specified exists.
        if not os.path.isfile(myNodeInfo.macfile):
            msg = kusuApp._("The file '%s' was not found") % myNodeInfo.macfile
            return False, msg

        # Validate node group name
        result, ngid = myNode.validateNodegroup(myNodeInfo.ngname)
        if result:
            myNodeInfo.ngid = ngid
        else:
            msg = kusuApp._("options_invalid_nodegroup")
            return False, msg

        myNode.setNodegroupByID(myNodeInfo.ngid)

        # Whether the node IP should be preserved as in Avalon
        preserveNodeIP = self.__db.getAppglobals('PRESERVE_NODE_IP')

        need_rack_prompt = myNode.isNodenameHasRack()

        # Check if the node group's interfaces are valid.
        if not myNode.validateInterface(myNodeInfo.selectedNodeInterface,
                                        installer=False, nodegroup=myNodeInfo.ngid):
            msg = kusuApp._("addhost_options_invalid_interface")
            return False, msg

        # MAC, [Desired IP], [Desired Hostname], [Unique ID]
        macfileList = [line.split(',') for line in open(myNodeInfo.macfile,'r') if len(line.strip()) > 0]

        # Check if the file specified is empty
        if not macfileList:
            msg = kusuApp._("The macfile '%s' is empty") % myNodeInfo.macfile
            return False,msg
        macaddrflag=False
        for line in macfileList:
             macaddr = line[0]
             if not re.search("(?<![-0-9a-f:])([\da-fA-F]{2}[:]){5}([\da-fA-F]{2})(?![-0-9a-f:])", macaddr):
                self.stdoutMessage(kusuApp._("Skipping '%s'. Not a MAC address") + "\n", macaddr.strip())
                continue

             macaddr = macaddr.lower().strip()
             checkMacAddr = myNode.findMACAddress(macaddr)
             if checkMacAddr == False:
                 myNode.setRankNumber(myNodeInfo.nodeRankNumber)
                 ng = self._db.NodeGroups.selectfirst_by(ngid=ngid)
                 if ng.installtype == 'unmanaged':
                     unmanaged=True
                 else:
                     unmanaged=False
                 # Get optional parameters from mac line
                 ipaddr = None
                 hostname = None
                 uid=''

                 if preserveNodeIP == '1':
                     # Determine if the IP should be preserved by consulting
                     # the nodegroups this node has previously been in.
                     # Start with the current nodegroup.  If not found use the
                     # first ip where the netid's match
                     try:
                         ipaddr = myNode.findOldIPForNode(macaddr, myNodeInfo.ngid)
                     except:
                         pass

                     try:
                         hostname = myNode.findOldHostnameForNode(macaddr, myNodeInfo.ngid)
                     except:
                         pass

                     if ipaddr:
                         self.stdoutMessage("Using IP address '%s'\n", ipaddr)
                     if hostname:
                         self.stdoutMessage("Using hostname '%s'\n", hostname)

                 if not (ipaddr and hostname):
                     # don't process the rest of the line on the first error
                     if len(line) > 1 and kusu.ipfun.validIP(line[1]):
                         ipaddr = line[1].strip()
                         if len(line) > 2:
                             hostname = line[2].strip() or None
                             if len(line) > 3:
                                 uid = line[3].strip()

                 # We need the rack from the user if a hostname isn't specified
                 if need_rack_prompt and hostname is None:
                     need_rack_prompt = False
                     if not self.getRackNumberFromUser():
                         # User decided to quit...
                         return True, 'Success'

                 nodeName = myNode.addNode(macaddr, myNodeInfo.selectedNodeInterface, installer=False, unmanaged=unmanaged, snackInstance=False, ipaddr=ipaddr, hostname=hostname, uid=uid)
                 msg = kusuApp._("addhost_imported_mac") % (macaddr,nodeName)
                 self.logEvent(msg)
                 macaddrflag=True

                 # Ask all plugins to call added() function
                 myNode.addUsedMAC(macaddr)
                 if pluginActions:
                     pluginActions.plugins_add(nodeName, True)
                 myNodeInfo.nodeList.append(nodeName)
             else:
                 msg = kusuApp._("addhost_duplicate_mac") % macaddr
                 self.logWarnEvent(msg)

        # If all the macaddrs in the macfile are either invalid or duplicate,exits directly.
        if macaddrflag==False:
            msg = kusuApp._("Check that MAC addresses are in valid format and are unique in the macfile '%s'") % myNodeInfo.macfile
            return False,msg
        if pluginActions:
            pluginActions.plugins_finished(True)

        return True, 'Success'

    def doImportUnmanagedHostsFile(self):

        # Check if the file specified exists:
        if not os.path.isfile(myNodeInfo.hostsfile):
            msg = kusuApp._("addhost_unmanaged_hosts_file_not_found") % myNodeInfo.hostsfile
            return False, msg

        f = open(myNodeInfo.hostsfile,'r')
        hosts = [line.split() for line in f if len(line.strip()) > 0]
        # Check if the file specified is empty
        if not hosts:
            msg = kusuApp._("The unmanaged hosts file '%s' is empty") % myNodeInfo.hostsfile
            return False,msg
        f.close()

        # Collect those invalid unmanaged host records
        badNodes = []

        for host in hosts:

            # Check if the unmanaged host record is of format:
            # <static hostname>:<static ip>
            items = host[0].split(":")
            if len(items) != 2:
                msg = "Skipping '%s'. Unmanaged host record must be in <static host name>:<static IP> format." % host[0].strip()
                self.stdoutMessage(kusuApp._(msg) + "\n")
                badNodes.append(host)
                continue

            hostname, ip = items

            # Start adding the node
            startMsg = kusuApp._("addhost_event_start_add_static_ip") % (hostname,ip)
            self.logEvent(startMsg, toStdout=False)

            # Check if the hostname or IP is in use is done in the method
            # addUnmanagedStaticDevice
            result, msg = myNode.addUnmanagedStaticDevice(hostname, ip)
            if not result:
                self.logWarnEvent(msg)
                badNodes.append(host)
                continue

            # Finish adding the node
            finishMsg = kusuApp._("addhost_event_finish_add_static_ip") % (hostname,ip)
            self.logEvent(finishMsg, toStdout=False)

            # Run plugins when there are valid unmanaged host records
            if pluginActions and hosts != badNodes:
                pluginActions.plugins_add(hostname)

        # Run plugins when there are valid unmanaged host records
        if pluginActions and hosts != badNodes:
            pluginActions.plugins_finished()

        return True, 'Success'

    def doDelNodes(self):

        delflag = False
        badnodes = []

        for delnode in self.removeList:
            delnode = delnode.strip()

            if not myNode.validateNode(delnode):
                badnodes.append(delnode)
                msg = kusuApp._("addhost_delete_unknown_node") %delnode
                self.logErrorEvent(msg)
                continue

            # Ask all plugins to call removed() function
            if pluginActions:
                pluginActions.plugins_removed(delnode)

            self.stdoutMessage(kusuApp._("Removing Node: %s") + "\n", delnode)

            # Handle removing node from db.
            if myNode.deleteNode(delnode):
                self.logEvent(kusuApp._("addhost_event_deleted_node") % delnode,
                              toStdout=False)
                delflag = True
                myNodeInfo.nodeList.append(delnode)
            else:
                self.logErrorEvent(kusuApp._("addhost_delete_node_db_error") % delnode,
                              toStderr=False)
                badnodes.append(delnode)
                continue

        if pluginActions and delflag:
            pluginActions.plugins_finished()

        if badnodes:
            return False, kusuApp._("addhost_delete_bad_nodes_found")

        return True, 'Success'

    def doUpdate(self):

        # Ask all plugins to call updated() function
        if pluginActions:
            pluginActions.plugins_updated()
            pluginActions.plugins_finished()

        return True, 'Success'

    def runAction(self, action, startMsg, finishMsg):

        if startMsg: self.logEvent(startMsg, toStdout=False)

        # Lock
        try:
            self.initAction()
        except KusuError, e:
            self.logErrorEvent(e)
            sys.exit(-1)

        provision = self.__db.getAppglobals('PROVISION')
        if provision and provision != 'KUSU' and self.action == ADDHOST_LISTEN:
            sys.stderr.write('Kusu provisioning has been disabled. addhost will not run.\n')
            self.exitFailedAndUnlock()

        # Do Action
        try:
            (success,errMsg) = action()
        except KusuError, e:
            self.logErrorEvent(e)
            self.exitFailedAndUnlock()

        # Check Action Result
        if success:
            if finishMsg: self.logEvent(finishMsg, toStdout=False)
            self.exitSuccessAndUnlock()
        else:
            self.logErrorEvent(errMsg)
            self.exitFailedAndUnlock()

    def getActionDesc(self):
        if self.action == ADDHOST_LISTEN:
            return "PXE Listener"
        elif self.action == ADDHOST_ADD_STATIC_IP:
            return "Add static IP"
        elif self.action == ADDHOST_IMPORT_MACS:
            return "Import MACs"
        elif self.action == ADDHOST_DEL:
            return "Delete hosts"
        elif self.action == ADDHOST_UPDATE:
            return "Update hosts"
        elif self.action == ADDHOST_IMPORT_UNMANAGED_HOSTS_FILE:
            return "Import unmanaged hosts file"
        else:
            return KusuApp.getActionDesc(self)

    def run(self):
        """run()
        Run the application """

        screenList = []

        global kusuApp

        if self.action == ADDHOST_LISTEN:

            self.runAction(self.doListenAction,
                           startMsg = kusuApp._("addhost_event_start_listener"),
                           finishMsg = kusuApp._("addhost_event_stop_listener"))

        elif self.action == ADDHOST_ADD_STATIC_IP:

            host = myNodeInfo.staticHostname
            ip = myNodeInfo.staticIPAddress

            self.runAction(self.doAddStaticIPAction,
                           startMsg = kusuApp._("addhost_event_start_add_static_ip") % (host,ip),
                           finishMsg = kusuApp._("addhost_event_finish_add_static_ip") % (host,ip))

        elif self.action == ADDHOST_IMPORT_MACS:

            self.runAction(self.doImportMacs,
                           startMsg = kusuApp._("addhost_event_start_mac_import"),
                           finishMsg = kusuApp._("addhost_event_finish_mac_import"))

        elif self.action == ADDHOST_DEL:

            self.runAction(self.doDelNodes,
                           startMsg = kusuApp._("addhost_event_start_delete_nodes"),
                           finishMsg = kusuApp._("addhost_event_finish_delete_nodes"))

        elif self.action == ADDHOST_UPDATE:

            self.runAction(self.doUpdate, None, None)

        elif self.action == ADDHOST_IMPORT_UNMANAGED_HOSTS_FILE:

            self.runAction(self.doImportUnmanagedHostsFile,
                           startMsg = kusuApp._("addhost_event_start_unmanagedhosts_import"),
                           finishMsg = kusuApp._("addhost_event_finish_unmanagedhosts_import"))


    def runBatchSteps(self, replaceMode, haveInterface, haveNodegroup, staticHostMode):
        """Run all of addhost's steps in batch mode"""

        db = self.__db

        if replaceMode or staticHostMode:
            batchStepList = [BatchNodeStatus(database=db, kusuApp=kusuApp)]
        elif haveInterface and haveNodegroup:
            batchStepList = [BatchUnmanaged(database=db, kusuApp=kusuApp),
                             BatchNodeStatus(database=db, kusuApp=kusuApp)]
        elif haveNodegroup and not haveInterface:
            batchStepList = [BatchUnmanaged(database=db, kusuApp=kusuApp),
                             BatchSelectNode(database=db, kusuApp=kusuApp),
                             BatchNodeStatus(database=db, kusuApp=kusuApp)]
        else:
            batchStepList = [NodeGroupBatch(database=db, kusuApp=kusuApp),
                             BatchUnmanaged(database=db, kusuApp=kusuApp),
                             BatchSelectNode(database=db, kusuApp=kusuApp),
                             BatchNodeStatus(database=db, kusuApp=kusuApp)]

        for step in batchStepList:
            if (myNodeInfo.forceQuitflag):
                break
            else:
                step()


    def runTUIScreens(self, replaceMode, haveInterface, haveNodegroup, staticHostMode):
        """Run all of addhost's steps in TUI mode"""

        # Screen ordering
        db = self.__db

        if replaceMode or staticHostMode:
            screenList = [ WindowNodeStatus(database=db, kusuApp=self) ]

        elif haveNodegroup and myNodeInfo.ngname == 'unmanaged':
            screenList = [ WindowUnmanaged(database=db, kusuApp=kusuApp),
                          WindowSelectNode(database=db, kusuApp=kusuApp),
                          WindowNodeStatus(database=db, kusuApp=self)
                         ]

        elif haveInterface and haveNodegroup:
            screenList = [ WindowNodeStatus(database=db, kusuApp=self) ]

        elif haveNodegroup and not haveInterface:
            screenList = [ WindowSelectNode(database=db, kusuApp=kusuApp),
                           WindowNodeStatus(database=db, kusuApp=self)
                         ]

        else:
            screenList = [ NodeGroupWindow(database=db, kusuApp=kusuApp),
                          WindowSelectNode(database=db, kusuApp=kusuApp),
                          WindowNodeStatus(database=db, kusuApp=self)
                         ]

        screenFactory = ScreenFactoryImpl(screenList)
        ks = USXNavigator(screenFactory=screenFactory, screenTitle="Add Hosts - Version ${VERSION_STR}", showTrail=False)
        ks.run()


class PluginActions(object, KusuApp):
    def __init__(self, pluginInstances):
        KusuApp.__init__(self)
        self._pluginInstances = pluginInstances
        global myNode
        self._nodeHandler = myNode

    # Plugin call actions
    def plugins_add(self, nodename, prePopulateMode=False):
        """plugins_add(nodename)
        Call all addhost plugins' added() method
        """

        global tuiMode
        #pt1=time.time()
        if self._nodeHandler.nodeIsPrimaryInstaller(nodename):
            self.stderrMessage(self._("add_primary_installer_error") + "\n")
            return

        info = self._nodeHandler.getNodeInformation(nodename)
        for plugin in self._pluginInstances:
            #t1=time.time()
            try:
                plugin.added(nodename, info, prePopulateMode)
            except:
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                if plugin.canFail:
                    failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                    kusuApp.kel.error("NON-FATAL EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                    pass
                else:
                    failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                    kusuApp.kel.error("EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                    if tuiMode == None:
                        print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                        print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                        sys.exit(-1)
                    else:
                        tuiMode.finish()
                        print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                        print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                        raise UserExitError

            #t2=time.time()
            #print "====> PLUGIN: %s: Time Spent: added(): %f" % (plugin, t2-t1)

        #t2=time.time()
        #print "******** ALL added() Plugins Time Spent: %f" % (t2-pt1)

    def plugins_removed(self, nodename):
        """plugins_removed(nodename)
        Call all addhost plugins' removed() method
        """

        global tuiMode
        #pt1=time.time()
        #print "DEBUG: Calling removed() method from plugins"
        info = self._nodeHandler.getNodeInformation(nodename)
        for plugin in self._pluginInstances:
            #t1=time.time()
            try:
                plugin.removed(nodename, info)
            except:
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                if plugin.canFail:
                   failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                   kusuApp.kel.error("NON-FATAL EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                   pass
                else:
                   failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                   kusuApp.kel.error("EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                   if tuiMode == None:
                      print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                      print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                      sys.exit(-1)
                   else:
                      tuiMode.finish()
                      print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                      print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                      raise UserExitError
            #t2=time.time()
            #print "====> PLUGIN: %s: Time Spent: removed(): %f" % (plugin, t2-t1)

        #t2=time.time()
        #print "******** ALL removed() Plugins Time Spent: %f" % (t2-pt1)

    def plugins_replaced(self, nodename):
        """plugins_replaced(nodename)
        Call all addhost plugins' replaced() method
        """
        global tuiMode
        #pt1=time.time()
        #print "DEBUG: Calling replaced() method from plugins"
        if not self._nodeHandler.nodeIsPrimaryInstaller(nodename):
            info = self._nodeHandler.getNodeInformation(nodename)
            for plugin in self._pluginInstances:
                #t1=time.time()
                try:
                    plugin.replaced(nodename, info)
                except:
                    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                    if plugin.canFail:
                       failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                       kusuApp.kel.error("NON-FATAL EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                       pass
                    else:
                       failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                       kusuApp.kel.error("EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                       if tuiMode == None:
                          print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                          print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                          sys.exit(-1)
                       else:
                          tuiMode.finish()
                          print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                          print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                          raise UserExitError
                #t2=time.time()
                #print "====> PLUGIN: %s: Time Spent: replaced(): %f" % (plugin, t2-t1)
        else:
            self.stderrMessage(self._("replace_primary_installer_error") + "\n")
            self.exitFailedAndUnlock()
        #t2=time.time()
        #print "******** ALL replaced() Plugins Time Spent: %f" % (t2-pt1)

    def plugins_finished(self, prePopulateMode=False):
        """plugins_finished()
        Call all addhost plugins' finished() method
        """
        global myNodeInfo
        global tuiMode
        #pt1=time.time()
        #print "DEBUG: Calling finished() method from plugins"
        for plugin in self._pluginInstances:
            #t1=time.time()
            try:
                plugin.finished(myNodeInfo.nodeList, prePopulateMode)
            except:
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                if plugin.canFail:
                   failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                   kusuApp.kel.error("NON-FATAL EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                   pass
                else:
                   failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                   kusuApp.kel.error("EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                   if tuiMode == None:
                      print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                      print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                      sys.exit(-1)
                   else:
                      tuiMode.finish()
                      print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                      print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                      raise UserExitError
            #t2=time.time()
            #print "====> PLUGIN: %s: Time Spent: finished(): %f" % (plugin, t2-t1)
        #t2=time.time()
        #print "******** ALL finished() Plugins Time Spent: %f" % (t2-pt1)

    def plugins_updated(self):
        """plugins_updated()
        Call all addhost plugins' updated() method
        """
        #print "DEBUG: Calling updated() method from plugins"
        #pt1=time.time()
        global tuiMode
        for plugin in self._pluginInstances:
            #t1=time.time()
            try:
                plugin.updated()
            except:
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                if plugin.canFail:
                   failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                   kusuApp.kel.error("NON-FATAL EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                   pass
                else:
                   failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                   kusuApp.kel.error("EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                   if tuiMode == None:
                      print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                      print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                      sys.exit(-1)
                   else:
                      tuiMode.finish()
                      print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                      print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                      raise UserExitError
            #t2=time.time()
            #print "====> PLUGIN: %s: Time Spent: updated(): %f" % (plugin, t2-t1)
        #t2=time.time()
        #print "******** ALL updated() Plugins Time Spent: %f" % (t2-pt1)

    def plugins_init(self):
        """plugins_init()
        Call all addhost plugins' init() method
        """

        global tuiMode
        for plugin in self._pluginInstances:
            try:
                plugin.init()
            except:
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                if plugin.canFail:
                   failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                   kusuApp.kel.error("NON-FATAL EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                   pass
                else:
                   failureTmp = repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
                   kusuApp.kel.error("EXCEPTION from plugin '%s': EXCEPTION ==> %s" % (plugin, failureTmp))
                   if tuiMode == None:
                      print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                      print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                      sys.exit(-1)
                   else:
                      tuiMode.finish()
                      print traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback)
                      print "************* EXCEPTION OCCURRED PLEASE SEE /var/log/kusu/kusu.log. Program will now exit..."
                      raise UserExitError

    def plugins_parse(self, options):
        """plugins_parse()
        Call all addhost plugins' parseOptions() method
        """
        for plugin in self._pluginInstances:
            plugin.parseOptions(options)


class NodeGroupBatch:
    def __init__(self, database, kusuApp=None):
        self.database = database;
        self.kusuApp = kusuApp;

    def __call__(self):
        if myNodeInfo.forceQuitflag:
            return

        self.selectNodeGroup()
        self.validate()

    def selectNodeGroup(self):
        """Asks user to select a node group from a list"""

        global myNodeInfo
        flag = True

        while flag:
            try:
                nodeGroups = self.getNodeGroupList()

                kusuApp.stdoutMessage("\n" + self.kusuApp._("addhost_instruction_nodegroup") + "\n")

                count = 1
                ngid_list = []
                for ng,ngid in nodeGroups:
                    kusuApp.stdoutMessage("%d) %s\n", count, ng)
                    ngid_list.append(ngid)
                    count = count + 1

                response = raw_input(">> ")

                try:
                    result = int(response) - 1
                    if (result < 0 or result >= len(ngid_list)):
                        kusuApp.stderrMessage("\n%s\n" % self.kusuApp._("addhost_invalid_selection"))
                    else:
                        myNodeInfo.ngid = ngid_list[result]
                        flag = False
                except ValueError:
                    kusuApp.stderrMessage("\n%s\n" % self.kusuApp._("addhost_invalid_selection"))

            except KusuError, e:
                kusuApp.stderrMessage("\n%s\n" % e.args[0])
                myNodeInfo.forceQuitflag = True
                return

            except (KeyboardInterrupt,EOFError), e:
                kusuApp.stdoutMessage("\n" + kusuApp._("addhost_cmd_abort") + "\n")
                myNodeInfo.forceQuitflag = True
                return


    def getNodeGroupList(self):
        nodeGroups = ()
        try:
            query = "SELECT ngname, ngid FROM nodegroups where type != 'installer' ORDER BY ngid"
            self.database.execute(query)
            nodeGroups = self.database.fetchall()
        except:
            raise KusuError, self.kusuApp._("DB_Query_Error\n")

        return nodeGroups

    def validate(self):
        if myNode.getNodegroupNameByID(myNodeInfo.ngid) == 'unmanaged':
           myNodeInfo.optionStaticHostMode = True
        else:
           myNodeInfo.optionStaticHostMode = False

    def exitAction(self):
        pass


class NodeGroupWindow(USXBaseScreen,NodeGroupBatch):

    name = "addhost_window_title_nodegroup"
    msg = "addhost_instruction_nodegroup"
    buttons = ['next_button', 'exit_button']

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        NodeGroupBatch.__init__(self, database, kusuApp)
        self.setHelpLine("Copyright(C) 2010 Platform Computing Inc.\t%s" % self.kusuApp._("addhost_helpline_instructions"))

    def F12Action(self):
        if myNodeInfo.quitPrompt:
            result = self.selector.popupDialogBox(self.kusuApp._("addhost_window_title_exit"), self.kusuApp._("addhost_instructions_exit"),
                    (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
            if result == "no":
                return NAV_NOTHING
            if result == "yes":
                return NAV_QUIT
        else:
            #if len(myNodeInfo.nodeList):
            #    if pluginActions:
            #       pluginActions.plugins_finished()
            return NAV_QUIT

    def exitAction(self, data=None):
        """ExitAction()
        Function Callback - Will pop up a quit dialog box if new nodes were added, otherwise quits without prompt
        """
        #if len(myNodeInfo.nodeList):
            #if pluginActions:
               #pluginActions.plugins_finished()
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
        global tuiMode
        tuiMode = self.screen
        dhcp_enabled = int(self.database.getAppglobals('InstallerServeDHCP'))

        try:
            nodeGroups = NodeGroupBatch.getNodeGroupList(self)
        except:
           self.selector.popupMsg (self.kusuApp._("Error"), self.kusuApp._("DB_Query_Error\n"))
           self.screen.finish()
           raise UserExitError

        self.screenGrid = snack.Grid(1, 2)
        instruction = snack.Textbox(40, 2, self.kusuApp._(self.msg), scroll=0, wrap=1)

        #value = snack.ListboxChoiceWindow(self.screen, self.kusuApp._(self.name), self.kusuApp._(self.msg), nodeGroups, buttons = ['Next', 'Exit'], width = 40, scroll=1, height=6, default=None, help=None)
        if dhcp_enabled:
            self.listbox = snack.Listbox(len(nodeGroups), scroll=1, returnExit=1)
            for ng,ngid in nodeGroups:
                self.listbox.append("%s" % ng, "%s" % ngid)
        else:
            self.listbox = snack.Listbox(1, scroll=1, returnExit=1)
            for ng,ngid in nodeGroups:
                if ng == 'unmanaged':
                    self.listbox.append("%s" % ng, "%s" % ngid)

        self.screenGrid.setField(instruction, col=0, row=0, padding=(0, 0, 0, 1), growx=1)
        self.screenGrid.setField(self.listbox, col=0, row=1, padding=(0, 0, 0, 1), growx=1)

        #self.screenGrid.setField(self.listbox, col=0, row=0, padding=(0, 0, 0, 1), growx=1)

    def validate(self):
        """Validation code goes here. Activated when 'Next' button is pressed."""

        myNodeInfo.ngid = self.listbox.current()
        NodeGroupBatch.validate(self)

        if myNode.getNodegroupNameByID(myNodeInfo.ngid) == 'unmanaged':
           screenList = [ WindowUnmanaged(database=self.database, kusuApp=kusuApp) ]
           screenFactory = ScreenFactoryImpl(screenList)
           ks = USXNavigator(screenFactory=screenFactory, screenTitle="Add Hosts - Version ${VERSION_STR}", showTrail=False)
           result = ks.run()
           if myNodeInfo.forceQuitflag:
               raise UserExitError

           if not myNodeInfo.optionDHCPMode:
              raise UserExitError

        return True, 'Success'

    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """
        pass


class BatchSelectNode:
    def __init__(self, database, kusuApp=None):
        self.database = database;
        self.kusuApp = kusuApp;

    def __call__(self):

        if myNodeInfo.forceQuitflag:
            return

        self.selectNetwork()
        self.setSyslogFilePosition()
        self.setRackNumber()

    def selectNetwork(self):

        flag = True

        if myNodeInfo.forceQuitflag:
            return

        while flag:
            try:
                networkList = self.getAvailableNetworks()

                if myNodeInfo.optionStaticHostMode:
                    pass
                else:
                    if not networkList:
                        kusuApp.stderrMessage(self.kusuApp._("addhost_nodegroup_has_no_network_error") + "\n")
                        kusuApp.exitFailedAndUnlock()

                kusuApp.stdoutMessage("\n" + self.kusuApp._("addhost_instruction_interface") + "\n")

                count = 1
                device_list = []
                for name,device,default in networkList:
                    kusuApp.stdoutMessage("%d) %s\n", count, name)
                    device_list.append(device)
                    count = count + 1

                response = raw_input(">> ")

                try:
                    result = int(response) - 1
                    if (result < 0 or result >= len(device_list)):
                        kusuApp.stderrMessage("\n%s\n" % self.kusuApp._("addhost_invalid_selection"))
                    else:
                        myNodeInfo.selectedInterface = device_list[result]
                        flag = False
                except ValueError:
                    kusuApp.stderrMessage("\n%s\n" % self.kusuApp._("addhost_invalid_selection"))

            except (KeyboardInterrupt,EOFError), e:
                kusuApp.stdoutMessage("\n" + kusuApp._("addhost_cmd_abort") + "\n")
                myNodeInfo.forceQuitflag = True
                return


    def getAvailableNetworks(self):
        networkList = []
        itemName = None
        # Get installer's available networks.
        try:
            query = "SELECT DISTINCT networks.network, networks.subnet, networks.device, networks.gateway \
                     FROM networks, nics, nodes \
                     WHERE nodes.nid=nics.nid AND nics.netid=networks.netid AND networks.usingdhcp=False \
                     AND nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller') \
                     AND networks.type = 'provision' \
                     AND (lower(networks.device) like 'eth%%' or lower(networks.device) like 'bond%%') ORDER BY device"

            self.database.execute(query)
            installerInfo = self.database.fetchall()

            # Get list of node group's available gateways.
            query = "SELECT DISTINCT networks.gateway, networks.startip FROM networks, ng_has_net \
                     WHERE ng_has_net.netid=networks.netid AND ng_has_net.ngid=%s AND networks.usingdhcp=False \
                     AND lower(networks.device) like 'eth%%'" % myNodeInfo.ngid
            self.database.execute(query)
            ngInfo = self.database.fetchall()
        except:
            raise KusuError, self.kusuApp._("DB_Query_Error\n")

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
               for ng_gateway, ng_startip in ngInfo:
                   if ng_gateway:
                      if kusu.ipfun.onNetwork(installer_network, installer_subnet, ng_gateway):

                         # If starting IP is Nothing, keep looking...
                         if not ng_startip:
                            continue

                         itemName = "%s  (%s)" % (installer_device.ljust(4), installer_gateway)
                         if defaultFlag:
                            networkList.append([itemName, installer_device, 1 ])
                         else:
                            networkList.append([itemName, installer_device, 0 ])
                         defaultFlag = 0

        return networkList

    def setSyslogFilePosition(self):
        if myNodeInfo.forceQuitflag:
            return

        filep = open("/var/log/messages", 'r')
        filep.seek(0, 2)
        myNodeInfo.syslogFilePosition = filep.tell()
        filep.close()

    def setRackNumber(self):

        if myNodeInfo.forceQuitflag:
            return

        # Prompt for Rack Number if node format requires a rack number specified.
        flag = 1
        if myNodeInfo.nodeRackNumber < 0:
           myNode.setNodegroupByID(myNodeInfo.ngid)
           if myNode.isNodenameHasRack():
               while flag:
                    kusuApp.stdoutMessage("\n" + self.kusuApp._("addhost_instructions_rack") + "\n")
                    try:

                        response = raw_input(">> ")
                        try:
                            result = int(response)
                            if result < 0:
                                kusuApp.stderrMessage("\n%s\n" % self.kusuApp._("rack_negative_number"))
                                continue
                            myNodeInfo.nodeRackNumber = result
                            flag = 0
                        except ValueError:
                            kusuApp.stderrMessage(self.kusuApp._("addhost_non_numeric_rack_number_error") + "\n", response)

                    except (KeyboardInterrupt,EOFError), e:
                        kusuApp.stdoutMessage("\n" + kusuApp._("addhost_cmd_abort") + "\n")
                        myNodeInfo.forceQuitflag = True
                        return

        myNode.setRackNumber(myNodeInfo.nodeRackNumber)


class WindowSelectNode(NodeGroupWindow,BatchSelectNode):

    name = "addhost_window_title_interface"
    msg = "addhost_instruction_interface"
    buttons = ['next_button', 'previous_button']
    #selectedInterface = None

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        BatchSelectNode.__init__(self, database, kusuApp)
        self.setHelpLine("Copyright(C) 2010 Platform Computing Inc.\t%s" % self.kusuApp._("addhost_helpline_instructions"))

    def setCallbacks(self):
        self.buttonsDict['previous_button'].setCallback_(self.backAction)
        self.buttonsDict['next_button'].setCallback_(self.nextAction)

        self.hotkeysDict['F12'] = self.F12Action
        self.hotkeysDict['F8'] = self.nextAction
        self.hotkeysDict['F5'] = self.backAction

    def drawImpl(self):
        """" Get list of network interfaces and allow user to choose one"""

        global tuiMode
        tuiMode = self.screen

        try:
            networkList = BatchSelectNode.getAvailableNetworks(self)
        except:
            self.selector.popupMsg (self.kusuApp._("Error"), self.kusuApp._("DB_Query_Error\n"))
            self.screen.finish()
            raise UserExitError

        # Static mode needs to see all the interfaces from the installer we don't care about if a network fits on any interface
        if myNodeInfo.optionStaticHostMode:
            pass
        else:
           if not networkList:
              self.selector.popupMsg (self.kusuApp._("Error"), self.kusuApp._("addhost_nodegroup_has_no_network_error"))
              self.kusuApp.unlock()
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

        BatchSelectNode.setSyslogFilePosition(self)
        myNodeInfo.selectedInterface = self.radioButtonList.getSelection()

        # Prompt for Rack Number if node format requires a rack number specified.
        flag = 1
        if myNodeInfo.nodeRackNumber < 0:
           myNode.setNodegroupByID(myNodeInfo.ngid)
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
                            self.kusuApp._("addhost_non_numeric_rack_number_error") % result[0], 2)
                        flag = 1

        myNode.setRackNumber(myNodeInfo.nodeRackNumber)
        return True, 'Success'

class BatchUnmanaged:
    def __init__(self, database, kusuApp=None):
        self.database = database;
        self.kusuApp = kusuApp;

    def __call__(self):

        if myNodeInfo.forceQuitflag:
            return

        # Run this step only if the user selected the "unmanaged" node group
        if myNodeInfo.ngid != self.database.getNgidOf('unmanaged'):
            return

        flag=True
        while flag:
            self.getUserInput()
            if myNodeInfo.forceQuitflag:
                break

            (result,errMsg) = self.validate()
            if result:
                flag=False
            else:
                kusuApp.stderrMessage(errMsg + "\n")

        if myNodeInfo.forceQuitflag:
           return

        if myNodeInfo.optionDHCPMode == False:
           kusuApp.stdoutMessage(kusuApp._("addhost_add_static_device_with_ip") + "\n",
                                 myNodeInfo.staticHostname, myNodeInfo.staticIPAddress)
           self.addStaticDevice()


    def getUserInput(self):
        kusuApp.stdoutMessage("\n" + self.kusuApp._("addhost_batch_unmanaged_device_instruction") + "\n")

        try:
            staticHostname = raw_input(self.kusuApp._("addhost_batch_unmanaged_device_hostname_prompt"))

            flag=True
            while flag:
                useDHCP = raw_input(self.kusuApp._("addhost_batch_unmanaged_device_use_dhcp_prompt"))
                if (useDHCP.strip().lower() in ['yes','y'] ):
                    myNodeInfo.optionDHCPMode = True
                    flag=False
                elif (useDHCP.strip().lower() in ['no','n'] ):
                    myNodeInfo.optionDHCPMode = False
                    flag=False
                else:
                    kusuApp.stderrMessage(self.kusuApp._("addhost_batch_unmanaged_device_use_dhcp_error") + "\n")

            if not myNodeInfo.optionDHCPMode:
                staticIPAddress = raw_input(self.kusuApp._("addhost_batch_unmanaged_device_ip_prompt"))
            else:
                staticIPAddress = ""

        except (KeyboardInterrupt,EOFError), e:
            kusuApp.stdoutMessage("\n" + kusuApp._("addhost_cmd_abort") + "\n")
            myNodeInfo.forceQuitflag = True
            return

        myNodeInfo.staticHostname = staticHostname.strip().lower()
        myNodeInfo.staticIPAddress = staticIPAddress.strip()


    def validate(self):
        """Check static host information. Return a tuple of two items indicating
        whether the validated succeeded and the corresponding error message."""

        if len(myNodeInfo.staticHostname) == 0:
            return (False, self.kusuApp._("addhost_static_device_no_host_error"))

        if myNodeInfo.staticHostname.find(' ') > 0:
            return (False, self.kusuApp._("addhost_static_device_hostname_space_error"))

        if myNode.validateNode(myNodeInfo.staticHostname):
            return (False, self.kusuApp._("addhost_static_device_hostname_used_error") % myNodeInfo.staticHostname)

        # Is what the user typed a valid IP address?
        if not kusu.ipfun.validIP(myNodeInfo.staticIPAddress) and myNodeInfo.optionDHCPMode == False:
            return (False, self.kusuApp._("addhost_static_device_invalid_ip_error") % myNodeInfo.staticIPAddress)

        if myNode.isIPUsed(myNodeInfo.staticIPAddress):
            return (False, self.kusuApp._("addhost_static_device_ip_used_error") % myNodeInfo.staticIPAddress)

        if not myNode.isIPInPrivateNet(myNodeInfo.staticIPAddress) and myNodeInfo.optionDHCPMode == False:
            return (False, self.kusuApp._("addhost_static_device_no_net_error") % myNodeInfo.staticIPAddress)

        return (True, "")

    def addStaticDevice(self):
        myNode.addUnmanagedStaticDevice(myNodeInfo.staticHostname.strip(), myNodeInfo.staticIPAddress.strip())
        myNodeInfo.forceQuitflag = True
        if pluginActions:
            pluginActions.plugins_add(myNodeInfo.staticHostname.strip())
            pluginActions.plugins_finished()


class WindowUnmanaged(NodeGroupWindow,BatchUnmanaged):
    name = "addhost_window_title_unmanaged"
    buttons = ['ok_button', 'exit_button']

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        BatchUnmanaged.__init__(self, database, kusuApp)
        self.setHelpLine("Copyright(C) 2010 Platform Computing Inc.\t%s" % self.kusuApp._("addhost_helpline_instructions"))

    def F12Action(self):
        if myNodeInfo.quitPrompt:
            result = self.selector.popupDialogBox(self.kusuApp._("addhost_window_title_exit"), self.kusuApp._("addhost_instructions_exit"),
                    (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
            if result == "no":
                return NAV_IGNORE
            if result == "yes":
                raise UserExitError
        #else:
        #    if len(myNodeInfo.nodeList):
        #        if pluginActions:
        #           pluginActions.plugins_finished()
        #    raise UserExitError

    def exitAction(self):
           self.kusuApp.unlock()
           self.screen.finish()
           os._exit(0)

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
        global tuiMode
        tuiMode = self.screen

        self.staticHostname = LabelledEntry(labelTxt=self.kusuApp._("addhost_hostname_label"), text="", width=20,
                password=0, returnExit = 0)

        self.IPEntry = LabelledEntry(labelTxt=self.kusuApp._("addhost_ipaddr_label"), text="", width=20,
                password=0, returnExit = 0)

        dhcp_enabled = int(self.database.getAppglobals('InstallerServeDHCP'))

        if dhcp_enabled:
            instruction = snack.Textbox(50, 3, self.kusuApp._("addhost_unmanaged_instructions"), scroll=0, wrap=1)
            self.dhcpCheck = snack.Checkbox(self.kusuApp._("netedit_field_dhcp"), isOn = 0)
            self.dhcpCheck.setCallback(self.checkDHCPStatus)
            self.screenGrid = snack.Grid(1, 4)
            self.screenGrid.setField(self.dhcpCheck, col=0, row=2, padding=(-30,1,0,0))
            self.screenGrid.setField(self.IPEntry, col=0, row=3, padding=(-10,1,0,0))
        else:
            instruction = snack.Textbox(50, 3, self.kusuApp._("addhost_unmanaged_instructions_with_external_dhcp"), scroll=0, wrap=1)
            self.screenGrid = snack.Grid(1, 3)
            self.screenGrid.setField(self.IPEntry, col=0, row=2, padding=(-10,1,0,0))

        self.screenGrid.setField(instruction, col=0, row=0, padding=(0,0,0,0))
        self.screenGrid.setField(self.staticHostname, col=0, row=1, padding=(-11,1,0,0))

    def validateInfo(self):
        myNodeInfo.staticHostname = self.staticHostname.value().strip().lower()
        myNodeInfo.staticIPAddress = self.IPEntry.value().strip()

        (result,errMsg) = BatchUnmanaged.validate(self)
        if not result:
            self.selector.popupStatus(self.kusuApp._("Error"), errMsg, 4)
            return NAV_NOTHING

        if myNodeInfo.optionDHCPMode == True and not int(self.database.getAppglobals('InstallerServeDHCP')):
            self.selector.popupStatus(self.kusuApp._("Error"), self.kusuApp._("Option not "), 4)
            return NAV_NOTHING

        if self.dhcp and myNodeInfo.optionDHCPMode == False:
            result = self.selector.popupStatus(self.kusuApp._("addhost_add_static_device_title"), self.kusuApp._("addhost_add_static_device_with_ip") % (myNodeInfo.staticHostname, myNodeInfo.staticIPAddress), 2)
            self.screen.finish()
            BatchUnmanaged.addStaticDevice(self)
            return NAV_QUIT
        else:
            return NAV_FORWARD

    def validate(self):
        # Adding a Static hostname via DHCP
        myNodeInfo.optionStaticHostMode = True
        return True,'Success'

    def formAction(self):
        """Any other action other than validation that takes place after the
           'Next button is pressed.
        """
        pass

class BatchNodeStatus:
    def __init__(self, database, kusuApp=None):
        self.database = database
        self.kusuApp = kusuApp
        # this flag used for manually specifying IP address scenario only
        # in this scenario, only lease DHCP IP once.
        self.specifyIPHostFound = False

    def __call__(self):

        kusuApp.stdoutMessage("\n" + kusuApp._("addhost_scanning_syslog") + "\n")
        while True:
            if (myNodeInfo.forceQuitflag):
                if (myNodeInfo.signal):
                    kusuApp.stdoutMessage("\n" + kusuApp._("addhost_cmd_abort") + "\n")
                return

            self.scanSyslogForPXEReqs()

            # Sleep for 500 msec
            time.sleep(0.5)

    def scanSyslogForPXEReqs(self):
        nodeName = None
        macAddress = None
        discoveryCheck = True

        if self.specifyIPHostFound:
            return

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
                        self.aNode = NodeFun(rack=myNodeInfo.nodeRackNumber, nodegroup=myNodeInfo.ngid)
                        self.aNode.setRankNumber(myNodeInfo.nodeRankNumber)
                        if myNodeInfo.staticIPAddrOfManagedNode:
                            # Set the flag so that addhost will ignore any other DHCP requests.
                            self.specifyIPHostFound = True
                            self.aNode.setSpecifiedIPAddr(myNodeInfo.staticIPAddrOfManagedNode)
                        try:
                            nodeName = self.aNode.addNode(macAddress, myNodeInfo.selectedInterface, installer=True, snackInstance=self.screen)
                        except:
                            nodeName = self.aNode.addNode(macAddress, myNodeInfo.selectedInterface, installer=True, snackInstance=False)

                        self.myNode.setRankNumber(myNodeInfo.nodeRankNumber)
                        self.displayAddedNode(nodeName,macAddress, self.aNode.getRankNumber())
                        kusuApp.logEvent(kusuApp._("addhost_event_discovered_node") % (nodeName,macAddress),
                                         toStdout=False)

                        if pluginActions:
                           pluginActions.plugins_add(nodeName)
                        myNodeInfo.nodeList.append(nodeName)
                        del self.aNode

                    # Replace node
                    if myNodeInfo.optionReplaceMode and discoveryCheck == False:
                       myNodeInfo.selectedInterface = self.myNode.findBootDevice(myNodeInfo.replaceNodeName)
                       # Check if the interface dhcp is PXEing from matches whats in the DB, if not don't bother trying to go further.
                       if (tokens[9][:-1] == myNodeInfo.selectedInterface or tokens[9] == myNodeInfo.selectedInterface):
                           self.displayReplacedNode(macAddress)
                           if myNode.replaceNodeEntry(myNodeInfo.replaceNodeName) == False:
                               myNodeInfo.forceQuitflag = True
                               return
                           self.myNode.replaceNICBootEntry (myNodeInfo.replaceNodeName, macAddress)
                           # Call Replace mode plugins
                           if pluginActions:
                              myNodeInfo.nodeList.append(myNodeInfo.replaceNodeName)
                              pluginActions.plugins_replaced(myNodeInfo.replaceNodeName)
                           myNodeInfo.forceQuitflag = True
                           kusuApp.logEvent(kusuApp._("addhost_event_replace_node") % myNodeInfo.replaceNodeName,
                                         toStdout=False)

                    # Adding a Static hostname w/ DHCP
                    if myNodeInfo.optionStaticHostMode and myNodeInfo.optionDHCPMode and discoveryCheck == False:
                       if (tokens[9][:-1] == myNodeInfo.selectedInterface or tokens[9] == myNodeInfo.selectedInterface):
                          self.displayUnmanagedNode(macAddress)
                          self.myNode.addUnmanagedDHCPDevice(myNodeInfo.selectedInterface, myNodeInfo.staticHostname, macAddress)

                          if pluginActions:
                             myNodeInfo.nodeList.append(myNodeInfo.staticHostname)
                             pluginActions.plugins_add(myNodeInfo.staticHostname)
                          myNodeInfo.forceQuitflag = True
                          kusuApp.logEvent(
                                kusuApp._("addhost_event_add_static_host_dhcp") % myNodeInfo.staticHostname,
                                toStdout=False)

                    del self.myNode

        # Store current position of /var/log/messages
        myNodeInfo.syslogFilePosition = filep.tell()
        filep.close()
        return NAV_IGNORE


    def displayAddedNode(self, nodeName, macAddress, rank):
        kusuApp.stdoutMessage(kusuApp._("addhost_discovered_node") + "\n", nodeName, macAddress)

    def displayReplacedNode(self, macAddress):
        kusuApp.stdoutMessage(kusuApp._("addhost_discovered_node") + "\n", myNodeInfo.replaceNodeName, macAddress)

    def displayUnmanagedNode(self, macAddress):
        kusuApp.stdoutMessage(kusuApp._("addhost_add_static_device") + "\n", myNodeInfo.staticHostname)


class WindowNodeStatus(NodeGroupWindow,BatchNodeStatus):
    name = "addhost_window_title_installing"
    buttons = ['quit_button']

    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        BatchNodeStatus.__init__(self, database, kusuApp)
        self.setScreenTimer(500)

    def exitAction(self):
        return NAV_QUIT

    def setCallbacks(self):
        self.buttonsDict['quit_button'].setCallback_(self.exitAction)
        self.hotkeysDict['F12'] = self.F12Action

    def drawImpl(self):
        global tuiMode
        tuiMode = self.screen

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

        BatchNodeStatus.scanSyslogForPXEReqs(self)

        # We must refresh or things will draw weird.
        #self.selector.refresh()

        if (myNodeInfo.forceQuitflag):
            # Someone sent a signal
            return NAV_QUIT
        else:
            return NAV_IGNORE

    def displayAddedNode(self, nodeName, macAddress, rank):
        # newly added
        # If the rank is not zero and the requested rank is in use then let user know that it will use the next available one.

        result = self.myNode.compareRankAvailable(rank)
        if result == False and myNodeInfo.inuseRank == -1:
           myNodeInfo.inuseRank = 1

        if myNodeInfo.inuseRank == 1:
           self.selector.popupStatus(self.kusuApp._("addhost_node_discovery"), "%s\n\n%s" % (self.kusuApp._("addhost_discovered_node") % (nodeName, macAddress), self.kusuApp._("addhost_discover_rank_inuse")), 3)
           myNodeInfo.inuseRank = 0
        else:
           self.selector.popupStatus(self.kusuApp._("addhost_node_discovery"), self.kusuApp._("addhost_discovered_node") % (nodeName, macAddress), 3)

        self.listbox.append("%s\t%s\t(%s)" % (nodeName, macAddress, self.kusuApp._("addhost_installing_string")), nodeName)
        self.listbox.setCurrent(nodeName)

    def displayReplacedNode(self, macAddress):
        self.selector.popupStatus(self.kusuApp._("addhost_node_discovery"), self.kusuApp._("addhost_discovered_node") % (myNodeInfo.replaceNodeName, macAddress), 3)
        self.screen.finish()

    def displayUnmanagedNode(self, macAddress):
        self.selector.popupStatus(self.kusuApp._("addhost_node_discovery"), self.kusuApp._("addhost_add_static_device") % myNodeInfo.staticHostname, 3)
        self.screen.finish()

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
    kl = kusulog.getKusuLog()
    kl.addFileHandler("/var/log/kusu/kusu.log")

    app = AddHostApp()
    app.loadPlugins()
    app.parse()
    app.run()
