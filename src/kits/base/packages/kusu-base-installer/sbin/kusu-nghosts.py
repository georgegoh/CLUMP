#!/usr/bin/python
#
# Kusu nghosts
#
# Copyright (C) 2009 Platform Computing Inc.

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

PROVISION_TYPE_KUSU = 'KUSU'
DEFAULT_PROVISION_TYPE = PROVISION_TYPE_KUSU

def getProvisionType(db):
    db.connect()
    db.execute("SELECT kvalue from appglobals WHERE kname=\'PROVISION\'")
    row = db.fetchone()
    if not row:
        return DEFAULT_PROVISION_TYPE

    return row[0]

def getNodegroupType(db, ngname):
    db.execute("SELECT type from nodegroups WHERE ngname=\'%s\'" % ngname)
    nodeGroupType = db.fetchone()
    if nodeGroupType:            
        return nodeGroupType[0].lower()

def getNgInstalltype(db, ngname):
    db.execute("SELECT installtype from nodegroups WHERE ngname=\'%s\'" % ngname)
    nodeGroupInstallType = db.fetchone()
    if nodeGroupInstallType:            
        return nodeGroupInstallType[0].lower()
    
def getNgnameForNode(db, node):
    db.execute("SELECT ngname FROM nodegroups,nodes WHERE \
                nodegroups.ngid=nodes.ngid AND nodes.name=\'%s\'" % node)
    nodeGroupName = db.fetchone()
    if nodeGroupName:
        return nodeGroupName[0]

# prompt user for rack if :
#  - destination nodegroup nameformat require a rack number and no rack number is provided and,
#     1) preserve_node_ip is not set to 1, or
#     2) preserve_node_ip is set to 1, source nodegroup and destination nodegroup have different
#        nameformat and the compute does not have an old hostname in the nameformat of the 
#        destination nodegroup.
def rackPromptRequired(preserve_node_ip, node_record, has_rack, dst_ng, ng_list=[], node_list=[]):
    if node_record.isNodenameHasRack() and not has_rack:
        if preserve_node_ip == '1':
            if bool(ng_list) and node_record.allNodegroupsHaveSameNameFormat(ng_list):
                if not node_record.nodegroupNameFormatMatches(ng_list[0], dst_ng):
                    nodelist = node_record.getAllNodesInNodeGroups(ng_list)
                    if not node_record.checkNodesForOldHostname(nodelist, dst_ng):
                        return True
            if bool(node_list) and node_record.allNodesHaveSameNameFormat(node_list):
                src_ng = node_record.getNodegroupFromNode(node_list[0])
                if not node_record.nodegroupNameFormatMatches(src_ng, dst_ng):
                    if not node_record.checkNodesForOldHostname(node_list, dst_ng):
                        return True
        else:
            return True
    return False

def filterUnmanagedNodes(nodes, nodefun):
    """
    Given a list of nodes, return a list of nodes that
    belong to the unmanaged node group.
    """
    unmanaged_nodes = []
    for node in nodes:
        node_info = nodefun.getNodeInformation(node)
        ngid = node_info[node][0]['nodegroupid']
        ngname = nodefun.getNodegroupNameByID(ngid)
        if "unmanaged" == ngname:
            unmanaged_nodes.append(node)
    return unmanaged_nodes

def writeMacFile(db, nodes, macList, targetNG, nodefun):
    """
    Given a list of nodes, write out a mac file in the format "<mac>, <ip>, <name>, <uid>"
    for each node. This mac file will be used by addhosts to re-create nodes
    that were being moved.
    Returns the file created.
    """
    db.connect()
    (fd, tmpfile) = tempfile.mkstemp()
    tmpname = os.fdopen(fd, 'w')

    # We dont want the IP address to be preserved always
    preserveNodeIP = db.getAppglobals('PRESERVE_NODE_IP')

    for node in nodes:
        try:
            db.execute("SELECT nics.ip, nodes.uid, networks.device FROM nics,nodes,networks \
                        WHERE nics.nid=nodes.nid AND nodes.name='%s' AND nics.netid=networks.netid \
                        AND (nics.boot=True OR lower(networks.device)='bmc')" % node)
            data = db.fetchall()
            ip = uid = bmc_ip = None
            for r_ip, r_uid, r_nic in data:
                if r_nic.lower() == 'bmc':
                    bmc_ip = r_ip
                else:
                    ip = r_ip
                    uid = r_uid

            if preserveNodeIP == '1':
                mac = macList[node]
                # get the target's ngid and nameformat.
                db.execute("SELECT ngid,nameformat FROM nodegroups WHERE \
                            nodegroups.ngname=\'%s\'" % targetNG)
                if db.rowcount < 1: # cannot find target ngid/nameformat.
                    # no hostname in the mac file, rely on addhost.
                    _writeMacLines(tmpname, macList[node], ip, bmc_ip, None, uid)
                    continue

                targetNG_id, targetNG_nameformat = db.fetchone()
                # Check if alteregos history for this node has the target nodegroup.
                # If yes, then use the format, rack and rank from the history.
                name = nodefun.retrieveHostnameFromAlteregos(mac, targetNG_id)
                if name:
                    _writeMacLines(tmpname, macList[node], ip, bmc_ip, name, uid)
                    continue

                # from the node's current nodegroup, get the nameformat.
                db.execute("SELECT nameformat FROM nodes,nodegroups WHERE \
                        nodes.ngid=nodegroups.ngid and name=\'%s\'" % node)
                if db.rowcount < 1: # cannot find nameformat.
                    # no nameformat found, leave hostname section empty in mac file
                    # rely on addhost to generate hostname.
                    _writeMacLines(tmpname, macList[node], ip, bmc_ip, None, uid)
                    continue
                
                currNG_nameformat = db.fetchone()[0]
                # check if the current nodegroup has the same nameformat as the
                # target nodegroup. If yes, then the same hostname can be used.
                if targetNG_nameformat == currNG_nameformat:
                    _writeMacLines(tmpname, macList[node], ip, bmc_ip, node, uid)
                    continue


                # from the node's history(in alteregos), get the first name
                # matching the target's nameformat.
                db.execute("SELECT name FROM alteregos,nodegroups WHERE \
                        alteregos.ngid=nodegroups.ngid and alteregos.mac=\'%s\' and \
                        nodegroups.nameformat=\'%s\'" % (mac, targetNG_nameformat))
                if db.rowcount < 1:
                    # no nameformat found, leave hostname section empty in mac file
                    # rely on addhost to generate hostname.
                    _writeMacLines(tmpname, macList[node], ip, bmc_ip, None, uid)
                    continue

                matching_name = db.fetchone()[0]
                # check if any of the other alteregos has the same nameformat.
                if matching_name:
                    _writeMacLines(tmpname, macList[node], ip, bmc_ip, matching_name, uid)
                    continue
                else:
                    _writeMacLines(tmpname, macList[node], ip, bmc_ip, None, uid)
            else:
                #Not preserve node's IP
                _writeMacLines(tmpname, macList[node], None, bmc_ip, None, uid)
        except:
            tmpname.write("%s\n" % macList[node])
    tmpname.close()
    return tmpfile

def _writeMacLines(file, mac, ip=None, bmc_ip=None, name=None, uid=None):
    file.write("%s,%s,%s,%s,%s\n" % (mac, ip or '', name or '', uid or '', bmc_ip or ''))


def writeUnmanagedHostsFile(db, nodes):
    """
    Given a list of nodes, write out a unmanaged file in the format "<name>:<ip>"
    for each node. This mac file will be used by addhosts to add nodes
    that were being moved to unmanaged nodegroup.
    Returns the file created.
    """
    db.connect()
    (fd, tmpfile) = tempfile.mkstemp()
    tmpname = os.fdopen(fd, 'w')

    try:
        # get the target's nameformat.
        db.execute("SELECT nameformat FROM nodegroups WHERE \
                    nodegroups.ngname='unmanaged'")
        if db.rowcount < 1: # cannot find target nameformat.
            # Writing unmanaged hosts file will not proceed if nameformat
            # cannot be retrieved from DB
            tmpname.close()
            return tmpfile

        targetNG_nameformat = db.fetchone()[0]
        # Get the default name without index
        defaultName = targetNG_nameformat.split("#")[0]

        # Get those unmanaged nodes with names starting with the default name
        db.execute("SELECT nodes.name FROM nodes,nodegroups WHERE \
                    nodes.ngid=nodegroups.ngid AND \
                    nodegroups.ngname='unmanaged' AND \
                    nodes.name LIKE \'%s\%%\'" % defaultName)
        nodeNames = db.fetchall()

        index = 0
        # If unmanaged nodes with names starting with default name -- "device" (e.g. device000) exist,
        # get the maximum index, set the default starting index for the nodes to be added as
        # maximum index + 1. For example:
        # If the unmanaged nodes with names starting with "device" has the maximum index 3,
        # then the starting index for the new unmanaged nodes to be added is 3+1=4
        if nodeNames:
            lastRsvName = sorted(nodeNames)[-1][0]
            lastRsvIndexStr = lastRsvName.split(defaultName)[1]
            if lastRsvIndexStr.isdigit():
                index = int(lastRsvIndexStr) + 1

    except:
        tmpname.close()
        return tmpfile

    else:
        for node in nodes:
            try:
                # Retrieve the IP address of the node
                db.execute("SELECT nics.ip FROM nics,nodes WHERE nics.nid=\
                            nodes.nid AND nodes.name=\'%s\' AND boot=True" % node)
                ip = db.fetchone()
                # The default node name will combine the default name and the index
                defaultNodeName = defaultName + "%03d" % index
                tmpname.write("%s:%s\n" % (defaultNodeName, ip[0]))
                index += 1
            except:
                # Skip the node information if its IP address cannot be retrieved from DB
                continue

    tmpname.close()
    return tmpfile

class NodeMemberApp(object, KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

    def toolVersion(self, option, opt, value, parser):
        """ 
        toolVersion()
        Prints out the version of the tool to screen. 
        """

        print "kusu-nghosts version %s" % self.version
        self.unlock()
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
        self.parser.add_option("-m", "--move-hosts", action="callback",
                                callback=self.varargs, dest="movehosts", help=kusuApp._("nghosts_move_hosts_usage"))
        #self.parser.add_option("-r", "--reinstall", action="store_true", dest="reinstall", help=kusuApp._("nghosts_reinstall_usage"))
        self.parser.add_option("-a", "--rack", type="int", action="store", dest="racknumber", help=kusuApp._("nghosts_rack_usage"))

        (self._options, self._args) = self.parser.parse_args(sys.argv[1:])

    def nxor(self, *args):
        """nxor(varargs args)
        N-way function, only one condition may be true otherwise false. """

        return len([x for x in args if x]) == 1

    def getActionDesc(self):
        return "Move nodes to nodegroup"

    def run(self):
        """run()
        Run the application """
       
        global database

        if os.geteuid() != 0:
            print kusuApp._("nonroot_execution\n")
            sys.exit(-1)

        # Check if kusu-nghosts is in use, if so abort running kusu-addhost.
        if os.path.isfile("/var/lock/subsys/kusu-addhost"):
           self.logErrorEvent(self._("nghosts_addhost_lock"))
           sys.exit(-1)

        if self.islock():
           self.logErrorEvent(self._("program_already_inuse") % ('Kusu-nghosts', 'kusu-nghosts')) # (program name, lock file name)
           sys.exit(-1)

        # Parse command options
        self.parseargs()
            
        self.lock() 

        # Don't allow option -l -g -t to be used together. Mutually Exclusive.
        if (not self.nxor(bool(self._options.allnodegroups), bool(self._options.listnodegroup), bool(self._options.togroup))):
                    if (bool(self._options.allnodegroups) == False and bool(self._options.listnodegroup) == False \
                        and bool(self._options.togroup) == False):
                        pass
                    else:
                        self.unlock()
                        self.parser.error(self._("nghosts_options_exclusive"))

        # Don't allow option -m -f to be used together. Mutually Exclusive.
        if (not self.nxor(bool(self._options.movegroups), bool(self._options.movehosts))):
            if not bool(self._options.movegroups) and not bool(self._options.movehosts):
                pass
            else:
                self.unlock()
                self.parser.error(self._("nghosts_m_f_options_exclusive"))

        # Non required values, if not set default to these            
        #if not bool(self._options.reinstall):
        #        self._options.reinstall = False
        #else:
        #        self._options.reinstall = True
        
        # Handle -a option
        if self._options.racknumber:
            result = int(self._options.racknumber)
            if result < 0:
                self.logErrorEvent(self._("rack_negative_number"))
                self.exitFailedAndUnlock(-1)

        # Handle -r option
        #if not bool(self._options.reinstall):
        #        self._options.reinstall = False
        #else:
        #        self._options.reinstall = True
          
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
            self.unlock()
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
                database.execute("select nodes.name, nodes.state from nodes WHERE NOT nodes.name=(SELECT kvalue FROM appglobals \
                                  WHERE kname='PrimaryInstaller' AND nodes.ngid=%s ORDER BY name)" % ngid)
                nodes = database.fetchall()
                if len(nodes):
                    print "%s" % self._options.listnodegroup
                    print "%s" % "-" * len(self._options.listnodegroup)
                    for node, nodestate in nodes:
                       print "%s".ljust(5) % node + "%s".rjust(1) % nodestate
                    print "\n"
            except:
                sys.stderr.write(self._("options_invalid_nodegroup") + "\n")
                self.exitFailedAndUnlock(-1)
            self.unlock()
            sys.exit(0)

        # Handle -t option - Move to this node group.
        if bool(self._options.togroup):
            if not bool(self._options.movegroups) and not bool(self._options.movehosts):
                    self.unlock()
                    self.parser.error("%s\n" % self._("nghosts_options_togroup_options_needed"))
            else:
                    flag = 1
                    badnodes = []
                    nodesList = []
                    moveIPList = []
                    macsList = {}
                    myinterface = ""
                    nodeRecord = NodeFun()
                    self.logEvent(self._("nghosts_event_move_nodes") % self._options.togroup, 
                                  toStdout=False)

                    # If nodegroups is unmanaged throw an error
                   # if self._options.togroup.strip() == 'unmanaged':
                   #    self.unlock()
                   #    self.parser.error(self._("options_invalid_nodegroup"))

                    # Validate if the nodegroup exists
                    testng,val = nodeRecord.validateNodegroup(self._options.togroup)
                    if testng == False:
                       self.logErrorEvent(self._("options_invalid_nodegroup"))
                       self.exitFailedAndUnlock(-1)                       

                    # Get provision type.
                    provision_type = getProvisionType(database)

                    # Get install type
                    insttype = getNgInstalltype(database, self._options.togroup.strip())

                    # Find out the type of the destination nodegroup
                    togroup_type = getNodegroupType(database, self._options.togroup.strip())

                    nodeRecord.setNodegroupByName(self._options.togroup)
                    nodeRecord.getNodeFormat()
                                        
                    # Are we in IP/hostname preserve mode?
                    preserveNodeIP = database.getAppglobals('PRESERVE_NODE_IP')

                    # Check if the selected node format has a rack. If not(and we 
                    # are not in PRESERVE_NODE_IP mode), then prompt for it.
                    if rackPromptRequired(preserveNodeIP, nodeRecord, self._options.racknumber!=None,
                                                                 self._options.togroup.strip(), 
                                                                      self._options.movegroups,
                                                                       self._options.movehosts):
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
                        # Check if there is a mix of multiboot/non-multiboot.
                        # If there is, then we don't support and exit.
                        # We check by finding out whether the first nodegroup is
                        # multiboot or not. Then all the rest of the nodegroups must
                        # be the same, or error out.
                        first_ng_installtype = getNgInstalltype(database,
                                               self._options.movegroups[0])
                        first_ng_is_multiboot = (first_ng_installtype == 'multiboot')
                        first_ng_is_not_multiboot = not first_ng_is_multiboot
                        for ng in self._options.movegroups:
                            # Get origin install type
                            origin = getNgInstalltype(database, ng.strip())
                            if origin == 'multiboot' and first_ng_is_multiboot:
                                pass
                            elif origin != 'multiboot' and first_ng_is_not_multiboot:
                                pass
                            else:
                                msg = self._("Cannot move the supplied list of nodegroups(mixed multiboot and non-multiboot).")
                                self.logErrorEvent(msg)
                                self.unlock()
                                sys.exit(-1)
                            self.origin_is_multiboot = first_ng_is_multiboot

                        # Do not allow moving nodes from "unmanaged" to "installer" nodegroup
                        # for HP-ICE environment.
                        if provision_type != PROVISION_TYPE_KUSU and togroup_type == 'installer' and \
                                'unmanaged' in self._options.movegroups:
                            print self._("Error: Moving nodes from unmanaged to installer nodegroup is not allowed.")
                            self.exitFailedAndUnlock(-1)                       

                        moveList, ipList, macList, badList, interface = nodeRecord.moveNodegroups(self._options.movegroups, self._options.togroup)
                        nodesList += moveList 
                        moveIPList += ipList
                        myinterface = interface
                        if badList:
                            msg = ''
                            for node in badList:
                                msg += '%s (%s)\n' % (node[0], node[1])
                            self.logErrorEvent(self._('The following nodes cannot be moved:\n') + msg)
                        macsList.update(macList)
           
                    if bool(self._options.movehosts):
                        for node in self._options.movehosts:
                            if not nodeRecord.validateNode(node):
                               print self._("Node not found: %s" % node)
                               badnodes.append(node)

                        for node in badnodes:
                               self._options.movehosts.remove(node)

                        if not self._options.movehosts:
                           msg = self._("There are no valid nodes to move to the node group '%s'" % self._options.togroup)
                           self.logErrorEvent(msg)
                           self.unlock()
                           sys.exit(-1)

                        else:
                            # Check if there is a mix of multiboot/non-multiboot.
                            # If there is, then we don't support and exit.
                            # We check by finding out whether the first node is
                            # multiboot or not. Then all the rest of the nodes must
                            # be the same, or error out.
                            first_node_ng = getNgnameForNode(database, self._options.movehosts[0].strip())
                            first_node_installtype = getNgInstalltype(database, first_node_ng)
                            first_node_is_multiboot = (first_node_installtype == 'multiboot')
                            first_node_is_not_multiboot = not first_node_is_multiboot
                            for node in self._options.movehosts:
                                # Get origin install type
                                ng = getNgnameForNode(database, node.strip())
                                origin = getNgInstalltype(database, ng)
                                if origin == 'multiboot' and first_node_is_multiboot:
                                    pass
                                elif origin != 'multiboot' and first_node_is_not_multiboot:
                                    pass
                                else:
                                    msg = self._("Cannot move the supplied list of nodes(mixed multiboot and non-multiboot).")
                                    self.logErrorEvent(msg)
                                    self.unlock()
                                    sys.exit(-1)
                            self.origin_is_multiboot = first_node_is_multiboot

                            # Do not allow moving nodes from "unmanaged" to "installer" nodegroup
                            # for HP-ICE environment.
                            if provision_type != PROVISION_TYPE_KUSU and togroup_type == "installer":
                                unmanaged_nodes = filterUnmanagedNodes(self._options.movehosts, nodeRecord)
                                if unmanaged_nodes:
                                    print self._("Error: The following nodes are not allowed to move from unmanaged to installer nodegroup:")
                                    for node in unmanaged_nodes:
                                        print self._("    %s" % node)
                                    self.exitFailedAndUnlock(-1)                       

                            moveList, ipList, macList, badList, getinterface = nodeRecord.moveNodes(self._options.movehosts, self._options.togroup, rack=self._options.racknumber)
                            nodesList += moveList
                            moveIPList += ipList
                            if getinterface:
                                myinterface = getinterface
                            macsList.update(macList)

                    if nodesList:
                        print self._("Will move the following hosts: [%s] to the node group '%s'" % (string.join(Set(nodesList), ", "), self._options.togroup))

                    if not nodesList:
                       msg = self._("Could not move the requested nodes to the '%s' node group. They may be already in the same node group or do not have a valid network to associate them to the new node group." % self._options.togroup)
                       if insttype == 'multiboot':
                           msg += " And if these nodes are configured with BMC IP, the target nodegroup must have the same BMC network."
                       self.logErrorEvent(msg)
                       self.unlock()
                       sys.exit(-1)
                    else:
                       if badList:
                            msg = ''
                            for node in badList:
                                msg += '%s (%s)\n' % (node[0], node[1])
                            self.logErrorEvent(self._('The following nodes cannot be moved:\n') + msg)

                    if self._options.togroup == 'unmanaged':
                        # Create temp unmanaged hosts file
                        tmpfile = writeUnmanagedHostsFile(database, Set(nodesList))
                    else:
                        # Create temp mac file
                        tmpfile = writeMacFile(database, Set(nodesList), macList, self._options.togroup, nodeRecord)

                    print self._("nghosts_moving_nodes_progress")

                    self.unlock() 
                    ret = os.system("/opt/kusu/sbin/kusu-addhost --remove %s > /dev/null 2>&1" % string.join(Set(nodesList), ' '))
                    if ret:
                        msg = self._("ERROR : kusu-addhost failed to remove nodes. Return code: %s" % ret)
                        self.logErrorEvent(msg)
                        sys.exit(-1)

                    if self._options.togroup == 'unmanaged':
                        # Add the unmanaged nodes
                        os.system("/opt/kusu/sbin/kusu-addhost --file=%s --nodegroup='unmanaged' < /dev/null 2>&1" % (tmpfile))
                    else:
                        # Add these back using mac file
                        if self._options.racknumber >= 0:
                            os.system("/opt/kusu/sbin/kusu-addhost --file=%s --node-interface=%s --nodegroup='%s' --rack=%s > /dev/null 2>&1" % (tmpfile, myinterface, self._options.togroup, self._options.racknumber))
                        else:
                            os.system("/opt/kusu/sbin/kusu-addhost --file=%s --node-interface=%s --nodegroup='%s' > /dev/null 2>&1" % (tmpfile, myinterface, self._options.togroup))

                        self.lock()
                    # If the user wants to reinstall the nodes check if the option is selected or not.
                    #if bool(self._options.reinstall):
                    #    if self._options.togroup != "unmanaged":
                    #       print self._("nghosts_reinstall_nodes_progress")

                    # Call PDSH reboot here if the move does not involve the
                    # unmanaged nodegroup as the source or destination.
                    #

                    # Check provision type. Only reboot for Kusu.
                        if provision_type == PROVISION_TYPE_KUSU:
                            if not self.origin_is_multiboot and not insttype == 'multiboot':
                                rn = syncfun()
                                rn.runPdsh(moveIPList, "reboot < /dev/null > /dev/null 2>&1 &")

                        self.unlock()

                    os.remove(tmpfile)                    
                    self.logEvent(self._("nghosts_event_finish_move_nodes") % self._options.togroup, 
                                  toStdout=False)
                    sys.exit(0)
            
        # Handle -n without -t
        if bool(self._options.movehosts) and not bool(self._options.togroup):
            self.unlock()
            self.parser.error(self._("nghosts_options_missing_togroup"))
        
        # Handle -f without -t
        if bool(self._options.movegroups) and not bool(self._options.togroup):
            self.unlock()
            self.parser.error(self._("nghosts_options_missing_togroup"))
            
        elif self._options.movehosts == []:
            self.unlock()
            self.parser.error(self._("nghosts_options_nodes_missing"))

        elif self._options.movegroups == []:
            self.unlock()
            self.parser.error(self._("nghosts_options_groups_missing"))
            
        if len(sys.argv[1:]) > 0:
            if (not bool(self._options.allnodegroups) or not self._options.listnodegroup or not bool(self._options.togroup)):
                self.unlock()
                self.parser.error(self._("nghosts_options_required_options"))
                
        # Screen ordering
        screenList = [ MembershipMainWindow(database=database, kusuApp=kusuApp) ]

        screenFactory = ScreenFactoryImpl(screenList)
        ks = USXNavigator(screenFactory=screenFactory, screenTitle="Node Membership Editor - Version ${VERSION_STR}", showTrail=False)
        ks.run()
        self.unlock()


class SelectNodesWindow(USXBaseScreen):
    name = "nghosts_window_title_select_node"
    msg = "nghosts_instruction_select_node"
    buttons = [ 'move_button', 'previous_button', 'quit_button' ]
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2010 Platform Computing Inc.\t%s" % self.kusuApp._("helpline_instructions"))
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
        rack = None
        needRack = False
        nodeRecord = NodeFun()

        if self.nodeCheckbox.getSelection() == [] or self.nodegroupCheckbox.getSelection() == []:            
            self.selector.popupMsg(self.kusuApp._("Error"), self.kusuApp._("nghosts_nothing_selected"))
            return NAV_NOTHING

        if self.nodeCheckbox.getSelection() == [] or len(self.nodegroupCheckbox.getSelection()) > 1:
            self.selector.popupMsg(self.kusuApp._("Error"), "Too many destination nodegroups selected choose only one")
            return NAV_NOTHING

        movehosts = self.nodeCheckbox.getSelection()
        # Check if there is a mix of multiboot/non-multiboot.
        # If there is, then we don't support and exit.
        # We check by finding out whether the first node is
        # multiboot or not. Then all the rest of the nodes must
        # be the same, or display error.
        first_node_ng = getNgnameForNode(database, movehosts[0].strip())
        first_node_installtype = getNgInstalltype(database, first_node_ng)
        first_node_is_multiboot = (first_node_installtype == 'multiboot')
        first_node_is_not_multiboot = not first_node_is_multiboot
        for node in movehosts:
            # Get origin install type
            ng = getNgnameForNode(database, node.strip())
            origin = getNgInstalltype(database, ng)
            if origin == 'multiboot' and first_node_is_multiboot:
                pass
            elif origin != 'multiboot' and first_node_is_not_multiboot:
                pass
            else:
                self.selector.popupMsg(self.kusuApp._("Error"), "Cannot move the supplied list of nodes(mixed multiboot and non-multiboot).")
                return NAV_NOTHING
        self.origin_is_multiboot = first_node_is_multiboot

        self.kusuApp.logEvent(self.kusuApp._("nghosts_event_move_nodes") % self.nodegroupCheckbox.getSelection()[0], 
                                  toStdout=False)
                    
        result = self.selector.popupDialogBox(self.kusuApp._("nghosts_window_title_move_prompt"), \
                 self.kusuApp._("nghosts_instructions_move_nodes"), (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            moveList, moveIPList, macList, badList, interface = nodeRecord.moveNodes(self.nodeCheckbox.getSelection(), self.nodegroupCheckbox.getSelection()[0])            

            # None of the nodes could be moved at all. This maybe because the nodes are already in the node group or the nodes networks do not map
            # to the new destination node group.
            if not moveList:
               msg = self.kusuApp._("Could not move the selected nodes to the '%s' node group. They may be already in the same node group or do not have a valid network to associate them to the new node group.") % self.nodegroupCheckbox.getSelection()[0]
               if self.origin_is_multiboot:
                   msg += " And if these nodes are configured with BMC IP, the target nodegroup must have the same BMC network."
               self.kusuApp.logErrorEvent(msg, toStderr=False)
               self.selector.popupMsg(self.kusuApp._("Notice"), msg)
            else:
               nodeRecord.setNodegroupByName(self.nodegroupCheckbox.getSelection()[0])
               nodeRecord.getNodeFormat()

               # Are we in IP/hostname preserve mode?
               preserveNodeIP = database.getAppglobals('PRESERVE_NODE_IP')
               # Check if the selected node format has a rack. If not(and we
               # are not in PRESERVE_NODE_IP mode), then prompt for it.
               if rackPromptRequired(preserveNodeIP, nodeRecord, rack!=None, 
                                     self.nodegroupCheckbox.getSelection()[0], 
                                                                [], movehosts):
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
                  msg = self.kusuApp._("Only can move %d nodes to node group '%s', the following nodes cannot be moved:\n") % (len(moveList), self.nodegroupCheckbox.getSelection()[0])
                  for node in badList:
                      msg += '%s (%s)\n' % (node[0], node[1])
                  self.kusuApp.logErrorEvent(msg, toStderr=False)
                  self.selector.popupMsg(self.kusuApp._("Notice"), msg)

               # Get provision type
               provision_type = getProvisionType(self.database)

               # Get type of destination nodegroup
               destNodegroupType = getNodegroupType(self.database, self.nodegroupCheckbox.getSelection()[0])

               # Get installer type of destination nodegroup
               insttype = getNgInstalltype(self.database, self.nodegroupCheckbox.getSelection()[0])

               # Do not allow moving nodes from "unmanaged" to "installer" nodegroup
               # for HP-ICE environment.
               if provision_type != PROVISION_TYPE_KUSU and destNodegroupType == "installer":
                   unmanaged_nodes = filterUnmanagedNodes(moveList, nodeRecord)
                   if unmanaged_nodes:
                       msg = "Moving of the following nodes from unmanaged to an installer nodegroup is not allowed:\n\n%s" % "\n".join(unmanaged_nodes)
                       self.selector.popupMsg(self.kusuApp._("Error"), msg)
                       return NAV_NOTHING

               if insttype == 'unmanaged':
                   # Create temp unmanaged hosts file
                   tmpfile = writeUnmanagedHostsFile(database, moveList)
               else:
                   # Create temp mac file
                   tmpfile = writeMacFile(database, moveList, macList, self.nodegroupCheckbox.getSelection()[0], nodeRecord)

               # Call kusu-addhost to delete these nodes
               progDialog = ProgressDialogWindow(self.screen, self.kusuApp._("nghosts_moving_nodes"), self.kusuApp._("nghosts_moving_nodes_progress"))

               self.kusuApp.unlock()
               ret = os.system("/opt/kusu/sbin/kusu-addhost --remove %s > /dev/null 2>&1" % string.join(moveList, ' '))
               if ret:
                   msg = self.kusuApp._("ERROR : kusu-addhost failed to remove nodes. Return code: %s" % (os.WEXITSTATUS(ret)))
                   self.kusuApp.logErrorEvent(msg, toStderr=False)
                   self.selector.popupMsg(self.kusuApp._("Error"), msg)
                   return NAV_NOTHING

               if insttype == 'unmanaged':
                   # Add the unmanaged nodes
                   os.system("/opt/kusu/sbin/kusu-addhost --file=%s --nodegroup='unmanaged' > /dev/null 2>&1" % (tmpfile))
               else:
                   # Add these back using mac file
                   if needRack:
                      os.system("/opt/kusu/sbin/kusu-addhost --file=%s --node-interface=%s --nodegroup='%s' --rack=%s > /dev/null 2>&1" % (tmpfile, interface, self.nodegroupCheckbox.getSelection()[0], rack))
                   else:
                      os.system("/opt/kusu/sbin/kusu-addhost --file=%s --node-interface=%s --nodegroup='%s' > /dev/null 2>&1" % (tmpfile, interface, self.nodegroupCheckbox.getSelection()[0]))                   

                   self.kusuApp.lock()
                   progDialog.close()

               # If the user wants to reinstall the nodes check if the option is selected or not.
               # if self.reinstcheckbox.value() and self.nodegroupCheckbox.getSelection()[0] != "unmanaged":
               #    progDialog = ProgressDialogWindow(self.screen, self.kusuApp._("nghosts_reinstalling_nodes"), \
               #                 self.kusuApp._("nghosts_reinstall_nodes_progress"))

               # Call PDSH here
                   if provision_type == PROVISION_TYPE_KUSU:
                       if not self.origin_is_multiboot and not insttype == 'multiboot':
                           rn = syncfun()
                           rn.runPdsh(moveIPList, "reboot < /dev/null > /dev/null 2>&1 &")

                   
               progDialog.close()
               # Remove temp file
               os.remove(tmpfile)
               self.kusuApp.logEvent(self.kusuApp._("nghosts_event_finish_move_nodes") % self.nodegroupCheckbox.getSelection()[0], 
                    toStdout=False)
                       
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
        haveNodes = False
        self.screenGrid  = snack.Grid(1, 6)
        self.nodeCheckbox = snack.CheckboxTree(height=8, width=35, scroll=1)
        self.nodegroupCheckbox = snack.CheckboxTree(height=8, width=40, scroll=1)
        instruction = snack.Textbox(65, 1, self.kusuApp._(self.msg), scroll=0, wrap=1)
        labeltokens = self.kusuApp._("nghosts_source_label").split(',')
        label = snack.Label(self.kusuApp._("%s %s" % (labeltokens[0].ljust(29),labeltokens[1])))
        #self.reinstcheckbox = snack.Checkbox(self.kusuApp._("Reinstall Nodes"), isOn = 0)
        query = 'SELECT ngname, ngid FROM nodegroups ORDER BY ngid'
        
        try:
            self.database.connect()
            self.database.execute(query)
            nodegroups = self.database.fetchall()
        except:
            self.screen.finish()
            print self.kusuApp._("DB_Query_Error\n")
            self.unlock()
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
                self.unlock()
                sys.exit(-1)

            # If the node group is empty don't display it.
            provision_type = getProvisionType(self.database)
            if len(nodes) > 0:
                if not (nodegroup[0] == "unmanaged" and provision_type == PROVISION_TYPE_KUSU):
                    haveNodes = True
                    self.nodeCheckbox.append(nodegroup[0])
                    self.nodeGroupNames.append(nodegroup[0])
                    self.nodegroupDict[nodegroup[0]] = []
                    
                    for node in nodes:
                        self.nodeCheckbox.addItem(node[0], (count, snack.snackArgs['append']))
                        self.nodegroupDict[nodegroup[0]].append(node[0])

                    count += 1

        for group in nodegroups:
            self.nodegroupCheckbox.append(group[0])
       
        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1))
        self.screenGrid.setField(label, 0, 1, padding=(6,0,0,0), anchorLeft=1)
        self.screenGrid.setField(self.nodeCheckbox, 0, 2, padding=(0,0,40,0),anchorLeft=1)
        self.screenGrid.setField(self.nodegroupCheckbox, 0, 3, padding=(0,-8,-1,0),anchorRight=1)
        #self.screenGrid.setField(self.reinstcheckbox, 0, 4, padding=(0,1,0,0), anchorLeft=1)
           
        # If there's no other nodes besides installer, then exit gracefully.
        if haveNodes == False:
           self.selector.popupMsg(self.kusuApp._("Notice"), self.kusuApp._("There are no nodes available. Exiting."))
           self.kusuApp.unlock()
           self.screen.finish()
           os._exit(-1)
     
class SelectNodegroupsWindow(USXBaseScreen):
    name = "nghosts_window_title_select_nodegroup"
    msg = "nghosts_instruction_select_nodegroup"

    buttons = [ 'move_button', 'previous_button', 'quit_button' ]
    hotkeysDict = {}
    
    def __init__(self, database, kusuApp=None, gridWidth=45):
        USXBaseScreen.__init__(self, database, kusuApp, gridWidth)
        self.setHelpLine("Copyright(C) 2010 Platform Computing Inc.\t%s" % self.kusuApp._("helpline_instructions"))
          
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
        rack = None
        needRack = False
        nodeRecord = NodeFun()

        if self.srcNodegroupsCheckbox.getSelection() == [] or self.destNodegroupCheckbox.getSelection() == []:            
            self.selector.popupMsg(self.kusuApp._("Error"), self.kusuApp._("nghosts_nothing_selected_groups"))
            return NAV_NOTHING

        if self.srcNodegroupsCheckbox.getSelection() == [] or len(self.destNodegroupCheckbox.getSelection()) > 1:
            self.selector.popupMsg(self.kusuApp._("Error"), "Too many destination nodegroups selected choose only one")
            return NAV_NOTHING

        movegroups = self.srcNodegroupsCheckbox.getSelection()
        # Check if there is a mix of multiboot/non-multiboot.
        # If there is, then we don't support and exit.
        # We check by finding out whether the first nodegroup is
        # multiboot or not. Then all the rest of the nodegroups must
        # be the same, or error out.
        first_ng_installtype = getNgInstalltype(database, movegroups[0])
        first_ng_is_multiboot = (first_ng_installtype == 'multiboot')
        first_ng_is_not_multiboot = not first_ng_is_multiboot
        for ng in movegroups:
            # Get origin install type
            origin = getNgInstalltype(database, ng.strip())
            if origin == 'multiboot' and first_ng_is_multiboot:
                pass
            elif origin != 'multiboot' and first_ng_is_not_multiboot:
                pass
            else:
                self.selector.popupMsg(self.kusuApp._("Error"), "Cannot move the supplied list of nodegroups(mixed multiboot and non-multiboot).")
                return NAV_NOTHING
        self.origin_is_multiboot = first_ng_is_multiboot

        # Get provision type
        provision_type = getProvisionType(self.database)

        # Get type of destination nodegroup
        destNodegroupType = getNodegroupType(self.database, self.destNodegroupCheckbox.getSelection()[0])

        # Get installer type of destination nodegroup
        insttype = getNgInstalltype(self.database, self.destNodegroupCheckbox.getSelection()[0])

        # For HP-ICE, do no allow moving of nodes from unmanaged to installer nodegroup
        if provision_type != PROVISION_TYPE_KUSU and destNodegroupType == 'installer' and \
                'unmanaged' in self.srcNodegroupsCheckbox.getSelection():
            self.selector.popupMsg(self.kusuApp._("Error"), "Moving nodes from unmanaged to an installer nodegroup is not allowed")
            return NAV_NOTHING

        self.kusuApp.logEvent(self.kusuApp._("nghosts_event_move_nodes") % self.destNodegroupCheckbox.getSelection()[0],
                                  toStdout=False)

        result = self.selector.popupDialogBox(self.kusuApp._("nghosts_window_title_move_prompt"), \
                 self.kusuApp._("nghosts_instructions_move_nodegroups"), (self.kusuApp._("no_button"), self.kusuApp._("yes_button")))
        if result == "no":
            return NAV_NOTHING
        if result == "yes":
            moveList, moveIPList, macList, badList, interface = nodeRecord.moveNodegroups(self.srcNodegroupsCheckbox.getSelection(), self.destNodegroupCheckbox.getSelection()[0])            

            # None of the nodes could be moved at all. This maybe because the nodes are already in the node group or the nodes networks do not map
            # to the new destination node group.
            if not moveList:
                msg = self.kusuApp._("Could not move the selected nodes to the '%s' node group. They may be already in the same node group or do not have a valid network to associate them to the new node group.") % self.destNodegroupCheckbox.getSelection()[0]
                self.kusuApp.logErrorEvent(msg, toStderr=False)
                self.selector.popupMsg(self.kusuApp._("Error"), msg)                
            else:
                nodeRecord.setNodegroupByName(self.destNodegroupCheckbox.getSelection()[0])                
                nodeRecord.getNodeFormat()

                # Are we in IP/hostname preserve mode?
                preserveNodeIP = database.getAppglobals('PRESERVE_NODE_IP')
                # Check if the selected node format has a rack. If not(and we 
                # are not in PRESERVE_NODE_IP mode), then prompt for it.
                if rackPromptRequired(preserveNodeIP, nodeRecord, rack!=None, 
                                      self.destNodegroupCheckbox.getSelection()[0], 
                                      self.srcNodegroupsCheckbox.getSelection(), []):
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
                msg = self.kusuApp._("Only can move %d nodes to node group '%s', the following nodes cannot be moved:\n") % (len(moveList), self.nodegroupCheckbox.getSelection()[0])
                for node in badList:
                    msg += '%s (%s)\n' % (node[0], node[1])
                self.kusuApp.logErrorEvent(msg, toStderr=False)
                self.selector.popupMsg(self.kusuApp._("Notice"), msg)
                
            if len(moveList) > 0:
                if self.destNodegroupCheckbox.getSelection()[0] == 'unmanaged':
                    # Create temp unmanaged hosts file
                    tmpfile = writeUnmanagedHostsFile(database, moveList)
                else:
                    # Create temp mac file
                    tmpfile = writeMacFile(database, moveList, macList, self.destNodegroupCheckbox.getSelection()[0], nodeRecord)

                # Call kusu-addhost to delete these nodes
                progDialog = ProgressDialogWindow(self.screen, self.kusuApp._("nghosts_moving_nodes"), self.kusuApp._("nghosts_moving_nodes_progress"))
                self.kusuApp.unlock()
                ret = os.system("/opt/kusu/sbin/kusu-addhost --remove %s > /dev/null 2>&1" % string.join(moveList, ' '))
                if ret:
                    # os.system()'s return code is encoded. The actual return code is the high byte.
                    # http://docs.python.org/library/os.html#os.system
                    msg = self.kusuApp._("ERROR : kusu-addhost failed to remove nodes. Return code: %s" % (ret >> 8))
                    self.kusuApp.logErrorEvent(msg, False)
                    self.selector.popupMsg("addhost error", msg)
                    return NAV_NOTHING

                if self.destNodegroupCheckbox.getSelection()[0] == 'unmanaged':
                    # Add the unmanaged nodes
                    os.system("/opt/kusu/sbin/kusu-addhost --file=%s --nodegroup='unmanaged' > /dev/null 2>&1" % (tmpfile))
                else:
                    # Add these back using mac file
                    if needRack:
                       os.system("/opt/kusu/sbin/kusu-addhost --file=%s --node-interface=%s --nodegroup='%s' --rack=%s > /dev/null 2>&1" % (tmpfile, interface, self.destNodegroupCheckbox.getSelection()[0], rack))                    
                    else:
                       os.system("/opt/kusu/sbin/kusu-addhost --file=%s --node-interface=%s --nodegroup='%s' > /dev/null 2>&1" % (tmpfile, interface, self.destNodegroupCheckbox.getSelection()[0]))                    

                    self.kusuApp.lock()
                    progDialog.close()
 
                # If the user wants to reinstall the nodes check if the option is selected or not.
                #if self.reinstcheckbox.value() and self.destNodegroupCheckbox.getSelection()[0] != "unmanaged":
                #    progDialog = ProgressDialogWindow(self.screen, self.kusuApp._("nghosts_reinstalling_nodes"), \
                #                 self.kusuApp._("nghosts_reinstall_nodes_progress"))

                # Call PDSH here
                    if provision_type == PROVISION_TYPE_KUSU:
                        if not self.origin_is_multiboot and not insttype == 'multiboot':
                            rn = syncfun()
                            rn.runPdsh(moveIPList, "reboot < /dev/null > /dev/null 2>&1 &")

                # Remove temp file
                os.remove(tmpfile)
                progDialog.close()
                    
                self.kusuApp.logEvent(self.kusuApp._("nghosts_event_finish_move_nodes") % self.destNodegroupCheckbox.getSelection()[0], 
                    toStdout=False)
                                    
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
        destNodegroupList = []
        haveNodes = False
        self.screenGrid  = snack.Grid(1, 7)
        self.srcNodegroupsCheckbox = snack.CheckboxTree(height=8, width=35, scroll=1)
        self.destNodegroupCheckbox = snack.CheckboxTree(height=8, width=40, scroll=1)
        instruction = snack.Textbox(75, 1, self.kusuApp._(self.msg), scroll=0, wrap=1)
        labeltokens = self.kusuApp._("nghosts_nodegroup_label").split(',')
        label = snack.Label(self.kusuApp._("%s %s" % (labeltokens[0].ljust(28),labeltokens[1])))
        #self.reinstcheckbox = snack.Checkbox(self.kusuApp._("Reinstall Nodes"), isOn = 0)
        query = 'SELECT ngname, ngid FROM nodegroups ORDER BY ngid'

        try:
            self.database.connect()
            self.database.execute(query)
            nodegroups = self.database.fetchall()
        except:
            self.screen.finish()
            print self.kusuApp._("DB_Query_Error\n")
            self.unlock()
            sys.exit(-1)

        for group in nodegroups:
           self.destNodegroupCheckbox.append(group[0])

           query = "SELECT COUNT(*) from nodes,nodegroups WHERE nodes.ngid=nodegroups.ngid AND nodegroups.ngname='%s'" % group[0]
           try:
               self.database.connect()
               self.database.execute(query)
               nodes = self.database.fetchall()[0]
               test = nodes[0]
           except:
               self.screen.finish()
               print self.kusuApp._("DB_Query_Error\n")
               self.unlock()
               sys.exit(-1)
 
           # Only display node groups that are not empty when moving.
           # Installer is special case, we can't move the installer group if there's only the master installer left.
           if group[1] == 1:  
               if not int(nodes[0]) == 1:
                   self.srcNodegroupsCheckbox.append(group[0])
           else:     
                provision_type = getProvisionType(self.database)
                if int(nodes[0]) > 0:
                    if not (group[0] == "unmanaged" and provision_type == PROVISION_TYPE_KUSU):
                        haveNodes = True
                        self.srcNodegroupsCheckbox.append(group[0])

        self.screenGrid.setField(instruction, 0, 0, padding=(0,0,0,1))
        self.screenGrid.setField(label, 0, 1, padding=(7,0,0,0), anchorLeft=1)
        self.screenGrid.setField(self.srcNodegroupsCheckbox, 0, 2, padding=(0,0,0,0), anchorLeft=1)
        self.screenGrid.setField(self.destNodegroupCheckbox, 0, 3, padding=(0,-8,-1,0), anchorRight=1)
        #self.screenGrid.setField(self.reinstcheckbox, 0, 4, padding=(0,1,0,0), anchorLeft=1)

        # If there's no other nodes besides installer, then exit gracefully.
        if haveNodes == False:
           self.selector.popupMsg(self.kusuApp._("Notice"), self.kusuApp._("There are no nodes available. Exiting."))
           self.kusuApp.unlock()
           self.screen.finish()
           os._exit(-1)

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
        self.setHelpLine("Copyright(C) 2010 Platform Computing Inc.\t%s" % self.kusuApp._("nghosts_helpline_intro"))

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
       
        ks = USXNavigator(screenFactory=ScreenFactory, screenTitle="Node Membership Editor - ${VERSION_STR}", showTrail=False) 
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
        selectionOption.append([self.kusuApp._("nghosts_move_selected_nodes"), 0, 0])
        selectionOption.append([self.kusuApp._("nghosts_move_nodegroup"), 1, 0])
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

