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
import shutil
import string
import glob
import ipfun
import time
import sha

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from niifun import NIIFun
from niifun import NodeInstInfoHandler

MODULE_LOAD_LIST='/etc/module-load-order.lst'
IMAGEINIT_LOGFILE='/tmp/imageinit.log'
SLES_CONFIGURATION_SCRIPT='/newroot/configure_sles.sh'

initrddebug = 0


class NodeConfigurator:
    """This class contains the code for doing the steps above"""

    def __init__(self):
        self.modules = []
        self.ifs = []
        self.installer = []
        self.logfilefp = 0
        self.niihandler = None
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
        """Logs a message to the IMAGEINIT_LOFILE"""
        try:
            self.logfilefp = file(IMAGEINIT_LOGFILE, 'a')
            self.logfilefp.write(mesg)
            self.logfilefp.close()
        except:
            self.logfilefp = 0
            print "Logging unavailable!"

    def loadModules(self):
        """Loads the modules in the MODULE_LOAD_LIST file."""
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
        """Tries to bring up the interfaces using DHCP"""
        dhcp_client_cmd = ''
        if os.path.exists('/sbin/udhcpc'):
            dhcp_client_cmd = 'udhcpc -n -i'
        else:
            dhcp_client_cmd = 'dhclient -lf /tmp/dhclient.leases -1'
        for i in range(0,3):
            status = os.system('%s eth%i > /dev/null 2>&1' % (dhcp_client_cmd, i))
            if os.WEXITSTATUS(status) == 0:
                self.ifs.append('eth%i' % i)
            else:
                print "%s eth%i exited with: %i" % (dhcp_client_cmd, i, os.WEXITSTATUS(status))

        print "Started interfaces:  %s\n" % self.ifs
        self.log("Started interfaces:  %s\n" % self.ifs)

    def getPhysicalAddressList(self):
        """ Returns a list of integer MAC addresses for the Physical interfaces."""
        macs = []

        for dir in ['', '/sbin/', '/usr/sbin']:
            try:
                pipe = os.popen(os.path.join(dir, 'ifconfig'))
            except IOError:
                continue
            else:
                break

        for line in pipe:
            words = line.lower().split()
            for i in range(len(words)):
                if words[i] in ['hwaddr', 'ether']:
                    macs.append(int(words[i + 1].replace(':', ''), 16))

        return macs

    def getLowestPhysicalAddress(self):
        """Returns the lowest integer Physical address."""
        macs = self.getPhysicalAddressList()

        for mac in macs:
            if 'low' not in locals() or mac < low:
                low = mac

        try:
            return low
        except UnboundLocalError:
            return ''

    def genUID(self):
        """Returns a time invariant unique identifier string."""
        mac = self.getLowestPhysicalAddress()

        if not mac:
            return ''

        s = sha.new(str(mac))
        return s.hexdigest()

    def setInterface(self, device, ip, subnet, dgateway=''):
        """Configures the named device with the given ip and subnet mask.
           If the gateway is provided it will also set the default route."""
        if not device or not ip or not subnet:
            return

        os.system('ifconfig %s netmask %s %s' % (device, subnet, ip))
        if dgateway:
            # Set the default route
            os.system('route add -net default gw %s' % dgateway)

    def findBestInstaller(self):
        """Finds the best IP address to get the NII"""
        if len(self.installer) == 1:
            return self.installer[0]

        print "Ifs = %s" % self.ifs
        if self.ifs == []:
            print "******************************************************************"
            print "*                                                                *"
            print "*  No Network interfaces are available!  The correct kernel      *"
            print "*  module for this machines NICs may not have been included.     *"
            print "*  Determine which module is used by using a package based       *"
            print "*  then including the module in the diskless nodegroup.          *"
            print "*                                                                *"
            print "******************************************************************"
            time.sleep(60)
            print "Rebooting....."
            # Exit with 99 to force reboot
            sys.exit(99)
            
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
                    if ipfun.onNetwork(ip, mask, instip):
                        # This is the interface to use
                        return instip
                    
        # Did not find an IP.  Try the first one.
        print "Failed to find the best installer IP!"
        return self.installer[0]

    def mkNewRoot(self, newroot):
        """Makes a new root filesystem to run from."""
        os.makedirs(newroot, mode=0777)
        os.system('mount tmpfs %s -t tmpfs' % newroot)

    def getImage(self, ngid, disked):
        """Downloads and extracts the image to use as the root filesystem.
        The 'disked' flag is used to control where the image is downloaded to"""
        image = "http://%s/images/%s.img.tar.bz2" % (bestip, ngid)
        sys.stdout.write("Downloading image: %s to " % image)
        if disked:
            os.chdir('/newroot/tmp')
            sys.stdout.write("/newroot/tmp\n")
        else:
            os.chdir('/tmp')
            sys.stdout.write("/tmp\n")
            
        while True:
            self.log("Downloading image: %s\n" % image)
            sys.stdout.write("Downloading image: %s\n" % image)
            status = os.system('wget %s' % image)
            if os.WEXITSTATUS(status) != 0:
                self.log("Unable to download image from: %s\nWill retry in 30 seconds.\n" % image)
                time.sleep(30)
            else:
                break

        os.chdir('/newroot')
        self.log("Extracting image\n")
        sys.stdout.write("Extracting image\n")
        if disked:
            es = os.system('tar jxf /newroot/tmp/%s.img.tar.bz2 2>/dev/null' % ngid)
        else:
            es = os.system('tar jxf /tmp/%s.img.tar.bz2 2>/dev/null' % ngid)
        if es != 0:
            sys.stdout.write("FATAL:  Failed to extract image!\n")
            sys.stdout.write("There may not be enough disk space\n")
        if disked:
            os.unlink('/newroot/tmp/%s.img.tar.bz2' % ngid)
        else:
            os.unlink('/tmp/%s.img.tar.bz2' % ngid)

    def setupSystem(self, niihandler, bestip):
        """Sets up the following:
           - network config (ifcfg files, resolv.conf, default gateway)
           - timezone and system clock settings"""

        hostname = niihandler.name
        gateway = bestip

        # Set up network config for rhel
        if not os.path.isdir('/newroot/etc/sysconfig/network'):
            f = open('/newroot/etc/sysconfig/network', 'w')
            f.write('NETWORKING=yes\n')
            f.write('NETWORKING_IPV6=yes\n')
            f.write('HOSTNAME=%s\n' % hostname)
            f.write('GATEWAY=%s\n' % gateway)
            f.close()
       
        # Set up network config for sles
        if os.path.isfile('/newroot/etc/HOSTNAME'):
            f = open('/newroot/etc/HOSTNAME', 'w')
            f.write('%s\n' % hostname)
            f.close()
        if os.path.isdir('/newroot/etc/sysconfig/network'):
            f = open('/newroot/etc/sysconfig/network/routes', 'w')
            f.write('default %s - -\n' % gateway)
            f.close()
            
        # setup timezone
        timezone = niihandler.appglobal['Timezone_zone']
        if not os.path.exists(os.path.join('/newroot/usr/share/zoneinfo', timezone)):
            self.log("WARNING:  The tzdata package has not been included in the image!\n")
        else:
            shutil.copy(os.path.join('/newroot/usr/share/zoneinfo', timezone), '/newroot/etc/localtime')

        hwclock_args = '--hctosys'
        if niihandler.appglobal['Timezone_utc'] == '1':
            hwclock_args += ' -u'
        os.system('hwclock %s > /dev/null 2>&1' % hwclock_args)
 
        f = open('/newroot/etc/sysconfig/clock', 'w')
        if os.path.exists('/newroot/etc/SuSE-release'):
            f.write('TIMEZONE="%s"\n' % timezone)
            if niihandler.appglobal['Timezone_utc'] == '1':
                f.write('HWCLOCK="-u"\n')
            else:
                f.write('HWCLOCK="--localtime"\n')
            f.write('SYSTOHC="yes"\n')
        else:
            f.write('ZONE="%s"\n' % timezone)
            if niihandler.appglobal['Timezone_utc'] == '1':
                f.write('UTC=true\n')
            else:
                f.write('UTC=false\n')
            f.write('ARC=false\n')
        f.close()

        # setup /etc/resolv.conf
        f = open('/newroot/etc/resolv.conf', 'w')
        f.write('search %s\n' % niihandler.appglobal['DNSZone'])
        if niihandler.appglobal['InstallerServeDNS'] == '1':
            f.write('nameserver %s\n' % bestip)
        else:
            for dns in ['dns1', 'dns2', 'dns3']:
                if niihandler.appglobal.has_key(dns):
                    f.write('search %s\n' % niihandler.appglobal[dns])
        f.close()

    def logNiiInformation(self, niihandler=None):
        self.niihandler = niihandler
        self.log("Name        = %s\n" % self.niihandler.name)
        self.log("installers  = %s\n" % self.niihandler.installers)
        self.log("repo        = %s\n" % self.niihandler.repo)
        self.log("ostype      = %s\n" % self.niihandler.ostype)
        self.log("installtype = %s\n" % self.niihandler.installtype)
        self.log("nodegrpid   = %s\n" % self.niihandler.nodegrpid)
        for i in self.niihandler.partitions.keys():
            self.log("------------------------------ Partitions: Key = %s\n" % i)
            self.log("        Device    = %s\n" % (self.niihandler.partitions[i]['device']))
            self.log("        Partition = %s\n" % (self.niihandler.partitions[i]['partition']))    
            self.log("        Mntpnt    = %s\n" % (self.niihandler.partitions[i]['mntpnt']))
            self.log("        fstype    = %s\n" % (self.niihandler.partitions[i]['fstype']))
            self.log("        size      = %s\n" % (self.niihandler.partitions[i]['size']))
            self.log("        options   = %s\n" % (self.niihandler.partitions[i]['options']))
            self.log("        preserve  = %s\n" % (self.niihandler.partitions[i]['preserve']))
        for i in self.niihandler.nics.keys():
            self.log("------------------------------ NICS:  Key = %s\n" % i)
            self.log("        Device  = %s\n" % (self.niihandler.nics[i]['device']))
            self.log("        IP      = %s\n" % (self.niihandler.nics[i]['ip']))
            self.log("        subnet  = %s\n" % (self.niihandler.nics[i]['subnet']))
            self.log("        network = %s\n" % (self.niihandler.nics[i]['network']))
            self.log("        suffix  = %s\n" % (self.niihandler.nics[i]['suffix']))
            self.log("        gateway = %s\n" % (self.niihandler.nics[i]['gateway']))
            self.log("        dhcp    = %s\n" % (self.niihandler.nics[i]['dhcp']))
            self.log("        options = %s\n" % (self.niihandler.nics[i]['options']))

    def configureNiiInterfaces(self):
        """Brings up the interfaces according to NII"""
        for i in self.niihandler.nics.keys():
            if self.niihandler.nics[i]['dhcp'] == 0:
                if self.niihandler.nics[i]['gateway'] != '':
                    self.setInterface(self.niihandler.nics[i]['device'],
                                      self.niihandler.nics[i]['ip'],
                                      self.niihandler.nics[i]['subnet'],
                                      self.niihandler.nics[i]['gateway'])
                else:
                    self.setInterface(self.niihandler.nics[i]['device'],
                                      self.niihandler.nics[i]['ip'],
                                      self.niihandler.nics[i]['subnet'])


class DirtyLittlePartitioner:
    """ This class deals with partitioning disks for imaged nodes
    until the real partitioning code can be used."""

    def __init__(self):
        self.firstdisk = ""
        self.root_device = ""
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
        '''Stores the partition information as a dict in the partinfo dict'''
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
        '''Deletes all partitions'''
        try:
            fp = file('/tmp/part0', 'w')
            fp.write(';\n;\n;\n;\n')
            fp.close()
        except:
            print "Unable to partition disk!"
            return
            
        os.system('sfdisk /dev/%s < /tmp/part0 >/dev/null 2>/dev/null' % (self.firstdisk))

    def partitionDisk(self):
        '''Creates the partitions'''
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

    def executeAndLog(self, cmd=''):
        """Executes the given cmd using os.system and logging its
           output to IMAGEINIT_LOGFILE."""
        os.system('%s >> %s 2>&1' % (cmd, IMAGEINIT_LOGFILE))

    def formatPart(self):
        '''Formats the partitions on the disk, and use swap'''
        for i in self.partinfo.keys():
            device = "/dev/%s%s" % (self.firstdisk, i)
            type = self.partinfo[i]['type']
            print "Formatting %s as %s" % (device, type)
            if type == 'linux-swap':
                self.executeAndLog('mkswap %s' % device)
                self.executeAndLog('swapon %s' % device)
            elif type == 'ext2':
                self.executeAndLog('mke2fs -q %s' % device)
            elif type == 'ext3':
                self.executeAndLog('mke2fs -j -q %s' % device)
            else:
                print "Unknown partition type: %s" % type

    def mountParts(self):
        '''Mounts the partitions.'''
        # Find root key first
        rkey = ''
        for i in self.partinfo.keys():
            if self.partinfo[i]['mntpnt'] == '/':
                rkey = i

        if rkey == '':
            print "ERROR:  No root partition defined!"
            sys.exit(-7)
            
        print "Mounting %s as root" % self.partinfo[rkey]['device']
        self.executeAndLog('mount %s /newroot/' % self.partinfo[rkey]['device'])

        # Now mount the other filesystems
        for i in self.partinfo.keys():
            if i == rkey:
                continue
            if self.partinfo[i]['type'] == 'linux-swap':
                continue
            os.makedirs('/newroot%s' % self.partinfo[i]['mntpnt'], mode=0755)
            print "Mounting %s to /newroot%s" % (self.partinfo[i]['device'], 
                                                 self.partinfo[i]['mntpnt'])
            self.executeAndLog('mount %s /newroot%s' % \
                    (self.partinfo[i]['device'], self.partinfo[i]['mntpnt']))

    def unmountParts(self):
        '''Unmounts the partitions.'''

        # Flush file system buffers first before unmounting partitions
        os.system('sync')

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
            self.executeAndLog('umount /newroot%s' % (self.partinfo[i]['mntpnt']))

        self.executeAndLog('umount /newroot%s' % (self.partinfo[i]['mntpnt']))
                
    def addGrub(self):
        '''Installs the grub bootloader'''
        flist = glob.glob('/newroot/boot/initrd*')
        if len(flist) == 0:
            print "ERROR:  Unable to locate the initrd!  Was the kernel package included?"
            sys.exit(-2)
        if os.path.islink(flist[0]):
            initrd = os.path.realpath(flist[0])
            initrd = os.path.basename(initrd)
        else:
            initrd = os.path.basename(flist[0])
        kver = ''
        kern = ''
        if initrd.startswith('initrd-'):
            kver = initrd[len('initrd-'):]
            if os.path.exists('/newroot/boot/vmlinuz-%s' % kver):
               kern = 'vmlinuz-%s' % kver

        if not kern:
            flist = glob.glob('/newroot/boot/vmlinuz-*')
            if len(flist) == 0:
                print "ERROR:  Unable to locate the kernel for imaged nodes!"
                sys.exit(-3)
            kern = os.path.basename(flist[0])
            kver = kern[len('vmlinuz-'):]
            initrd = 'initrd-%s' % kver

        if not (os.path.exists('/newroot/usr/sbin/grub') or os.path.exists('/newroot/sbin/grub')):
            print "ERROR:  Unable to locate the grub package!  Was the grub package included?"
            sys.exit(-4)

        # Find root dev, and bootable dev
        rkey = 0
        bdev = 0
        for i in self.partinfo.keys():
            if self.partinfo[i]['mntpnt'] == '/':
                rkey = i
            if self.partinfo[i]['boot'] == '*':
                bdev = string.atoi(i) - 1

        os.system('cp -r /newroot/usr/share/grub/*/* /newroot/boot/grub > /dev/null 2>&1')
        os.system('cp -r /newroot/usr/lib/grub/* /newroot/boot/grub > /dev/null 2>&1')
        # make /dev/ available for grub
        os.system('mount -o bind /dev /newroot/dev')
        fp = file('/newroot/boot/grub/grub.conf', 'w')
        fp.write('# Imaged node \n')
        fp.write('# \n')
        fp.write('default=0\n')
        fp.write('timeout=2\n')
        fp.write('\n')
        fp.write('title Imaged Node\n')
        fp.write('        root (hd0,%s)\n' % bdev)
        fp.write('        kernel /%s ro root=%s\n' % (kern, self.partinfo[rkey]['device']))
        fp.write('        initrd /%s\n' % (initrd))
        fp.close()
        os.chdir('/newroot/boot/grub')
        os.system('ln -s grub.conf menu.lst')
        os.chdir('/')
        return kver

    def configBootloader(self):
        if os.path.exists('/newroot/etc/SuSE-release'):
            if not os.path.exists('/newroot/var/log/YaST2'):
                os.makedirs('/newroot/var/log/YaST2', mode=0700)

            fp = file('/newroot/etc/grub.conf', 'w')
            fp.write('setup --stage2=/boot/grub/stage2 (hd0) (hd0,0)\n')
            fp.write('quit\n')
            fp.close()

            fp = file('/newroot/etc/sysconfig/bootloader', 'w')
            fp.write('LOADER_TYPE=\"grub\"\n')
            fp.close()
        else:
            fp = file('/newroot/etc/sysconfig/kernel', 'w')
            fp.write('# UPDATEDEFAULT specifies if new-kernel-pkg should make\n'
                     '# new kernels the default\n')
            fp.write('UPDATEDEFAULT=yes\n')
            fp.write('\n')
            fp.write('# DEFAULTKERNEL specifies the default kernel package type\n')
            fp.write('DEFAULTKERNEL=kernel\n')
            fp.close()

    def mkfstab(self):
        '''Writes the fstab file'''
        filename = "/newroot/etc/fstab"
        fp = file(filename, 'w')
        fp.writelines('# Created by Kusu Image installation\n')
        for i in self.partinfo.keys():
            if self.partinfo[i]['mntpnt'] != '/':
                continue
            self.root_device = "/dev/%s%s" % (self.firstdisk, i)
            fp.writelines('%s          /       %s     defaults        1 1\n' % \
                    (self.root_device, self.partinfo[i]['type']))

        fp.writelines('devpts                  /dev/pts                devpts  gid=5,mode=620  0 0\n')
        fp.writelines('proc                    /proc                   proc    defaults        0 0\n')

        if os.path.exists('/newroot/etc/SuSE-release'):
            fp.writelines('sysfs                   /sys                    sysfs   noauto        0 0\n')   
            fp.writelines('debugfs                 /sys/kernel/debug       debugfs noauto        0 0\n')   
        else:
            fp.writelines('sysfs                   /sys                    sysfs   defaults        0 0\n')   
            fp.writelines('tmpfs                   /dev/shm                tmpfs   defaults        0 0\n')

        for i in self.partinfo.keys():
            if self.partinfo[i]['mntpnt'] == '/':
                continue
            device = "/dev/%s%s" % (self.firstdisk, i)
            type = self.partinfo[i]['type']
            if type == 'linux-swap':
                fp.writelines('%s          swap       swap     defaults      0 0\n' % device)
                continue
            # FIX THIS:  Mounting may require ordering
            fp.writelines('%s         %s         %s     defaults   1 2\n' % (device, self.partinfo[i]['mntpnt'], type))
                
        fp.close()


class ImagedConfigFiles:
    """ This class will deal with all the files that need to be created
    on imaged nodes."""

    def __init__(self, niihandler=None, bestip=''):
        self.root = '/newroot'
        self.niihandler = niihandler
        self.bestip = bestip

    def getPhysicalAddressOfInterface(self, interface):
        """ Returns the MAC address of the given interface."""
        sys.path.append("/opt/primitive/lib/python2.4/site-packages")
        from primitive.system.hardware import probe
        from primitive.system.hardware.net import arrangeOnBoardNicsFirst
        interfaces = arrangeOnBoardNicsFirst(probe.getPhysicalInterfaces())
        return interfaces[interface]['hwaddr']

    def getIfcfgFilename(self, interface):
        dir = "%s/etc/sysconfig/network-scripts/" % self.root
        if not os.path.exists(dir):
            dir = "%s/etc/sysconfig/network/" % self.root
        filename = "%sifcfg-%s" % (dir, interface)
        if os.path.exists('%s/etc/SuSE-release' % self.root) and interface.startswith('eth'):
            filename = "%sifcfg-eth-id-%s" % (dir, self.getPhysicalAddressOfInterface(interface))
        return filename

    def mkifcfgs(self, hostname, data):
        """Writes the ifcfg-XXX files."""
        for i in data.keys():
            interface = data[i]['device']
            fp = file(self.getIfcfgFilename(interface), 'w')
            fp.writelines('# NIC configured by Kusu\n')
            if os.path.exists('%s/etc/SuSE-release' % self.root):
                fp.writelines('STARTMODE=auto\n')
            else:
                fp.writelines('ONBOOT=yes\n')
                fp.writelines('DEVICE=%s\n' % interface)
            if data[i]['dhcp'] == '0':
                fp.writelines('BOOTPROTO=static\n')
                fp.writelines('IPADDR=%s\n' % data[i]['ip'])
                fp.writelines('NETMASK=%s\n' % data[i]['subnet'])
                fp.writelines('NETWORK=%s\n' % data[i]['network'])
            else:
                fp.writelines('BOOTPROTO=dhcp\n')
                fp.writelines('# IPADDR=%s\n' % data[i]['ip'])
                fp.writelines('# NETMASK=%s\n' % data[i]['subnet'])
                fp.writelines('# NETWORK=%s\n' % data[i]['network'])
                fp.writelines('# dhcp=%s\n' % data[i]['dhcp'])
            fp.close()

    def get_sles_module_list(self):
        if not os.path.exists('/var/log/YaST2'):
            os.makedirs('/var/log/YaST2', mode=0700)
        import ycp
        controllers = ycp.SCR.Read(ycp.Path('.probe.storage'))
        sles_module_list = []
        for controller in controllers:
            if controller.has_key('drivers'):
                for drivers in controller['drivers']:
                    for module in drivers['modules']:
                        sles_module_list.append(module[0])
            elif controller.has_key('driver'):
                sles_module_list.append(controller['driver'])

        return ' '.join(set(sles_module_list))

    def generate_sles_configuration_script(self):
        fp = file(SLES_CONFIGURATION_SCRIPT, 'w')
        fp.writelines('#!/bin/sh\n')
        fp.writelines('for svc in boot.localnet boot.klog haldaemon network syslog portmap nfs; do\n')
        fp.writelines('    chkconfig --add $svc\n')
        fp.writelines('done\n')
        fp.writelines('SuSEconfig --module permissions > /dev/null 2>&1\n')
        fp.writelines('echo y | zypper service-delete TEMPORARY 2>&1 > /dev/null\n')
        repo_url = "http://%s%s" % (self.bestip, self.niihandler.repo)
        fp.writelines('echo y | zypper service-add %s %s\n' % (repo_url, self.niihandler.ostype))
        fp.close()
        os.system('chmod 755 %s' % SLES_CONFIGURATION_SCRIPT)
        os.system('cat %s' % SLES_CONFIGURATION_SCRIPT)

    def rebuildInitrd(self, kver):
        '''Rebuilds the initrd so this thing can boot. This is VERY linux centric.'''

        if os.path.exists('/newroot/etc/SuSE-release'):
            # For sles, should add module list to /etc/sysconfig/kernel for 'mkinitrd'
            sles_module_list = self.get_sles_module_list()
            fp = file('/newroot/etc/sysconfig/kernel', 'r')
            contents = fp.readlines()
            fp.close()
            fp = file('/newroot/etc/sysconfig/kernel', 'w')
            for line in contents:
                if line.strip().startswith('INITRD_MODULES='):
                    fp.write('INITRD_MODULES="%s"\n' % sles_module_list)
                else:
                    fp.write(line)
            fp.close()

        # Create a script to run in a chroot'ed environment to build the initrd
        filename = "/newroot/SetupInitrd"
        fp = file(filename, 'w')
        fp.writelines('#!/bin/sh\n')
        fp.writelines('mount /sys\n')
        fp.writelines('mount /proc\n')
        fp.writelines('cd /boot\n')
        fp.writelines('if [ -f "/etc/SuSE-release" ]; then\n')
        fp.writelines('    ./%s\n' % os.path.basename(SLES_CONFIGURATION_SCRIPT))
        fp.writelines('    ln -s /proc/self/fd /dev/fd\n')
        fp.writelines('    mkinitrd -k /boot/vmlinuz-%s -i /boot/initrd-%s\n' % (kver, kver))
        fp.writelines('else\n')
        fp.writelines('    mv initrd-%s.img initrd-%s.ORIG.img\n' % (kver, kver))
        fp.writelines('    mkinitrd /boot/initrd-%s.img %s\n' % (kver, kver))
        fp.writelines('fi\n')
        fp.writelines('cat <<EOF >/tmp/grub.cmd\n')
        fp.writelines('root (hd0,0)\n')
        fp.writelines('setup (hd0)\n')
        fp.writelines('EOF\n')
        fp.writelines('grub --batch --no-floppy --no-curses < /tmp/grub.cmd\n')
        fp.writelines('umount /sys\n')
        fp.writelines('umount /proc\n')
        fp.writelines('exit')
        fp.close()
        os.system('chmod 755 %s' % filename)
        os.system('cat %s' % filename)
        os.system('chroot /newroot /SetupInitrd')
        os.chdir('/')


if __name__ == '__main__':
    app = NodeConfigurator()
    app.loadModules()
    app.upInterfaces()

    bestip = app.findBestInstaller()
    app.log("Best Installer = %s\n" % bestip)

    uid = app.genUID()
    app.log("UID = %s\n" % uid)

    niiinfo = NIIFun()
    niiinfo.setState('Installing')
    niiinfo.setUID(uid)
    niiinfo.wantNII(1)
    #niiinfo.wantCFM(1)  # Can't do anything with it yet

    while True:
        try:
            niifile = niiinfo.callNodeboot(bestip)
            break
        except:
            app.log("ERROR:  Unable to get NII from:  %s\n" % bestip)
            print "ERROR:  Unable to get NII from:  %s\nWill retry in 30 seconds.\n" % bestip
            time.sleep(30)
        
    niihandler = NodeInstInfoHandler()
    try:
        parser = make_parser()
    except:
        app.log("ERROR:  Unable to initialize xml parser.  Make sure initrd has Expat\n")
        print "ERROR:  Unable to initialize xml parser.  Make sure initrd has Expat\n"
        sys.exit(-1)
        
    parser.setContentHandler(niihandler)
    parser.parse(open(niifile)) 

    if len(niihandler.partitions.keys()) > 0 and niihandler.installtype == 'disked':
        disked = True
        app.log("Using local disk\n")
    else:
        disked = False
        app.log("Not using local disk\n")

    app.logNiiInformation(niihandler=niihandler)
    app.configureNiiInterfaces()

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
    app.setupSystem(niihandler, bestip)

    os.system('hostname %s' % niihandler.name)

    icf = ImagedConfigFiles(niihandler=niihandler, bestip=bestip)
    nicdata = {}
    for i in niihandler.nics.keys():
        if  niihandler.nics[i]['device'] in ['bmc']: continue 

        nicdata[i] = { 'device'  : niihandler.nics[i]['device'],
                       'ip'      : niihandler.nics[i]['ip'],
                       'subnet'  : niihandler.nics[i]['subnet'],
                       'network' : niihandler.nics[i]['network'],
                       'suffix'  : niihandler.nics[i]['suffix'],
                       'gateway' : niihandler.nics[i]['gateway'],
                       'dhcp'    : niihandler.nics[i]['dhcp'],
                       'options' : niihandler.nics[i]['options'],
                       'boot'    : niihandler.nics[i]['boot'] }
            
    if os.path.exists('/newroot/etc/SuSE-release'):
        icf.generate_sles_configuration_script()

    if disked or (not disked and os.path.exists('/newroot/etc/SuSE-release')):
        # Imaged nodes need ifcfg files to be generated.
        # SLES diskless nodes also need the ifcfg files otherwise when
        # the name_eths scripts execute, the network service will be
        # stopped since it could not find any ifcfg files.
        # RHEL diskless nodes do not restart the network service in
        # their name_eths scripts.
        print "Writing network config files"
        icf.mkifcfgs(niihandler.name, nicdata)

    if disked:
        # Install the bootloader
        print "Adding bootloader"
        kversion = dlp.addGrub()
        dlp.configBootloader()

        print "Adding Fstab"
        dlp.mkfstab()
        
        print "Installing initrd"
        icf.rebuildInitrd(kversion)

        if os.path.exists(IMAGEINIT_LOGFILE):
            os.system('mv %s /newroot/root/imageinit.log' % IMAGEINIT_LOGFILE)

        dlp.unmountParts()

        print "Changing boot device"
        niiinfo.setState('Installed')
        niiinfo.wantNII(0)
        niiinfo.setBootFrom('disk')  # This is only for disked!

        while True:
            try:
                niifile = niiinfo.callNodeboot(bestip)
                break
            except:
                app.log("ERROR:  Unable to update bootfrom:  %s\n" % bestip)
                print "ERROR:  Unable to update bootfrom:  %s\nWill retry in 30 seconds.\n" % bestip
                time.sleep(30)
                
        # Exit with 99 to force reboot
        sys.exit(99)

    # diskless systems have errors on reboot/shutdown due
    # to the S01reboot script crashing the system.
    # This section is a workaround hack that inserts
    # rc scripts to run before the S01reboot scripts
    # in runlevels 0(shutdown) and 6(reboot).
    if not disked:
        # shutdown in runlevel 0.
        f = open('/newroot/etc/rc.d/rc0.d/S00killpcm', 'w')
        f.write('#!/bin/bash\n')
        f.write('echo 1 > /proc/sys/kernel/sysrq\n')
        f.write('echo o > /proc/sysrq-trigger\n')
        f.close()
        os.system('chmod 755 /newroot/etc/rc.d/rc0.d/S00killpcm')
        # reboot in runlevel 6.
        f = open('/newroot/etc/rc.d/rc6.d/S00killpcm', 'w')
        f.write('#!/bin/bash\n')
        f.write('echo 1 > /proc/sys/kernel/sysrq\n')
        f.write('echo b > /proc/sysrq-trigger\n')
        f.close()
        os.system('chmod 755 /newroot/etc/rc.d/rc6.d/S00killpcm')

    app.log("INFO: Exiting imageinit with:  %i" % initrddebug)
    if initrddebug == 1:
        # Exit with 1 to stop the switch_root
        sys.exit(1)

    sys.exit(0)
