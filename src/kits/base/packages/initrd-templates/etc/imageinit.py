#!/usr/bin/python

# $Id$
#
#  Copyright (C) 2007 Platform Computing Inc
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

# This script is responsible for:
#     - Loading the required modules
#     - Bringing the NICs up to request an IP address
#     - Downloading the NII
#     - Configuring the NICs
#     - Partitioning the disks (If needed)
#     - Copying the image over

import os
import sys
import string
import glob
import ipfun

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from niifun import NIIFun
from niifun import NodeInstInfoHandler

MODULE_LOAD_LIST='/etc/module-load-order.lst'

class ImagedNodeConfiger:
    """This class contains the code for doing the steps above"""

    def __init__(self):
        self.modules = []
        self.ifs = []
        self.installer = []
        try:
            fp = file('/proc/cmdline', 'r')
            for line in fp.readlines():
                for entry in string.split(line):
                    if entry[:8] == 'niihost=':
                        self.installer = string.split(entry[8:], ',')
            fp.close()
            self.test = 0
        except:
            print "ERROR:  Unable to read the /proc/cmdline"
            self.installer = "10.1.0.1"
            self.test = 1

        try:
            self.logfilefp = file('/tmp/imageinit.log', 'w')
        except:
            self.logfilefp = 0

            
    def log(self, mesg):
        """log - Output messages to a log file"""
        self.logfilefp.write(mesg)


    def loadModules(self):
        """loadModules - Load the modules in the provided list."""
        if self.test:
            self.log("Skipping module loading")
            return
        
        global MODULE_LOAD_LIST
        
        if os.path.exists(MODULE_LOAD_LIST):
            fp = open(MODULE_LOAD_LIST, 'r')
            self.modules = fp.readlines()
            fp.close()
            for mod in self.modules:
                self.log("Loading:  %s" % mod)
                sys.stdout.write("Loading module:  %s" % mod)
                os.system('modprobe %s > /dev/null 2>&1' % mod)
        else:
            self.log("No modules to load!\n")


    def upInterfaces(self):
        """upInterfaces - Try to bring up the interfaces using DHCP"""
        for i in range(0,3):
            status = os.system('udhcpc -i eth%i > /dev/null 2>&1' % i)
            if os.WEXITSTATUS(status) == 0:
                self.ifs.append('eth%i' % i)

        self.log("Started interfaces:  %s\n" % self.ifs)


    def setInterface(self, device, ip, subnet, dgateway=''):
        """setInterface - Configure the named device with the given ip,
        and subnet mask.  If the gateway is provided it will also set
        the default route."""
        if not device or not ip or not subnet:
            return

        os.system('ifconfig %s netmask %s %s' % (device, subnet, ip))
        if dgateway:
            # Set the default route
            os.system('route add -net default gw %s' % dgateway)
            

    def findBestInstaller(self):
        """findBestInstaller - Find the best IP address to get the NII"""
        if len(self.installer) == 1:
            return self.installer[0]

        for interface in self.ifs:
            cmd = 'ifconfig %s |grep inet |grep Mask' % interface
            ip = ''
            mask = ''
            for retline in os.popen(cmd).readlines():
                t = string.split(retline)
                for data in t[1:]:
                    ent = string.split(data, ':')
                    if ent[0] == 'addr':
                        ip = ent[1]
                    elif ent[0] == 'Mask':
                        mask = ent[1]
            if ip and mask:
                self.log("Address:  %s,  Mask:  %s\n" % (ip, mask))

                for instip in self.installer:
                    print "Testing:  %s, %s, %s" % (ip, mask, instip)
                    if ipfun.onNetwork(ip, mask, instip):
                        # This is the interface to use
                        return instip
                    
        # Did not find an IP.  Try the first one.
        return self.installer[0]


    def mkNewRoot(self, newroot):
        """mkNewRoot - Make a new root filesystem to run from."""
        os.makedirs(newroot, mode=0777)
        os.system('mount tmpfs %s -t tmpfs' % newroot)
        


    def getImage(self, ngid):
        """getImage - Download and extract the image to use as the root filesystem"""
        image = "http://%s/images/%s.img.tar.bz2" % (bestip, ngid)
        os.chdir('/tmp')
        self.log("Downloading image: %s\n" % image)
        sys.stdout.write("Downloading image: %s\n" % image)
        status = os.system('wget %s' % image)
        if os.WEXITSTATUS(status) != 0:
            self.log("Unable to download image from: %s\n" % image)
            sys.exit(0)
        os.chdir('/newroot')
        self.log("Extracting image\n")
        sys.stdout.write("Extracting image\n")
        os.system('tar jxf /tmp/%s.img.tar.bz2' % ngid)
        


app = ImagedNodeConfiger()
app.loadModules()
app.upInterfaces()

bestip = app.findBestInstaller()
app.log("Best Installer = %s" % bestip )

niiinfo = NIIFun()
niiinfo.setState('Installed')
niiinfo.wantNII(1)
# niiinfo.wantCFM(1)  # Can't do anything with it yet

try:
    niifile = niiinfo.callNodeboot(bestip)
except:
    app.log("ERROR:  Unable to get NII from:  %s" % bestip)
    sys.exit(-1)
    
niihandler = NodeInstInfoHandler()
parser = make_parser() 
parser.setContentHandler(niihandler)
parser.parse(open(niifile)) 

app.log("Name        = %s\n" % niihandler.name)
app.log("installers  = %s\n" % niihandler.installers)
app.log("repo        = %s\n" % niihandler.repo)
app.log("ostype      = %s\n" % niihandler.ostype)
app.log("installtype = %s\n" % niihandler.installtype)
app.log("nodegrpid   = %s\n" % niihandler.nodegrpid)

for i in niihandler.partitions.keys():
    app.log("------------------------------ Partitions: Key = %s\n" % i)
    app.log("        Device    = %s\n" % (niihandler.partitions[i]['device']))
    app.log("        Partition = %s\n" % (niihandler.partitions[i]['partition']))    
    app.log("        Mntpnt    = %s\n" % (niihandler.partitions[i]['mntpnt']))
    app.log("        fstype    = %s\n" % (niihandler.partitions[i]['fstype']))
    app.log("        size      = %s\n" % (niihandler.partitions[i]['size']))
    app.log("        options   = %s\n" % (niihandler.partitions[i]['options']))
    app.log("        preserve  = %s\n" % (niihandler.partitions[i]['preserve']))

if len(niihandler.partitions.keys()) > 0:
    # Bring up the partitions according to the NII
    # TODO
    #
    from nodeinstaller import adaptNIIPartition
    from kusu.partitiontool import DiskProfile
    from kusu.installer.defaults import setupDiskProfile
    disk_profile = DiskProfile(True) # Start with blank disk.
    schema, disk_profile = adaptNIIPartition(niihandler, disk_profile)
    setupDiskProfile(disk_profile, schema)
    disk_profile.commit()
    disk_profile.formatAll()

for i in niihandler.nics.keys():
    app.log("------------------------------ NICS:  Key = %s" % i)
    app.log("        Device  = %s\n" % (niihandler.nics[i]['device']))
    app.log("        IP      = %s\n" % (niihandler.nics[i]['ip']))
    app.log("        subnet  = %s\n" % (niihandler.nics[i]['subnet']))
    app.log("        network = %s\n" % (niihandler.nics[i]['network']))
    app.log("        suffix  = %s\n" % (niihandler.nics[i]['suffix']))
    app.log("        gateway = %s\n" % (niihandler.nics[i]['gateway']))
    app.log("        dhcp    = %s\n" % (niihandler.nics[i]['dhcp']))
    app.log("        options = %s\n" % (niihandler.nics[i]['options']))

# Bring up the interfaces according to the NII
for i in niihandler.nics.keys():
    if niihandler.nics[i]['dhcp'] == 0:
        if niihandler.nics[i]['gateway'] != '':
            app.setInterface(niihandler.nics[i]['device'],
                             niihandler.nics[i]['ip'],
                             niihandler.nics[i]['subnet'],
                             niihandler.nics[i]['gateway'])
        else:
            app.setInterface(niihandler.nics[i]['device'],
                             niihandler.nics[i]['ip'],
                             niihandler.nics[i]['subnet'])

# Download the image, and store the NII
app.mkNewRoot('/newroot')
os.makedirs('/newroot/etc', mode=0755)
niihandler.saveAppGlobalsEnv('/newroot/etc/profile.nii')
app.getImage(niihandler.nodegrpid)
os.unlink('/tmp/%s.img.tar.bz2' % niihandler.nodegrpid)
os.system('hostname %s' % niihandler.name)
