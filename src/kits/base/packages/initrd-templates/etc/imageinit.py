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

initrddebug = 0
dlp = ''
class ImagedNodeConfiger:
    """This class contains the code for doing the steps above"""

    def __init__(self):
        self.modules = []
        self.ifs = []
        self.installer = []
        self.logfilefp = 0
        global initrddebug
        initrddebug = 0
        try:
            fp = file('/proc/cmdline', 'r')
            for line in fp.readlines():
                for entry in string.split(line):
                    if entry[:8] == 'niihost=':
                        self.installer = string.split(entry[8:], ',')
                    if entry == 'initrddebug':
                        initrddebug = 1
            fp.close()
            self.test = 0
        except:
            print "ERROR:  Unable to read the /proc/cmdline"
            self.installer = "10.1.0.1"
            self.test = 1


    def log(self, mesg):
        """log - Output messages to a log file"""
        try:
            self.logfilefp = file('/tmp/imageinit.log', 'a')
            self.logfilefp.write(mesg)
            self.logfilefp.close()
        except:
            self.logfilefp = 0
            print "Logging unavailable!"


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
            status = os.system('udhcpc -n -i eth%i > /dev/null 2>&1' % i)
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
        


    def getImage(self, ngid, disked):
        """getImage - Download and extract the image to use as the root filesystem.
        The 'disked' flag is used to control where the image is downloaded to"""
        image = "http://%s/images/%s.img.tar.bz2" % (bestip, ngid)
        sys.stdout.write("Downloading image: %s to " % image)
        if disked:
            os.chdir('/newroot/tmp')
            sys.stdout.write("/newroot/tmp")
        else:
            os.chdir('/tmp')
            sys.stdout.write("/tmp")
            
        self.log("Downloading image: %s\n" % image)
        sys.stdout.write("Downloading image: %s\n" % image)
        status = os.system('wget %s' % image)
        if os.WEXITSTATUS(status) != 0:
            self.log("Unable to download image from: %s\n" % image)
            sys.exit(0)
        os.chdir('/newroot')
        self.log("Extracting image\n")
        sys.stdout.write("Extracting image\n")
        if disked:
            es = os.system('tar jxf /newroot/tmp/%s.img.tar.bz2' % ngid)
        else:
            es = os.system('tar jxf /tmp/%s.img.tar.bz2' % ngid)
        if es != 0:
            sys.stdout.write("FATAL:  Failed to extract image!\n")
            sys.stdout.write("There may not be enough disk space\n")
        if disked:
            os.unlink('/newroot/tmp/%s.img.tar.bz2' % ngid)
        else:
            os.unlink('/tmp/%s.img.tar.bz2' % ngid)

        
class DirtyLittlePartitioner:
    """ This class will deal with partitioning disks for imaged nodes
    until the real partitioning code can be used."""

    def __init__(self):
        self.firstdisk = ""
        self.rootdev = ""
        self.bootpartnum = 0
        self.partinfo  = {}    # Dictionary of all the Partition info.
        devlist = []
        pdir = "/proc/partitions"
        if os.path.exists(pdir):
            fin = open(pdir, 'r')
            data= fin.readlines()
            fin.close()
            for line in data[2:]:
                dev = string.split(line)[-1:]
                c = dev[0]
                if c[:4] == 'loop' or c[:2] == 'fd' or c[:2] == 'md' or str.isdigit(c[-1:]):
                    continue
                devlist.append(dev[0])
                print "Found: %s" % dev[0]

        else:
            # No disk found!
            print "FATAL:  No Disk Found!"
            print "The kernel modules for the drive controller is not loaded."
            sys.exit(4)

        preference = ['sda', 'sdb', 'sdc', 'sdd', 'hda', 'hdb', 'hdc', 'hdd', 'none']
        best = ''
        for best in preference:
            print "Checking for %s in %s" % (best, devlist)
            if best in devlist:
                break

        self.firstdisk = best
        print "First disk to use is: %s" % best

        
    def addPart(self, pnum, ptype, size, mntpnt):
        '''addPart - Store the partition information in a class structure'''
        self.partinfo[pnum] = { 'type'   : ptype,
                                'size'   : size,
                                'mntpnt' : mntpnt,
                                'boot'   : '',
                                'device' : "/dev/%s%s" % (self.firstdisk, pnum) }
        

    def findType(self, fstype):
        if fstype == 'linux-swap':
            ptype = 82  # Swap
        elif fstype == 'ext2':
            ptype = 83  # Linux partition
        elif fstype == 'ext3':
            ptype = 83  # Linux partition
        elif fstype == 'fat32':
            ptype = 82  # Dos partition
        elif fstype == 'ntfs':
            ptype = 82  # Windows partition
        else:
            ptype = 83  # Linux partition
        return(ptype)


    def wipeParts(self):
        '''wipeParts - Delete all partitions'''
        try:
            fp = file('/tmp/part0', 'w')
            fp.write(';\n;\n;\n;\n')
            fp.close()
        except:
            print "Unable to partition disk!"
            return
            
        os.system('sfdisk /dev/%s < /tmp/part0 >/dev/null 2>/dev/null' % (self.firstdisk))


    def partitionDisk(self):
        '''partitionDisk - Create the partitions'''
        # Determine which to boot
        boot = -1
        for i in self.partinfo.keys():
            if self.partinfo[i]['mntpnt'] == '/boot':
                boot = i
                break
            if self.partinfo[i]['mntpnt'] == '/':
                boot = i
                    
        if boot == -1:
            print "ERROR:  No root or /boot partition available!"
            sys.exit(-6)

        self.partinfo[boot]['boot'] = "*"
        
        # Make the sfdisk strings
        for i in self.partinfo.keys():
            type = self.findType(self.partinfo[i]['type'])
            if i == 1:
                self.partinfo[i]['sfdiskstr'] =  '0,%s,%i,%s\n' % (self.partinfo[i]['size'], type, self.partinfo[i]['boot'])
            else:
                self.partinfo[i]['sfdiskstr'] =  ',%s,%i,%s\n' % (self.partinfo[i]['size'], type, self.partinfo[i]['boot'])

        try:
            fp = file('/tmp/partitions', 'w')
            if self.partinfo.has_key('1'):
                fp.write(self.partinfo['1']['sfdiskstr'])
            else:
                fp.write('0,0,0,\n')
            if self.partinfo.has_key('2'):
                fp.write(self.partinfo['2']['sfdiskstr'])
            else:
                fp.write('0,0,0,\n')
            if self.partinfo.has_key('3'):
                fp.write(self.partinfo['3']['sfdiskstr'])
            else:
                fp.write('0,0,0,\n')
            if self.partinfo.has_key('4'):
                fp.write(self.partinfo['4']['sfdiskstr'])
            else:
                fp.write('0,0,0,\n')
            
            fp.close()
        except:
            print "Unable to partition disk!"
            return
        print "****  Running:  sfdisk -uM /dev/%s < /tmp/partitions" % (self.firstdisk)
        os.system('sfdisk -uM /dev/%s < /tmp/partitions >/dev/null 2>/dev/null' % (self.firstdisk))


    def formatPart(self):
        '''prepPart  - Format the partitions on the disk, and use swap'''
        for i in self.partinfo.keys():
            device = "/dev/%s%s" % (self.firstdisk, i)
            type = self.partinfo[i]['type']
            print "Formatting %s as %s" % (device, type)
            if type == 'linux-swap':
                os.system('mkswap %s >> /tmp/imageinit.log 2>&1' % device)
                os.system('swapon %s >> /tmp/imageinit.log 2>&1' % device)
            elif type == 'ext2':
                os.system('mke2fs -q %s >> /tmp/imageinit.log 2>&1' % device)
            elif type == 'ext3':
                os.system('mke2fs -j -q %s >> /tmp/imageinit.log 2>&1' % device)
            else:
                print "Unknown partition type: %s" % type


    def mountParts(self):
        '''mountParts - Mount the partitions.'''
        # Find root key first
        rkey = ''
        for i in self.partinfo.keys():
            if self.partinfo[i]['mntpnt'] == '/':
                rkey = i

        if rkey == '':
            print "ERROR:  No root partition defined!"
            sys.exit(-7)
            
        print "Mounting %s as root" % self.partinfo[rkey]['device']
        os.system('mount %s /newroot/ >> /tmp/imageinit.log 2>&1' % self.partinfo[rkey]['device'])

        # Now mount the other filesystems
        for i in self.partinfo.keys():
            if i == rkey:
                continue
            if self.partinfo[i]['type'] == 'linux-swap':
                continue
            os.makedirs('/newroot%s' % self.partinfo[i]['mntpnt'], mode=0755)
            os.system('mount %s /newroot%s >> /tmp/imageinit.log 2>&1' % (self.partinfo[i]['device'], self.partinfo[i]['mntpnt']))


    def unmountParts(self):
        '''unmountParts - Unmount the partitions.'''
        # Find root key first
        rkey = ''
        for i in self.partinfo.keys():
            if self.partinfo[i]['mntpnt'] == '/':
                rkey = i

        # Unmount the other filesystems first
        for i in self.partinfo.keys():
            if i == rkey:
                continue
            if self.partinfo[i]['type'] == 'linux-swap':
                continue
            os.system('umount /newroot%s >> /tmp/imageinit.log 2>&1' % (self.partinfo[i]['mntpnt']))

        os.system('umount /newroot%s >> /tmp/imageinit.log 2>&1' % (self.partinfo[i]['mntpnt']))
            
                
    def addGrub(self):
        '''addGrub  - Install the grub bootloader'''
        flist = glob.glob('/newroot/boot/initrd*')
        if len(flist) == 0:
            print "ERROR:  Unable to locate the initrd!"
            sys.exit(-2)
        init = os.path.basename(flist[0])
        
        flist = glob.glob('/newroot/boot/vmlin*')
        if len(flist) == 0:
            print "ERROR:  Unable to locate the kernel for imaged nodes!"
            sys.exit(-3)
        kern = os.path.basename(flist[0])

        if not os.path.exists('/newroot/usr/share/grub/'):
            print "ERROR:  Unable to locate the grub package!"
            sys.exit(-4)

        # Find root dev, and bootable dev
        rkey = 0
        bdev = 0
        for i in self.partinfo.keys():
            if self.partinfo[i]['mntpnt'] == '/':
                rkey = i
            if self.partinfo[i]['boot'] == '*':
                bdev = string.atoi(i) - 1

        os.system('cp -r /newroot/usr/share/grub/*/* /newroot/boot/grub')
        fp = file('/newroot/boot/grub/grub.conf', 'w')
        fp.write('# Imaged node \n')
        fp.write('# \n')
        fp.write('default=0\n')
        fp.write('timeout=2\n')
        fp.write('\n')
        fp.write('title Imaged Node\n')
        fp.write('        root (hd0,%s)\n' % bdev)
        fp.write('        kernel /%s ro root=%s\n' % (kern, self.partinfo[rkey]['device']))
        fp.write('        initrd /%s\n' % (init))
        fp.close()
        

app = ImagedNodeConfiger()
app.loadModules()
app.upInterfaces()

bestip = app.findBestInstaller()
app.log("Best Installer = %s\n" % bestip )

niiinfo = NIIFun()
niiinfo.setState('Installed')
niiinfo.wantNII(1)
# niiinfo.wantCFM(1)  # Can't do anything with it yet

try:
    niifile = niiinfo.callNodeboot(bestip)
except:
    app.log("ERROR:  Unable to get NII from:  %s\n" % bestip)
    sys.exit(-1)
    
niihandler = NodeInstInfoHandler()
parser = make_parser() 
parser.setContentHandler(niihandler)
parser.parse(open(niifile)) 

if len(niihandler.partitions.keys()) > 0 and niihandler.installtype == 'disked':
    disked = True
    app.log("Using local disk\n")
else:
    disked = False
    app.log("Not using local disk\n")

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

if disked:
    os.makedirs('/newroot/', mode=0755)
else:
    # Make a RAM root filesystem
    app.mkNewRoot('/newroot')

if disked and 'gdfgd' == 'FAIL':
    # Bring up the partitions according to the NII
    # TODO
    #
    # Need to get a lot more modules from the installer before this can work
    #from nodeinstaller import adaptNIIPartition
    #from kusu.partitiontool import DiskProfile
    #from kusu.installer.defaults import setupDiskProfile
    #disk_profile = DiskProfile(True) # Start with blank disk.
    #schema, disk_profile = adaptNIIPartition(niihandler, disk_profile)
    #setupDiskProfile(disk_profile, schema)
    #disk_profile.commit()
    #disk_profile.formatAll()
    print ""

if disked:
    dlp = DirtyLittlePartitioner()
    if dlp.firstdisk == 'none':
        print "FATAL:  No Disk Found!"
        print "The kernel modules for the drive controller may not be loaded."
        print "Type:  Alt-F2, login and look at /proc/partitions"
        sys.exit(4)
        
    app.log("Trying to partition %s\n" % dlp.firstdisk)
    dlp.wipeParts()
    for i in niihandler.partitions.keys():
        # This is all we will deal with.
        if niihandler.partitions[i]['device'] == "1":
            if niihandler.partitions[i]['partition'] == '':
                continue

            dlp.addPart(niihandler.partitions[i]['partition'],
                        niihandler.partitions[i]['fstype'],
                        niihandler.partitions[i]['size'],
                        niihandler.partitions[i]['mntpnt'])

    dlp.partitionDisk()
    dlp.formatPart()
    dlp.mountParts()
    

os.makedirs('/newroot/etc', mode=0755)
os.makedirs('/newroot/etc/cfm', mode=0755)
os.makedirs('/newroot/tmp', mode=0777)
os.system('cp /.cfmsecret /newroot/etc/cfm/')
os.system('chmod 400 /newroot/etc/cfm/.cfmsecret')
os.system('chown root /newroot/etc/cfm/.cfmsecret')
niihandler.saveAppGlobalsEnv('/newroot/etc/profile.nii')
app.getImage(niihandler.nodegrpid, disked)

os.system('hostname %s' % niihandler.name)

if disked:
    # Install the bootloader
    dlp.addGrub()
    dlp.unmountParts()
    # Exit with 99 to force reboot 
    sys.exit(99)

app.log("INFO: Exiting imageinit with:  %i" % initrddebug)
if initrddebug == 1:
    # Exit with 1 to stop the switch_root
    sys.exit(1)

sys.exit(0)
