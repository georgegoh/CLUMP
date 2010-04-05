#!/usr/bin/python
#
# $Id: kusu-boothost.py 3481 2010-02-03 08:01:55Z mkchew $
#
#   Copyright 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

import os
import pwd
import string
import sys

sys.path.append("/opt/primitive/lib/python2.4/site-packages")
from primitive.fetchtool.commands import FetchCommand
from primitive.core.errors import CommandException
from primitive.system.software.dispatcher import Dispatcher

sys.path.append("/opt/kusu/bin")
sys.path.append("/opt/kusu/lib")
import platform
if platform.machine() == "x86_64":
    sys.path.append("/opt/kusu/lib64/python")
sys.path.append("/opt/kusu/lib/python")

from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
from kusu.syncfun import syncfun
import kusu.ipfun
import IPy

from path import path
from primitive.pixietool.commands import GeneratePXEConfCommand

class boothost:
    """This is the class containing the metdods for manipulating PXE files"""
    updatednodes = []    # This list will contain a list of the nodes acted on
                         # It is used to reduce the DB queries for the "-r"

    badnodes = []     # Keep track of invalid nodes

    def __init__(self, gettext, kusuApp, bootdir):
        self.db = KusuDB()            
        self._ = gettext
        webserver_user = Dispatcher.get('webserver_usergroup')[0]
        self.passdata = pwd.getpwnam(webserver_user)     # Cache this for later
        self.kusuApp = kusuApp
        self.tftpdir = bootdir

        try:
            self.db.connect('kusudb', 'apache')
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)        
       
        self.primaryInstaller = self.db.getAppglobals('PrimaryInstaller')
                
        # Get the installers here so it can be cached for other hosts
        self.installerIPs = []
        query = ('SELECT nics.ip, networks.subnet, networks.device, networks.startip '
                 'FROM nics, nodes, networks '
                 'WHERE nodes.nid=nics.nid AND nics.netid=networks.netid '
                 'AND networks.usingdhcp=False AND LOWER(networks.device)!="bmc"'
                 'AND nodes.name="%s"') % self.primaryInstaller

        try:
            self.db.execute(query)
            data = self.db.fetchall()
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)
        if not data:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)
        for ipdata in data:
            self.installerIPs.append(ipdata)

    def errorMessage(self, message, *args):
        """errorMessage - Output messages to STDERR with Internationalization.
        Additional arguments will be used to substitute variables in the
        message output"""
        if len(args) > 0:
            mesg = self._(message) % args
        else:
            mesg = self._(message)
        
        sys.stderr.write(mesg)
        
    def logErrorEvent(self, msg, toStderr=True):        
        self.kusuApp.logErrorEvent(msg, toStderr)

        
    def toolHelp(self):
        """toolHelp - provide a help screen for this tool."""
        self.errorMessage("boothost_Help")
        sys.stderr.write('\n')
        sys.exit(0)


    def mkMultibootPXEFile(self, mac, kparams, hostname=''):
        """mkMultibootPXEFile - Create a PXE boot file for booting an existing
        partition.  The partition is a kernel parameter like:  hd0 1 - for
        first disk first partition."""
  
        newmac = '01-%s' % mac.replace(':', '-')
        filename = os.path.join('/tftpboot','kusu','pxelinux.cfg',newmac)
        fp = file(filename, 'w')
        if hostname != '':
            fp.write("# PXE file for: %s\n" % hostname)
        
        fp.write("DEFAULT menu.c32\n")
        fp.write("PROMPT 0\n")
        fp.write("NOESCAPE 1\n")
        fp.write("TIMEOUT 10\n")
        fp.write("ONTIMEOUT chain.c32 %s\n" % kparams)
        fp.write("MENU TITLE Boot Menu\n")
        fp.write("LABEL Partition\n")
        fp.write("        MENU LABEL Boot ^Partition\n")
        fp.write("        MENU DEFAULT\n")
        fp.write("        KERNEL chain.c32\n")
        fp.write("        APPEND %s\n" % kparams)
        fp.close()

        # The PXE file needs to be owned by apache, so the nodeboot.cgi can update it.
        os.chmod(filename, 0644)
        os.chown(filename, self.passdata[2], self.passdata[3])


    def mkPXEFile(self, mac, kernel, initrd, kparams, localboot, hostname=''):
        """mkPXEFile - Create a PXE boot file given the kernel, initrd and
        kparams.  If the localboot flag is true then the PXE file that is
        generated will attempt to boot from the local disk first."""

        newmac = '01-%s' % mac.replace(':', '-')

        # Determine which niihost to give to the node.
        # If it is diskless or imaged, then just give it a list.  It will
        # determine the best one to use.  If it is package based then
        # Correlate the installers IP's with the nodes IP's.  Where they
        # intersect use that IP as the niihost.
        # Have:  self.installerIPs which is a list of primary installer IP's,
        # and the corresponding network information.
        query = ("SELECT nodegroups.repoid, networks.device, nodegroups.installtype, nics.ip, nodes.ngid " + 
                 "FROM nics, nodes, networks, nodegroups " + 
                 "WHERE nodes.nid=nics.nid " + 
                 "AND nics.netid=networks.netid " +
                 "AND nodegroups.ngid=nodes.ngid " +
                 "AND nics.mac ='%s'" % mac)
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)

        # Unmanaged hosts do not need a PXE file!
        if data[4] == self.db.getNgidOf('unmanaged'):
            sys.exit(0)
            
        repoid      = data[0]
        ksdevice    = data[1]
        installtype = data[2]
        nodesip     = data[3]
        
        query = ("SELECT ostype FROM repos WHERE repos.repoid = '%s'" % repoid)
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)
            
        ostype      = data[0].split('-')[0]

        syslog_ip = self.db.getAppglobals('SYSLOG_SERVER')

        niihost = instip = ''
        if installtype == 'package':
            # Find the installer IP address whose network matches best with node ip
            # Cannot directly check for NIC ip against the network device due to
            # supplementary networks (<physical network>-eth0 network)
            best_ip = ''
            # Support overlapping networks with different startips by comparing and storing the last best one
            best_start_ip = 0

            for netdata in self.installerIPs:
                # Pop a installer IP and it's network info (subnet, device, startip) 
                instip, instsub, instdev, inst_start_ip = netdata
                # Check if node ip falls within this network
                if kusu.ipfun.onNetwork(instip, instsub, nodesip, inst_start_ip):
                    # Check against overlapping networks by comparing their startip(s)
                    integer_start_ip = IPy.IP(inst_start_ip).int()
                    if integer_start_ip > best_start_ip:
                        # Found a smaller network within the last best match
                        # Or this is the first matching network
                        best_ip = instip
                        best_start_ip = integer_start_ip

                if not syslog_ip or best_ip:
                    syslog_ip = best_ip
                if instdev == ksdevice and kusu.ipfun.onNetwork(instip, instsub, nodesip):
                    break
        else:
            # Diskless and imaged do not care.  They can find the best one.
            for line in self.installerIPs:
                niihost = niihost + "%s," % line[0]
            niihost = niihost[:-1]

        kname = kpath = kernel
        iname = ipath = initrd
        # If kernel/initrd provided is not full path, assume 
        # that they are found under self.tftpdir.
        if kernel is not None and path(kernel).dirname() == '':
            kpath = path(self.tftpdir) / kernel
        if initrd is not None and path(initrd).dirname() == '':
            ipath = path(self.tftpdir) / initrd

        kusu_root = os.getenv('KUSU_ROOT', '/opt/kusu')
        template = path(kusu_root) / 'etc/templates/pxefile.tmpl'

        # Note: Strictly speaking kpath and ipath is not necessary
        # since noUpdate=True. Will leave it in for completeness.
        c = GeneratePXEConfCommand(name='GeneratePXEConf',
                                   template=template,
                                   identifierList=[newmac],
                                   preamble='# PXE file for: %s' % hostname,
                                   tftpdir=self.tftpdir,
                                   localboot=localboot,
                                   kname=kname,
                                   mac=mac,
                                   kpath=kpath,
                                   iname=iname,
                                   ipath=ipath,
                                   params=kparams or '',
                                   instIP=instip,
                                   syslogIP=syslog_ip,
                                   noUpdate=True,
                                   ksdevice=ksdevice,
                                   ostype=ostype,
                                   niihost=niihost,
                                   repoid=repoid,
                                   installtype=installtype,
                                   logged=False)

        results = c.execute()
        # The list of files generated by GeneratePXEConfCommand is
        # returned in results[3]
        fnames = results[3]
            
        # The PXE file needs to be owned by apache, so the nodeboot.cgi can update it.
        for fname in fnames:
            pxefile = path(fname)
            pxefile.chmod(0644)
            pxefile.chown(self.passdata[2], self.passdata[3])
    


    def getNodeBootInfo(self, nodename):
        """getNodeBootInfo - Gets the node boot information for a given node and
        displays it in a pretty form."""
        if nodename == self.primaryInstaller:
            print "Not displaying info for PrimaryInstaller: %s" % nodename
            return

        query = ('select '
                 'nodes.name, nodes.kernel, nodes.initrd, nodes.kparams, nodes.state,'
                 'nodes.bootfrom, nodegroups.ngname, nodegroups.kernel, nodegroups.initrd,'
                 'nodegroups.kparams, nodes.nid, nics.mac, nics.ip, nodes.uid '
                 'from nodes,nodegroups,nics  where name="%s" '
                 'and nodes.ngid=nodegroups.ngid '
                 'and nics.nid=nodes.nid '
                 'and nics.boot=True' % nodename)
    
        try:
            self.db.execute(query)
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)
        
        data = self.db.fetchone()

        if data:  # The Installer node will not have nics.boot set, so need to test
            name     = data[0]
            kernel   = data[1]
            initrd   = data[2]
            kparams  = data[3]
            state    = data[4]
            bootfrom = data[5]
            ngname   = data[6]
            nid      = data[10]
            mac      = data[11]
            ip       = data[12]
            uid      = data[13]

            if kernel  == None :
                kernel  = data[7]

            if initrd  == None :
                initrd  = data[8]
            
            if kparams == None :
                kparams = data[9]
            if bootfrom:
                bootfrom = 'Disk'
            else:
                bootfrom = 'Network'
        
            print "Node:   %s\t\tNode Group: %s" % (name, ngname)
            print "State:  %s\t\tBoot:  %s" % (state, bootfrom)
            print "UID: %s" % uid
            print "Kernel: %s" % kernel
            print "Initrd: %s" % initrd
            print "Kernel Params:  %s" % kparams
            print "MAC:  %s\t\tIP:  %s" % (mac, ip)
            print "-"*60
        else:
            self.logErrorEvent(self._('boothost_no_such_host') % nodename)
            self.badnodes.append(nodename)

    def getAllBootInfo(self):
        """getAllBootInfo  - Generate a list of all the boot info for
        all nodes in the database."""
        query = ('select name from nodes where ngid != %d '
                 'AND NOT name="%s"') % (self.db.getNgidOf('unmanaged'), self.primaryInstaller)
        try:
            self.db.execute(query)
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)
        
        else:
            data = self.db.fetchall()
            for row in data:
                self.getNodeBootInfo(row)


    def __mkUpdateSql2(self, kernel='', initrd='', kparams=''):
        """__mkUpdateSql2 - This method generates the SQL fragment to update the
        kernel, initrd, and/or kparams.  It also handles unsetting
        the values when the value is set to NULL.
        This can be used with the nodegroup table, but NOT the nodes table"""
        setstr = ''
        if kernel != '':
            if kernel == 'NULL':
                setstr = setstr + 'kernel=NULL, '
            else:
                setstr = setstr + 'kernel=\'%s\', ' % kernel
        if initrd != '':
            if initrd == 'NULL':
                setstr = setstr + 'initrd=NULL, '
            else:
                setstr = setstr + 'initrd=\'%s\', ' % initrd
        if kparams != '':
            if kparams == 'NULL':
                setstr = setstr + 'kparams=NULL, '
            else:
                setstr = setstr + 'kparams=\'%s\', ' % kparams

        if setstr != '':
            return setstr[:-2]
        return ''


    def __mkUpdateSql(self, kernel='', initrd='', kparams='', state='', localboot=''):
        """__mkUpdateSql - This method generates the SQL fragment to update the
        kernel, initrd, and/or kparams.  It also handles unsetting
        the values when the value is set to NULL"""
        setstr = self.__mkUpdateSql2(kernel, initrd, kparams)
        if setstr != '':
            setstr = setstr + ', '

        # A reinstall has to occur if the kernel, initrd, or kparams changes.
        if kernel != '' or initrd != '' or kparams != '':
            state = 'Expired'
            localboot = 0
        if state != '':
            if state == 'NULL':
                setstr = setstr + 'state=NULL, '
            else:
                setstr = setstr + 'state=\'%s\', ' % state
        if localboot != '':
            if localboot == '1':
                setstr = setstr + 'bootfrom=True, '
            else:
                setstr = setstr + 'bootfrom=False, '

        if setstr != '':
            return setstr[:-2]
        return ''


    def __genNodesPXE(self, nodename, kernel='', initrd='', kparams='', state='', localboot=''):
        """__genNodesPXE - This function will generate the PXE file associated
        with nodename.  If the kernel, initrd, or kparams are specified then it
        then it will update the database first, then generate the PXE file.
        USE:  __genNodesPXE(nodename, kernel, initrd, kparams)
           nodename = The name of the node to make a PXE file for
           kernel   = (Optional) Name of kernel to use in PXE file.  Causes
                      the node table to be updated with this value.
           initrd   = (Optional) Path to the initrd to boot with.  Causes
                      the node table to be updated with this value.
           kparams  = (Optional) Kernel paramaters to use with the kernel
                      in the PXE file.  Causes the node table to be updated
                      with this value.
           state    = (optional) State to set the nodes to in the database.
                      Causes the node table to be updated with this value.
           localboot = (optional) If set to "1" the PXE file will attempt
                      to boot from the local disk.  If set to "0" it will
                      boot from the network.  Causes the node table to be
                      updated with this value.
                      """
        # Build up the sql update from the args provided
        setstr = self.__mkUpdateSql(kernel, initrd, kparams, state, localboot)

        if setstr != '':
            # Need to update the database
            query = ('update nodes set %s where name="%s"' % (setstr, nodename))
            try:
                self.db.execute(query)
            except:
                print "ERROR:  Unable to update database"
        
        # Query the database to gather the data needed
        query = ('select '
                 'nodes.name, nodes.kernel, nodes.initrd, nodes.kparams, nodes.bootfrom, '
                 'nodegroups.kernel, nodegroups.initrd, nodegroups.kparams, '
                 'nics.mac, nodes.state, nodegroups.installtype '
                 'from nodes,nodegroups,nics where nodes.name="%s" '
                 'and nodes.ngid=nodegroups.ngid '
                 'and nics.nid=nodes.nid '
                 'and nics.boot=True' % nodename)        
        try:
            self.db.execute(query)
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)

        else:
            data = self.db.fetchone()

        if data:
            name     = data[0]
            kernel   = data[1]
            initrd   = data[2]
            kparams  = data[3]
            bootfromb = data[4]
            if kernel  == None :
                kernel  = data[5]
            if initrd  == None :
                initrd  = data[6]
            if kparams == None :
                kparams = data[7]
            mac      = data[8]
            state    = data[9]
            insttype = data[10]
            if bootfromb:
                bootfrom = 1
            else:
                bootfrom = 0

            if not mac:
                self.logErrorEvent(self._('boothost_no_mac_host') % nodename)
                return False

            if insttype != 'multiboot':
                self.mkPXEFile(mac, kernel, initrd, kparams, bootfrom, name)
            else:
                self.mkMultibootPXEFile(mac, kparams, name)
                # Force the state to Installed since there is nothing else for it
                query = "update nodes set state='Installed' where name='%s'" % (nodename)
                try:
                    self.db.execute(query)
                except:
                    self.logErrorEvent(self._('DB_Update_Error'))
                    print "ERROR:  Unable to update database"
                    return False
        else:
            self.logErrorEvent(self._('boothost_no_such_host') % nodename)
            return False
        
        return True

    def genNodeGrpPXE(self, nodegroup, kernel='', initrd='', kparams='', state='', localboot='', synced=0):
        """genNodeGrpPXE - This function will generate the PXE file associated
        with all the nodes in the noderoup.  If the kernel, initrd, or kparams
        are specified then it will update the database first, then generate
        the PXE file.
        USE: genNodeGrpPXE(nodegroup, kernel, initrd, kparams)
            nodegroup = The name of the node group to update the PXE files for.
                        All nodes in this node group will get have the PXE file
                        regenerated
            kernel   = (optional) Name of kernel to use in PXE file.  Causes
                       the node table to be updated with this value.
            initrd   = (optional) Path to the initrd to boot with.  Causes the
                       node table to be updated with this value.
            kparams  = (optional) Kernel paramaters to use
                       with the kernel in the PXE file.  Causes the node table
                       to be updated with this value.
            state    = (optional) State to set the nodes to in the database.
                       Causes the node table to be updated with this value.
            localboot = (optional) If set to "1" the PXE file will attempt to
                       boot from the local disk.  If set to "0" it will boot
                       from the network.  Causes the node table to be updated
                       with this value.
            synced   = [0|1] (optional) If this flag is 1 then the PXE file
                       will only be generated for those nodes where
                       state="Expired" """
                       
        self.updatednodes = []
        self.kusuApp.logEvent(self._("boothost_event_update_nodegroup") % nodegroup, toStdout=False)

        # Test for a valid node group
        query = ('select ngid, type from nodegroups where ngname="%s"' % nodegroup)
        try:
            self.db.execute(query)
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)
            
        ngid, ngtype = self.db.fetchone() or (None, None)
        if not ngid:
            self.logErrorEvent(self._('boothost_no_such_nodegroup') % nodegroup)
            sys.exit(-1)

        if ngtype == 'installer':
            self.logErrorEvent('Not generating PXE files for installer nodegroup: %s' % nodegroup)
            sys.exit(-1)

        # Update the Kernel, initrd, and/or kernel paramaters if needed
        setstr = self.__mkUpdateSql2(kernel, initrd, kparams)
        if setstr != '':
            # Need to update the database
            query = ('update nodegroups set %s where ngname="%s"' % (setstr, nodegroup))
            try:
                self.db.execute(query)
            except:
                self.logErrorEvent(self._('boothost_unable_to_update_nodegroup') % nodegroup)
                sys.exit(-1)

        # Get a list of all of the nodes to update
        if synced == 1:
            query = ('select nodes.name from nodes,nodegroups where '
                     'nodes.ngid=nodegroups.ngid and nodegroups.ngname="%s" '
                     'and nodes.state="Expired"' % nodegroup)
        else:
            query = ('select nodes.name from nodes,nodegroups where '
                     'nodes.ngid=nodegroups.ngid and nodegroups.ngname="%s"' % nodegroup)

        try:
            self.db.execute(query)
        except:
            self.logErrorEvent(self._('DB_Query_Error'))
            sys.exit(-1)
            
        hostlist = self.db.fetchall()
        if hostlist == None :
            self.logErrorEvent(self._("boothost_unable_to_get_nodegroup") % nodegroup)
            sys.exit(-1)

        self.updatednodes = hostlist

        # If a kernel, initrd, or kparams is specified all nodes are expired
        # and need to install.  If they are not specified, only those nodes
        # that have their own kernel, initrd, or kparams should be reinstalled
        if kernel != '' or initrd != '' or kparams != '':
            # Clean out and custom kernel, initrd, and kernel params
            setstr = self.__mkUpdateSql('NULL', 'NULL', 'NULL', 'Expired', 0)
            if setstr != '':
                # Need to update the database
                query = ('update nodes set %s where '
                         'ngid=(select ngid from nodegroups '
                         'where ngname="%s")' % (setstr, nodegroup))
                try:
                    self.db.execute(query)
                except:
                    self.logErrorEvent(self._('boothost_unable_to_update_nodegroup') % nodegroup)
                    sys.exit(-1)
        else:
            if state != '' or localboot != '':
               # Set the state of these nodes to what the user requested
               setstr = self.__mkUpdateSql('', '', '', state, localboot)
               if setstr != '':
                   # Need to update the database
                   query = ('update nodes set %s where '
                            'ngid=(select ngid from nodegroups '
                            'where ngname="%s")' % (setstr, nodegroup))
                   try:
                       self.db.execute(query)
                   except:
                       self.logErrorEvent(self._('boothost_unable_to_update_nodegroup') % nodegroup)
                       sys.exit(-1)

            # Reset those nodes that have a custom kernel, initrd, and kernel params
            query = ('update nodes set '
                     'bootfrom=False, kernel=NULL, initrd=NULL, kparams=NULL, state="Expired" '
                     'where (kernel is not null or initrd is not null or kparams is not null) '
                     'and ngid=(select ngid from nodegroups where ngname="%s")' % (nodegroup))

            try:
                self.db.execute(query)
            except:
                self.logErrorEvent(self._('boothost_unable_to_update_nodegroup') % nodegroup)
                sys.exit(-1)

        # Iterate over the list of hosts
        if hostlist:
            for row in hostlist:
                self.kusuApp.logEvent(self._("boothost_event_updated_node") % row[0], toStdout=False)
                self.__genNodesPXE(row[0])

        self.kusuApp.logEvent(self._("boothost_event_finish_update_nodegroup") % nodegroup, toStdout=False)


    def genNodeListPXE(self, nodelist, kernel='', initrd='', kparams='', state='', localboot=''):
        """genNodeListPXE - This function will generate the PXE file associated
        with all the nodes in the nodelist.  If the kernel, initrd, or kparams
        are specified then it will update the database first, then generate the
        PXE file.
        USE: genNodeListPXE(nodelist, kernel, initrd, kparams)
             nodelist = A list of nodes to generate the PXE file for
             kernel   = (Optional) Name of kernel to use in PXE file.  Causes
                        the node table to be updated with this value.
             initrd   = (Optional) Path to the initrd to boot with.  Causes
                        the node table to be updated with this value.
             kparams  = (Optional) Kernel paramaters to use with the kernel in
                        the PXE file.  Causes the node table to be updated with
                        this value.
             state    = (optional) State to set the nodes to in the database.
                        Causes the node table to be updated with this value.
             localboot = (optional) If set to "1" the PXE file will attempt
                        to boot from the local disk.  If set to "0" it will
                        boot from the network.  Causes the node table to be
                        updated with this value.
                        """
                        
        self.kusuApp.logEvent(self._("boothost_event_update_nodes"), toStdout=False)
        
        # If the primaryInstaller name is found in the supplied
        # list of nodes, silently drop it.
        if self.primaryInstaller in nodelist:
            nodelist.remove(self.primaryInstaller)

        # Iterate over the list of hosts, and update their PXE files
        self.updatednodes = []
        for node in nodelist:
            if self.__genNodesPXE(node, kernel, initrd, kparams, state, localboot):
                try:
                    self.kusuApp.logEvent(self._("boothost_event_updated_node") % node, toStdout=False)
                except:
                    self.kusuApp.logEvent("ERROR invalid node name", toStdout=False)
                    self.kusuApp.logEvent("Nodelist = " % nodelist)
                    pass
                self.updatednodes.append(node)
            else:
                self.badnodes.append(node)
        
        self.kusuApp.logEvent(self._("boothost_event_finish_update_nodes"), toStdout=False)
        
    def checkKusuProvision(self):
        provision = self.db.getAppglobals('PROVISION')
        if provision and provision != 'KUSU':
            sys.stderr.write('Kusu provisioning has been disabled. kusu-boothost will not run.\n')
            sys.exit(-1)        
 
class BootHostApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)   # Get the Lang stuff from the kusuapp class

        if os.getuid() != 0:
            # apache(RHEL)/wwwrun(SLES) is allowed for nodeboot.cgi
            webserver_user = Dispatcher.get('webserver_usergroup')[0]
            webuser = pwd.getpwnam(webserver_user)
            if os.getuid() != webuser[2]:
                self.errorMessage("nonroot_execution\n")
                sys.exit(-1)

        self.updatewhat = ''
        self._retrieveDBData()

    def _retrieveDBData(self):
        self.db = KusuDB()            
        try:
            self.db.connect('kusudb', 'apache')
        except:
            self.logErrorEvent('DB_Query_Error')
            sys.exit(-1)        
        
        self.installerIPs = []

        # Set self.BootDir to PIXIE_ROOT (db.appglobals)
        query = ('SELECT kvalue FROM appglobals where kname="PIXIE_ROOT"')
        try:
            self.db.execute(query)
            self.BootDir = self.db.fetchone()[0]
        except:
            self.logErrorEvent('DB_Query_Error')
            sys.exit(-1)
        if not self.BootDir:
            self.logErrorEvent('DB_Query_Error')
            sys.exit(-1)

    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        self.errorMessage("kusu-boothost version %s\n", self.version)
        sys.exit(0)


    def parseargs(self, toolinst):
        """parseargs - Parse the command line arguments and populate the
        class variables"""
        self.reinstall  = 0
        self.nodegroup  = ''    # Node group to update
        self.nodelist   = ''    # List of nodes to update
        self.newkernel  = ''    # New kernel to use
        self.newinitrd  = ''    # New initrd to use
        self.newkparms  = ''    # New kernel parameters to use
        self.updatewhat = ''    # What to update NodeGroup|NodeList|UnSyncedNodes
        self.state      = ''    # New state to use (Unexposed to users)
        self.localboot  = ''    # New localboot to use (Unexposed to users)

        
        args = self.args[1:]
        i = 0
        while i < len(args):
            if args[i] == '-h':
                toolinst.toolHelp()
            elif args[i] == '-v':
                self.toolVersion()
            elif args[i] == '-r':
                self.reinstall  = 1
            elif args[i] == '-l':
                if len(args) > (i+1):
                    toolinst.getNodeBootInfo(args[i+1])
                else:
                    toolinst.getAllBootInfo()
                if toolinst.badnodes:
                    sys.exit(-1)
                else:
                    sys.exit(0)
            else:
                # Now deal with all the other arguments that are not mutually exclusive
                if args[i] == '-n':
                    if len(args) > (i+1):
                        self.nodegroup = args[i+1]
                        self.updatewhat = 'NodeGroup'
                    else:
                        toolinst.toolHelp()
                elif args[i] == '-m':
                    if len(args) > (i+1):
                        self.nodelist = string.split(args[i+1], ',')
                        self.updatewhat = 'NodeList'
                    else:
                        toolinst.toolHelp()
                elif args[i] == '-s':
                    if len(args) > (i+1):
                        self.nodegroup = args[i+1]
                        self.updatewhat = 'NodeUnSynced'
                    else:
                        toolinst.toolHelp()
                elif args[i] == '-k':
                    if len(args) > (i+1):
                        self.newkernel = args[i+1]
                    else:
                        toolinst.toolHelp()
                elif args[i] == '-i':
                    if len(args) > (i+1):
                        self.newinitrd = args[i+1]
                    else:
                        toolinst.toolHelp()      
                elif args[i] == '-p':
                    if len(args) > (i+1):
                        self.newkparms = args[i+1]
                    else:
                        toolinst.toolHelp()
                else:
                    self.errorMessage('Unknown arguments %i\n', args[i:])
                    toolinst.toolHelp()
                i = i + 1
            # end else
            i = i + 1
        # end while


    def validateKernel(self, newkernel):
        newkernelpath = os.path.join(self.BootDir, newkernel)
        if not os.path.isfile(newkernelpath) and not os.path.isfile(newkernel):
            self.logErrorEvent(self._('boothost_no_such_kernel') % newkernel)
            sys.exit(-1)
    
    def placeTFTPBootFile(self, file):
        p = os.path.realpath(file)
        if not p.startswith(os.path.realpath(self.BootDir)):
            d,f = os.path.split(p)
            if d:
                try:
                    # ignore leading '/'s
                    end_slash = 0
                    for i,v in enumerate(d):
                        if v != '/':
                            end_slash = i
                            break
                    d = d[end_slash:]
                    destdir = os.path.join(self.BootDir, d)
                    if not os.path.exists(destdir):
                        os.makedirs(destdir)
                    fc = FetchCommand(uri='file://' + p,
                                      fetchdir=False,
                                      destdir=os.path.join(self.BootDir, d),
                                      overwrite=True)
                    fc.execute()
                except CommandException, e:
                    self.logErrorEvent("Couldn't place kernel in tftpboot directory. %s" % str(e))


    def validateInitrd(self, newinitrd):
        newinitrdpath = os.path.join(self.BootDir, newinitrd)
        if not os.path.isfile(newinitrdpath) and not os.path.isfile(newinitrd):
            self.logErrorEvent(self._('boothost_no_such_initrd') % newinitrd)
            sys.exit(-1)


    def getActionDesc(self):
        if self.updatewhat == 'NodeList':
            return "Update PXE config (nodes)"
        elif self.updatewhat == 'NodeGroup':
            return "Update PXE config (nodegroup)"
        else:
            return KusuApp.getActionDesc(self)
       
    def run(self):
        """run - Run the application"""

        bhinst = boothost(self.gettext, self, self.BootDir)
        self.parseargs(bhinst)

        if self.reinstall == 1:
            self.state = 'Expired'
            self.localboot = 0

        if self.newkernel:
            self.validateKernel(self.newkernel)
            # place kernel if absolute path given.
            if os.path.split(self.newkernel)[0]:
                self.placeTFTPBootFile(self.newkernel)
        
        if self.newinitrd:
            self.validateInitrd(self.newinitrd)
            # place initrd if absolute path given.
            if os.path.split(self.newinitrd)[0]:
                self.placeTFTPBootFile(self.newinitrd)
           
        if self.updatewhat == 'NodeList':
            bhinst.checkKusuProvision()
            bhinst.genNodeListPXE(self.nodelist, self.newkernel,
                                  self.newinitrd, self.newkparms, 
                                  self.state, self.localboot)
        elif self.updatewhat == 'NodeGroup':
            bhinst.checkKusuProvision()
            bhinst.genNodeGrpPXE(self.nodegroup, self.newkernel,
                                 self.newinitrd, self.newkparms,
                                 self.state, self.localboot)
        elif self.updatewhat == 'NodeUnSynced':
            bhinst.checkKusuProvision()
            bhinst.genNodeGrpPXE(self.nodegroup, self.newkernel,
                                 self.newinitrd, self.newkparms,
                                 self.state, self.localboot, 1)
        else:
            bhinst.toolHelp()

        # Check and reinstall if needed
        if self.reinstall == 1:
            if os.getuid() != 0:
                sys.stderr.write(self._('boothost_root_reboot'))
                sys.stderr.write(_('boothost_root_reboot'))
                sys.exit(-2)

            self.logEvent(self._("boothost_event_reboot_nodes"), toStdout=False)

            print self._('boothost_reboot'),
            names = []
            for name in bhinst.updatednodes:
                self.logEvent(self._("boothost_event_rebooted_node") % name, toStdout=False)
                if isinstance(name, tuple):
                    names.append(name[0])
                else:
                    names.append(name)
            print ", ".join(names)
                
            #sys.exit(0)
            pdshcls = syncfun()
            pdshcls.runPdsh(bhinst.updatednodes, '/sbin/reboot')
            
            self.logEvent(self._("boothost_event_finish_reboot_nodes"), toStdout=False)

        # Exit with error if invalid hosts exist
        if bhinst.badnodes:
            sys.exit(-1)

app = BootHostApp()
app.run()

