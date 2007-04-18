#!/usr/bin/python
#
# $Id$
#
#   Copyright 2007 Platform Computing Corporation
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
#
#

# This file contains the classes for parsing the data from the
# Node installation Information.


from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import urllib


class NodeInstInfoHandler(ContentHandler):
    """This class provides the content handler for parsing the Node
    Installation Information.  The data from the NNI is stored in
    instance variables."""
    
    def __init__ (self):
        self.name        = ''    # Name of the node
        self.installers  = []    # List of avaliable installers
        self.repo        = ''    # Repo location
        self.ostype      = ''    # OS type
        self.installtype = ''    # Type of install to perform
        self.nodegrpid   = 0     # Node group ID
        self.appglobal   = {}    # Dictionary of all the appglobal data
        self.nics        = {}    # Dictionary of all the NIC info
        self.partitions  = {}    # Dictionary of all the Partition info.  Note key is only a counter
        self.packages    = []    # List of packages to install
        self.scripts     = []    # List of scripts to run
        
        # The following are for use by the handler internally
        self.partnum     = 0     # Counter used by Partition dictionary
        self.compstart   = 0     # Flag for the start of a component block
        self.packstart   = 0     # Flag for the start of a package block
        self.scrptstart  = 0     # Flag for the start of a script block
        self.data        = ''

    def startElement(self, name, attrs):
        if name == 'nodeinfo':
            self.name        = attrs.get('name',"")
            self.installers  = attrs.get('installers',"")
            self.repo        = attrs.get('repo',"")
            self.ostype      = attrs.get('ostype',"")
            self.installtype = attrs.get('installtype',"")
            self.nodegrpid   = attrs.get('nodegrpid',"")

        elif name == 'appglobals':
            name  = attrs.get('name',"")
            value = attrs.get('value',"")
            if name:
                self.appglobal[name] = value

        elif name == 'partition':
            device   = attrs.get('device',"")
            self.partitions[self.partnum] = { 'device'   : device,
                                              'mntpnt'   : attrs.get('mntpnt',""),
                                              'fstype'   : attrs.get('fstype',""),
                                              'size'     : attrs.get('size',""),
                                              'options'  : attrs.get('options',""),
                                              'preserve' : attrs.get('preserve',"") }
            self.partnum = self.partnum + 1

        elif name == 'nicinfo':
            device   = attrs.get('device',"")
            self.nics[device] = { 'device'  : device,
                                  'ip'      : attrs.get('ip',""),
                                  'subnet'  : attrs.get('subnet',""),
                                  'network' : attrs.get('network',""),
                                  'suffix'  : attrs.get('suffix',""),
                                  'gateway' : attrs.get('gateway',""),
                                  'dhcp'    : attrs.get('dhcp',""),
                                  'options' : attrs.get('options',"") }
        elif name == 'component':
            self.compstart = 1

        elif name == 'optpackage':
            self.packstart = 1 

        elif name == 'optscript':
            self.scrptstart = 1 

        else:
            return


    def endElement(self, name):
        if name == 'component':
            self.compstart = 0
            self.packages.append(self.data)
        elif name == 'optpackage':
            self.packstart = 0
            self.packages.append(self.data)
        elif name == 'optscript':
            self.scrptstart = 0
            self.scripts.append(self.data)
        self.data = ''


    def characters (self, ch):
        if self.compstart == 1 or self.packstart == 1 or self.scrptstart == 1:
            self.data += ch



class NNIFun():
    """This class is responsible for retrieving the NII"""
    
    def __init__ (self):
        self.state   = ''
        self.cfmflag = 0
        self.niiflag = 0
        self.installer = []     # List of all of the IP's for the primary installer node
        try:
            # fp = file('/proc/cpuinfo', 'r')
            fp = file('/tftpboot/kusu/pxelinux.cfg/00:11:22:33:44:00', 'r')  # Remove after testing
            for line in fp.readlines():
                for entry in string.split(line):
                    if entry[:8] == 'niihost=':
                        self.installer = string.split(entry[8:], ',')
            fp.close()
            
        except:
            print "ERROR:  The /proc/cmdline file is unavalible!"
        

    def setState(self, state):
        """setState - Set the value of the state.  This needs to be used in
        conjunction with the callNodeboot to actually cause the state to be set."""
        self.state = state[:20]    # Database size is the limiting factor

    def wantCFM(self, flag):
        """wantCFM - Set the flag to request the CFM data.  This needs to be used in
        conjunction with the callNodeboot to actually get the data."""
        if flag and flag == 1:
            self.cfmflag = 1
        else:
            self.cfmflag = 0

    def wantNII(self, flag):
        """wantNII - Set the flag to request the NII data.  This needs to be used in
        conjunction with the callNodeboot to actually get the data."""
        if flag and flag == 1:
            self.niiflag = 1
        else:
            self.niiflag = 0 

    def callNodeboot(self, url):
        if not self.state and not self.cfmflag and not self.niiflag :
            # Do nothing
            return
        
        options = '?'
        if self.niiflag:
            options += 'dump=1&'
        if self.cfmflag:
            options += 'getindex=1&'
        if self.state:
            options += 'state=%s&' % self.state
            


# Run the unittest if run directly
if __name__ == '__main__':

    niidata, header = urllib.urlretrieve("http://localhost/repos/nodeboot.cgi?dump=1&getindex=1")
    
    parser = make_parser()
    niihandler = NodeInstInfoHandler()

    parser.setContentHandler(niihandler)
    parser.parse(open(niidata)) 
    os.unlink(niidata)

    print "Name        = %s" % niihandler.name
    print "installers  = %s" % niihandler.installers
    print "repo        = %s" % niihandler.repo
    print "ostype      = %s" % niihandler.ostype
    print "installtype = %s" % niihandler.installtype
    print "nodegrpid   = %s" % niihandler.nodegrpid
    
    for i in niihandler.packages:
        print "Packages = %s" % i

    for i in niihandler.scripts:
        print "Scripts = %s" % i
        
    for i in niihandler.appglobal.keys():
        print "Key=%s, Value=%s" % (i, niihandler.appglobal[i])

    for i in niihandler.partitions.keys():
        print "------------------------------ Partitions: Key = %s" % i
        print "        Device   = %s" % (niihandler.partitions[i]['device'])
        print "        Mntpnt   = %s" % (niihandler.partitions[i]['mntpnt'])
        print "        fstype   = %s" % (niihandler.partitions[i]['fstype'])
        print "        size     = %s" % (niihandler.partitions[i]['size'])
        print "        options  = %s" % (niihandler.partitions[i]['options'])
        print "        preserve = %s" % (niihandler.partitions[i]['preserve'])
    
    for i in niihandler.nics.keys():
        print "------------------------------ NICS:  Key = %s" % i
        print "        Device  = %s" % (niihandler.nics[i]['device'])
        print "        IP      = %s" % (niihandler.nics[i]['ip'])
        print "        subnet  = %s" % (niihandler.nics[i]['subnet'])
        print "        network = %s" % (niihandler.nics[i]['network'])
        print "        suffix  = %s" % (niihandler.nics[i]['suffix'])
        print "        gateway = %s" % (niihandler.nics[i]['gateway'])
        print "        dhcp    = %s" % (niihandler.nics[i]['dhcp'])
        print "        options = %s" % (niihandler.nics[i]['options'])
    

