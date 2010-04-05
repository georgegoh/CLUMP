#!/usr/bin/python
#
# $Id: niifun.py 3264 2009-11-24 12:08:22Z ltsai $
#
#   Copyright 2007 Platform Computing Inc.
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


import string
import os
import sys
import urllib

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# ** The initrd's have basic Python installs.  Be careful what you import!
#from path import path

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
        self.components  = []    # List of components to install
        self.scripts     = []    # List of scripts to run
        self.cfm         = ''    # The CFM data
        self.ngtype      = ''    # Nodegroup Type
        self.repoid      = ''    # Repo ID
        self.dbpasswd    = ''    # DB Passwd
        self.ipmipasswd  = ''    # IPMI Passwd
        self.cfmsecret   = ''    # CFM Secret

        # The following are for use by the handler internally
        self.partnum     = 0     # Counter used by Partition dictionary
        self.compstart   = 0     # Flag for the start of a component block
        self.packstart   = 0     # Flag for the start of a package block
        self.scrptstart  = 0     # Flag for the start of a script block
        self.debugstart  = 0     # Flag for the start of a debug block
        self.cfmstart    = 0     # Flag for the start of a cfm block
        self.data        = ''


    def startElement(self, name, attrs):
        if name == 'nodeinfo':
            self.name        = attrs.get('name',"")
            self.installers  = attrs.get('installers',"")
            self.repo        = attrs.get('repo',"")
            self.ostype      = attrs.get('ostype',"")
            self.installtype = attrs.get('installtype',"")
            self.nodegrpid   = attrs.get('nodegrpid',"")
            self.ngtype      = attrs.get('ngtype',"")
            self.repoid      = attrs.get('repoid', "")
            self.dbpasswd    = attrs.get('dbpasswd',"")
            self.ipmipasswd  = attrs.get('ipmipasswd',"")
            self.cfmsecret   = attrs.get('cfmsecret',"")

        elif name == 'appglobals':
            name  = attrs.get('name',"")
            value = attrs.get('value',"")
            if name:
                self.appglobal[name] = value

        elif name == 'partition':
            device   = attrs.get('device',"")
            self.partitions[self.partnum] = { 'device'   : device,
                                              'partition'  : attrs.get('partition',""),
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
                                  'options' : attrs.get('options',""),
                                  'boot'    : attrs.get('boot',""),
                                  'mac'     : attrs.get('mac',""), 
                                  'type'    : attrs.get('type',"") }
        elif name == 'component':
            self.compstart = 1

        elif name == 'optpackage':
            self.packstart = 1 

        elif name == 'optscript':
            self.scrptstart = 1 

        elif name == 'debug':
            self.debugstart = 1

        elif name == 'cfm':
            self.cfmstart = 1
            
        else:
            return


    def endElement(self, name):
        if name == 'component':
            self.compstart = 0
            self.components.append(self.data)
        elif name == 'optpackage':
            self.packstart = 0
            self.packages.append(self.data)
        elif name == 'optscript':
            self.scrptstart = 0
            self.scripts.append(self.data)
        elif name == 'debug':
            self.debugstart = 0
            # Ignore the data
        elif name == 'cfm':
            self.cfmstart = 0
            self.cfm += (self.data)

        self.data = ''


    def characters (self, ch):
        if self.compstart == 1 or self.packstart == 1 or self.scrptstart == 1 or self.debugstart == 1 or self.cfmstart == 1:
            self.data += ch


    def saveAppGlobalsEnv (self, filename=''):
        """saveAppGlobalsEnv - Save the appglobals variable as a shell script which
        exports all of them.  This file can then be sourced in other scripts.
        It also saves useful parts of the NII"""
        if not filename:
            file = "/etc/profile.nii"
        else:
            file = filename

        try:
            fp = open(filename, 'w')
        except:
            return

        fp.write("#!/bin/sh\n#\n")
        fp.write("# This file is generated at install time.  It contains all\n")
        fp.write("# of the variables that were used to install this node.\n#\n")
        fp.write('export NII_HOSTNAME=%s\n' % self.name)
        fp.write('export NII_NGID=%s\n' % self.nodegrpid)
        fp.write('export NII_NGTYPE="%s"\n' % self.ngtype)
        fp.write('export NII_INSTALLERS="%s"\n' % self.installers)
        fp.write('export NII_REPO="%s"\n' % self.repo)
        fp.write('export NII_REPOID="%s"\n' % self.repoid)
        fp.write('export NII_OSTYPE="%s"\n' % self.ostype)
        fp.write('export NII_INSTALLTYPE="%s"\n' % self.installtype)

        cnt = 0
        fp.write('\n# NIC Definitions  Device:IP:Subnet:Network:suffix:gateway:dhcp:options:mac:type\n')
        for i in self.nics.keys():
            fp.write('export NII_NICDEF%i="%s|%s|%s|%s|%s|%s|%s|%s|%s|%s"\n' % ( cnt, self.nics[i]['device'],
                                                                         self.nics[i]['ip'],
                                                                         self.nics[i]['subnet'],
                                                                         self.nics[i]['network'],
                                                                         self.nics[i]['suffix'],
                                                                         self.nics[i]['gateway'],
                                                                         self.nics[i]['dhcp'],
                                                                         self.nics[i]['options'],
                                                                         self.nics[i]['mac'],
                                                                         self.nics[i]['type']))
            cnt = cnt + 1

        fp.write('\n')
        for i in self.appglobal.keys():
            fp.write('export %s="%s"\n' % (i, self.appglobal[i]))

        fp.close()


    def saveCFMSecret (self, filename=''):
        """saveCFMSecret - Save the CFM secret variable to the given file."""
        if not filename:
            file = '/mnt/etc/cfm/.cfmsecret'
        else:
            file = filename

        if not os.path.exists(os.path.dirname(file)):
            os.system('mkdir -p %s' % (os.path.dirname(file)))
        
        try:
            fp = open(file, 'w')
        except:
            return

        fp.write('%s' % self.cfmsecret.strip())
        fp.close()
        os.chmod(file, 0400)


    def saveIpmiPassword(self, ipmiPasswordFile):
        """ Saves the IPMI password file """
        try:
            fp = open(ipmiPasswordFile, 'w')
            fp.write('%s' % self.ipmipasswd.strip())
            fp.close()
            os.chmod(ipmiPasswordFile, 0400)
        except:
            return False
        return True


    def saveDbPasswd (self, filename=''):
        """saveDbPasswd - Save the db password file.  This is probably a misunderstanding"""
        if not filename:
            file = '/mnt/opt/kusu/etc/db.passwd'
        else:
            file = filename

        if not os.path.exists(os.path.dirname(file)):
            os.system('mkdir -p %s' % (os.path.dirname(file)))

        try:
            fp = open(file, 'w')
        except:
            return

        fp.write('%s' % self.dbpasswd.strip())
        fp.close()
        os.chmod(file, 0400)


class NIIFun:
    """This class is responsible for retrieving the NII"""
    
    def __init__ (self):
        self.state    = ''
        self.cfmflag  = 0
        self.niiflag  = 0
        self.nextboot = ''
        self.uid      = ''
        

    def setBootFrom(self, bootfrom):
        """setBootFrom - Set the value of the bootfrom.  This needs to be used in
        conjunction with the callNodeboot to actually cause the value to be set."""
        self.nextboot = bootfrom

        
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


    def setUID(self, uid):
        """ setUID - Set the value of the uid. This needs to be used in
        conjunction with the callNodeboot to actually cause the value to be set."""
        self.uid = str(uid)


    def callNodeboot(self, host):
        """callNodeboot  - Call the CGI script to gather the data, and return a file
        with the response in it."""
        if not self.state and not self.cfmflag and not self.niiflag and not self.nextboot:
            # Do nothing
            return
        
        options = 'http://%s/repos/nodeboot.cgi?' % host
        if self.niiflag:
            options += 'dump=1&'
        if self.cfmflag:
            options += 'getindex=1&'
        if self.state:
            options += 'state=%s&' % self.state
        if self.state:
            options += 'boot=%s&' % self.nextboot
        if self.uid:
            options += 'uid=%s&' % self.uid
            
        print "URL: %s" % options[:-1]
        (niidata, header) = urllib.urlretrieve(options[:-1])
        return niidata


# Run the unittest if run directly
if __name__ == '__main__':
    # The host is is using in the URL has to be in the database
    #(niidata, header) = urllib.urlretrieve("http://fe3/repos/nodeboot.cgi?dump=1&getindex=1")
    (niidata, header) = urllib.urlretrieve("http://172.20.0.1/repos/nodeboot.cgi?dump=1&getindex=1")
    
    fp = open(niidata)
    print fp.readlines()
    fp.close()
    
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

    for i in niihandler.components:
        print "Components = %s" % i
 
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
    
    print "CFM Data = %s" % niihandler.cfm

    niihandler.saveAppGlobalsEnv('/tmp/profile.nii')
    print "Wrote:  /tmp/profile.nii"

    niihandler.saveDbPasswd('/tmp/opt/kusu/etc/db.passwd')
    print "Wrote:  /tmp/opt/kusu/etc/db.passwd"

    # niihandler.saveCFMSecret('/tmp/etc/cfm/.cfmsecret')
    # print "Wrote:  /tmp/etc/cfm/.cfmsecret"
