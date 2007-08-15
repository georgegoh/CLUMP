#!/usr/bin/python
#
# $Id$
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

from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
from kusu.syncfun import syncfun


version="-VERSION-"

class boothost:
    """This is the class containing the metdods for manipulating PXE files"""
    updatednodes = []    # This list will contain a list of the nodes acted on
                         # It is used to reduce the DB queries for the "-r"
    def __init__(self, gettext):
        self.db = KusuDB()
        self.db.connect('kusudb', 'apache')
        self.gettext = gettext
        

    def errorMessage(self, message, *args):
        """errorMessage - Output messages to STDERR with Internationalization.
        Additional arguments will be used to substitute variables in the
        message output"""
        if len(args) > 0:
            mesg = self.gettext(message) % args
        else:
            mesg = self.gettext(message)
        sys.stderr.write(mesg)

        
    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        global version
        self.errorMessage("Version %s\n", version)
        sys.exit(0)


    def toolHelp(self):
        """toolHelp - provide a help screen for this tool."""
        self.errorMessage("boothost_Help")
        sys.stderr.write('\n')
        sys.exit(0)


    def mkPXEFile(self, mac, kernel, initrd, kparams, localboot, hostname=''):
        """mkPXEFile - Create a PXE boot file given the kernel, initrd and
        kparams.  If the localboot flag is true then the PXE file that is
        generated will attempt to boot from the local disk first."""
        
        # Get the IP of the primary installer
        #query = ('select nics.ip from nics,nodes where nodes.nid=nics.nid '
        #         'and nodes.name=(select kvalue from appglobals where '
        #         'kname="PrimaryInstaller")')
        #
        #try:
        #    self.db.execute(query)
        #    data = self.db.fetchall()
        #except:
        #    self.errorMessage('DB_Query_Error\n')
        #    sys.exit(-1)
        #         
        #niihost = ''
        #if data:
        #    for line in data:
        #        niihost = niihost + "%s," % line[0]
        #    niihost = niihost[:-1]

        newmac = '01-%s' % mac.replace(':', '-')
        filename = os.path.join('/tftpboot','kusu','pxelinux.cfg',newmac)
        fp = file(filename, 'w')
        if hostname != '':
            fp.write("# PXE file for: %s\n" % hostname)
            
        if localboot == True :
            fp.write("default localdisk\n")
        else:
            fp.write("default Reinstall\n")

        query = ("SELECT nics.ip FROM nics, nodes, networks WHERE nodes.nid=nics.nid " +
                 "AND networks.netid=nics.netid " +
                 "AND networks.netid=(SELECT netid FROM nics WHERE mac='%s') " % mac +
                 "AND nodes.name=(SELECT kvalue FROM appglobals WHERE kname='PrimaryInstaller')")
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)

        http_ip = data[0]

        query = ("SELECT nodegroups.repoid, networks.device, repos.ostype, nodegroups.installtype " + 
                 "FROM nics, nodes, networks, nodegroups, repos " + 
                 "WHERE nodes.nid=nics.nid " + 
                 "AND nics.netid=networks.netid " +
                 "AND nodegroups.ngid=nodes.ngid " +
                 "AND nodegroups.repoid=repos.repoid " +
                 "AND nics.mac ='%s'" % mac)
        try:
            self.db.execute(query)
            data = self.db.fetchone()
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)

        repoid = data[0]
        ksdevice = data[1]
        ostype = data[2].split('-')[0]
        installtype = data[3]

        fp.write("prompt 0\n")
        fp.write("label Reinstall\n")
        fp.write("        kernel %s\n" % kernel)

        if installtype == 'package' and ostype in ['fedora', 'centos', 'rhel']:
            kickstart_file = 'http://%s/repos/%s/ks.cfg.%s' % (http_ip, repoid, http_ip)
            fp.write("        append initrd=%s syslog=%s:514 niihost=%s ks=%s ksdevice=%s %s\n" % \
                     (initrd, http_ip, http_ip, kickstart_file, ksdevice, kparams or ''))
        else:
            fp.write("        append initrd=%s niihost=%s %s\n" % (initrd, http_ip, kparams or ''))

        if localboot == True :
            fp.write("\nlabel localdisk\n")
            fp.write("        localboot 0\n")
                
        fp.close()

        # The PXE file needs to be owned by apache, so the nodeboot.cgi can update it.
        os.chmod(filename, 0644)
        passdata = pwd.getpwnam('apache')     # Might be more efficient to cache this
        os.chown(filename, passdata[2], passdata[3])
    


    def getNodeBootInfo(self, nodename):
        """getNodeBootInfo - Gets the node boot information for a given node and
        displays it in a pretty form."""
        query = ('select '
                 'nodes.name, nodes.kernel, nodes.initrd, nodes.kparams,'
                 'nodes.state, nodes.bootfrom, nodegroups.ngname, nodegroups.kernel, '
                 'nodegroups.initrd, nodegroups.kparams, nodes.nid, nics.mac, nics.ip '
                 'from nodes,nodegroups,nics  where name="%s" '
                 'and nodes.ngid=nodegroups.ngid '
                 'and nics.nid=nodes.nid '
                 'and nics.boot=1' % nodename)
    
        try:
            self.db.execute(query)
        except:
            self.errorMessage('DB_Query_Error\n')
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
            if kernel  == None :
                kernel  = data[7]

            if initrd  == None :
                initrd  = data[8]
            
            if kparams == None :
                kparams = data[9]
            if bootfrom == 1:
                bootfrom = 'Disk'
            else:
                bootfrom = 'Network'
        
            print "Node:   %s\t\tNode Group: %s" % (name, ngname)
            print "State:  %s\t\tBoot:  %s" % (state, bootfrom)
            print "Kernel: %s" % kernel
            print "Initrd: %s" % initrd
            print "Kernel Params:  %s" % kparams
            print "MAC:  %s\t\tIP:  %s" % (mac, ip)
            print "-"*60
        # else:
            # self.errorMessage('boothost_no_such_host %s\n', nodename)

    def getAllBootInfo(self):
        """getAllBootInfo  - Generate a list of all the boot info for
        all nodes in the database."""
        query = ('select name from nodes')
        try:
            self.db.execute(query)
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)
        
        else:
            data = self.db.fetchall()
            for row in data:
                self.getNodeBootInfo(row)


    def __mkUpdateSql(self, kernel='', initrd='', kparams='', state='', localboot=''):
        """__mkUpdateSql - This method generates the SQL fragment to update the
        kernel, initrd, and/or kparams.  It also handles unsetting
        the values when the value is set to NULL"""
        setstr = ''
        if kernel != '':
            state = 'Expired'
            if kernel == 'NULL':
                setstr = setstr + 'kernel=NULL, '
            else:
                setstr = setstr + 'kernel=\'%s\', ' % kernel
        if initrd != '':
            state = 'Expired'
            if initrd == 'NULL':
                setstr = setstr + 'initrd=NULL, '
            else:
                setstr = setstr + 'initrd=\'%s\', ' % initrd
        if kparams != '':
            state = 'Expired'
            if kparams == 'NULL':
                setstr = setstr + 'kparams=NULL, '
            else:
                setstr = setstr + 'kparams=\'%s\', ' % kparams
        if state != '':
            if state == 'NULL':
                setstr = setstr + 'state=NULL, '
            else:
                setstr = setstr + 'state=\'%s\', ' % state
        if localboot != '':
            if localboot == '1':
                setstr = setstr + 'bootfrom=1, '
            else:
                setstr = setstr + 'bootfrom=0, '

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
                raise "ERROR:  Unable to update database"
        
        # Query the database to gather the data needed
        query = ('select '
                 'nodes.name, nodes.kernel, nodes.initrd, nodes.kparams, nodes.bootfrom, '
                 'nodegroups.kernel, nodegroups.initrd, nodegroups.kparams, '
                 'nics.mac '
                 'from nodes,nodegroups,nics where nodes.name="%s" '
                 'and nodes.ngid=nodegroups.ngid '
                 'and nics.nid=nodes.nid '
                 'and nics.boot=1' % nodename)        
        try:
            self.db.execute(query)
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)

        else:
            data = self.db.fetchone()

        if data:
            name     = data[0]
            kernel   = data[1]
            initrd   = data[2]
            kparams  = data[3]
            bootfrom = data[4]
            if kernel  == None :
                kernel  = data[5]
            if initrd  == None :
                initrd  = data[6]
            if kparams == None :
                kparams = data[7]
            mac = data[8]

            self.mkPXEFile(mac, kernel, initrd, kparams, bootfrom, name)


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

        # Test for a valid node group
        query = ('select ngid from nodegroups where ngname="%s"' % nodegroup)
        try:
            self.db.execute(query)
        except:
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)
            
        data = self.db.fetchone()
        if not data:
            self.errorMessage('boothost_no_such_nodegroup %s\n', nodegroup)
            sys.exit(-1)

        # Update the Kernel, initrd, and/or kernel paramaters if needed
        setstr = self.__mkUpdateSql(kernel, initrd, kparams)
        if setstr != '':
            # Need to update the database
            query = ('update nodegroups set %s where ngname="%s"' % (setstr, nodegroup))
            try:
                self.db.execute(query)
            except:
                self.errorMessage('boothost_unable_to_update_nodegroup %s\n', nodegroup)

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
            self.errorMessage('DB_Query_Error\n')
            sys.exit(-1)
            
        hostlist = self.db.fetchall()
        if hostlist == None :
            self.errorMessage("boothost_unable_to_get_nodegroup %s\n", nodegroup)
            sys.exit(-1)

        self.updatednodes = hostlist
        
        # Clean out and custom kernel, initrd, and kernel params
        setstr = self.__mkUpdateSql('NULL', 'NULL', 'NULL', state, localboot)
        if setstr != '':
            # Need to update the database
            query = ('update nodes set %s where '
                     'ngid=(select ngid from nodegroups '
                     'where ngname="%s")' % (setstr, nodegroup))
            try:
                self.db.execute(query)
            except:
                self.errorMessage('boothost_unable_to_update_nodegroup %s\n', nodegroup)

        # Iterate over the list of hosts
        if hostlist:
            for row in hostlist:
                self.__genNodesPXE(row[0])


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
        # Iterate over the list of hosts, and update their PXE files
        self.updatednodes = []
        for node in nodelist:
            self.__genNodesPXE(node, kernel, initrd, kparams, state, localboot)
            self.updatednodes.append(node)

        

class BootHostApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)   # Get the Lang stuff from the kusuapp class

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
                toolinst.toolVersion()
            elif args[i] == '-r':
                self.reinstall  = 1
            elif args[i] == '-l':
                if len(args) > (i+1):
                    toolinst.getNodeBootInfo(args[i+1])
                else:
                    toolinst.getAllBootInfo()
                sys.exit(0)
            else:
                # Now deal with all the other arguments that are not mutually exclusive
                if args[i] == '-t':
                    if len(args) > (i+1):
                        self.nodegroup = args[i+1]
                        self.updatewhat = 'NodeGroup'
                    else:
                        toolinst.toolHelp()
                elif args[i] == '-n':
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


    def run(self):
        """run - Run the application"""

        bhinst = boothost(self.gettext)
        self.parseargs(bhinst)

        if self.reinstall == 1:
            self.state = 'Expired'
            
        if self.updatewhat == 'NodeList':
            bhinst.genNodeListPXE(self.nodelist, self.newkernel,
                                  self.newinitrd, self.newkparms, self.state)
        elif self.updatewhat == 'NodeGroup':
            bhinst.genNodeGrpPXE(self.nodegroup, self.newkernel,
                                 self.newinitrd, self.newkparms, self.state)
        elif self.updatewhat == 'NodeUnSynced':
            bhinst.genNodeGrpPXE(self.nodegroup, self.newkernel,
                                 self.newinitrd, self.newkparms, self.state, '', 1)
        else:
            bhinst.toolHelp()

        # Check and reinstall if needed
        if self.reinstall == 1:
            if os.getuid() != 0:
                sys.stderr.write(_('boothost_root_reboot'))
                sys.exit(-2)

            print self._('boothost_reboot'),
            for name in bhinst.updatednodes:
                print "%s, " % name,
                
            #sys.exit(0)
            pdshcls = syncfun()
            pdshcls.runPdsh(bhinst.updatednodes, '/sbin/reboot')



app = BootHostApp()
app.run()

