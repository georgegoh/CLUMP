#!/usr/bin/python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
import re
import StringIO
import struct
import tempfile
import urlparse
from optparse import OptionParser
try:
    import subprocess
except:
    from popen5 import subprocess
import primitive.support.log as primitivelog

ul = primitivelog.getPrimitiveLog()
ul.addFileHandler()
import xml.sax
from xml.sax import make_parser
from path import path 

import primitive.system.hardware.probe
from primitive.support import compat


from primitive.nodeinstall.errors import *
import primitive.imagetool.commands
from primitive.core.command import CommandFailException

from primitive.nodeinstall.nodeinstall import NodeInstaller
from primitive.system.hardware.nodes import checkAndMakeNode
from primitive.system.hardware.errors import MountFailedError
from primitive.system.hardware import DiskProfile
from primitive.system.hardware.grub import generateDeviceMapEntries
from primitive.system.hardware.disk_utils import isDiskOrderAmbiguous
from primitive.system.hardware.disk_utils import remarkMBRs
from primitive.fetchtool.commands import FetchCommand
from primitive.core.errors import ApplicationException
from primitive.core.errors import ModuleException
from primitive.nodeinstall.nodeinstall import KickstartFromNIIProfile
from primitive.nodeinstall.niifun import NodeInstInfoHandler
from primitive.imagetool.commands import RetrieveNIICommand
import primitive.support.util


from primitive.configtool.commands import ConfigCommand
from primitive.configtool.plugins import BasePlugin
from primitive.system.hardware import net
try:
    import subprocess
except:
    from popen5 import subprocess

class ImageTool(object):
    
    def __init__(self):

        self.actions = {'provision':['niihost'], 
            'get-nii':['niihost','node']}
        
        self.nodeinst = NodeInstaller()
        self.parser = OptionParser("Imagetool Help")
        self.diskprofile = None
        # self.action and self.actionargs will hold the current action and its arguments            
        self.action = None 
        self.actionargs = None
        self.diskprofile = None
        self.PRIMITIVE_ROOT='/mnt/primitive'
        self.imageinfo_uri = '' # uri we got imageinfo from , all files in imageinfo relative to this
        self.imageinfo_dict = None # dictionary storing image information
        self.ordered_mountpoints = []
        self.usagestr = """\
nodeinstaller <action> arg1=val1 arg2=val2 ...

nodeinstaller is the automated version of the Kusu Installer. This
application is not meant to be run as a standalone application.

When run with no actions, nodeinstaller will attempt to automatically
run in provisioning mode.


actions:

    provision   - Starts the automatic installer for provisioning a node. 
                  Available arguments for this action:
                    niihost=<NII Server Address>
                                        
    get-nii     - Prints the Node Installation Information for a node to 
                  standard output. Available arguments for this action:
                    niihost=<NII Server Address>
                    node=<Name or IP Address of a Node>

"""
        self.parser.set_usage(self.usagestr)

    def printUsageExit(self):
        """ Print usage text and exit. """
        sys.stdout.write(self.usagestr)
        sys.stdout.write(os.linesep)
        sys.exit(0)

    def printMsgExit(self, msg):
        """ Print msg and exit. """
        sys.stdout.write(msg)
        sys.stdout.write(os.linesep)
        sys.exit(1)

    def handleArgPairs(self, arglist):
        """ Handle the argument list and return a dict of key-value pairs. """

        li = []
        d = {}

        for s in arglist:
            li2 = s.split('=')
            for s2 in li2: 
                if s2: li.append(s2)        

        # There should be even number of items in order to make pairs
        if not len(li) % 2: 
            # Collect the pairs
            while li:
                d[li[0].lower()] = li[1]
                del li[0:2]

        return d
    def parseargs(self):
        """ App-specific arguments goes here. """

        self.options, self.args = self.parser.parse_args()

        if not self.args :
            # run in provision mode
            ul.debug('Running in automatic provision mode')
            self.args.append('provision')
            
            # grab the /proc/cmdline and look for niihost
            cmdline = open('/proc/cmdline').read()
            cmdlist = cmdline.strip('\n').split()
            for l in cmdlist:
                if l.startswith('niihost='):
                    self.args.append(l)

        # check if the first parsed argument is a supported action
        action = self.args[0]

        if action not in self.actions.keys():
            self.printUsageExit()
        d = self.handleArgPairs(self.args[1:])

        if not d:
            self.printUsageExit()

        # iterate keys in d and validate against the commands'
        # list of keys
        for k in d.keys():
            if k not in self.actions[action]:
                self.printUsageExit()

        self.action = action
        self.actionargs = d
     
    def run(self):
        """ Main launcher. """
        ul.debug('Starting nodeinstaller')
        
        self.parseargs()
        
        # call the correct sub-handler for the action
        m = '_' + self.action.split('-')[0] \
            + ''.join([l.capitalize() for l in self.action.split('-')[1:]])
            
        handler = getattr(self,m)
        
        handler(self.actionargs)
        ul.debug('Finishing launcher')
    
        sys.exit(0)
    def disambiguateDiskOrder(self, disk_profile, interactive=False, fix=True):
        """
        If there are disks which share the same MBR signature, disambiguate
        them by rewriting the duplicate signatures with unique ones.
        System needs to be rebooted for the kernel EDD code to read the MBR
        signatures by BIOS order.
        """
        disk_order = disk_profile.getBIOSDiskOrder() #can return empty
        if disk_order:
            disk0 = disk_profile.disk_dict[disk_order[0]]
        else:
            keys = disk_profile.disk_dict.keys()
            keys.sort()
            first_disk = keys[0]
            disk0 = disk_profile.disk_dict[first_disk]
        disk0_mbrsig = disk0.mbr_signature

        duplicates = []
        for k in disk_order[1:]:
            d = disk_profile.disk_dict[k]
            if d.mbr_signature == disk0.mbr_signature:
                duplicates.append(k)

        if not duplicates:
            return disk_order

        if interactive:
            if fix:
                msg = 'The Kusu installer cannot automatically determine the first '
                msg += 'disk that this system boots from due to duplicate MBR '
                msg += 'signatures on some disks.\n\n'
                msg += 'To proceed, Kusu needs to make changes to the MBR signature '
                msg += 'of the affected disks and reboot. On reboot, Kusu will then '
                msg += 'be able to determine which disk the system boots from.\n\n'
                msg += 'Please click "OK" to proceed, or power off now to stop the '
                msg += 'installation'
#                self.selector.popupMsg('Cannot determine the first disk', msg,60)
                remarkMBRs(disk_profile)
                subprocess.call(['reboot'])
            else:
                msg = 'The Kusu installer cannot automatically determine the first '
                msg += 'disk that this system boots from due to duplicate MBR '
                msg += 'signatures on some disks.\n\n'
                msg += 'Please refer to the installation guide for more information.'
 #               self.selector.popupDialogBox('Cannot determine the first disk', msg, ['Reboot'])
                subprocess.call(['reboot'])

        # else not interactive
        if fix:
            remarkMBRs(disk_profile)
        subprocess.call(["reboot"])
    def orderMountpoints(self,mntlist):
        ''' This function takes a list of mountpoints and returns a similar list
        of ordered mountpoints'''
        # The goal of this function is to ensure that the mount point tree is correclty
        #ordered. To do this, the first mountpoint must be '/'.
        # Verify no relative mountpoints exist.
        retlist = []
        for m in mntlist:
            if not m.startswith('/'):
                raise ApplicationException,"Relative mountpounts unsupported!"
        
        # construct new list
        # the insertion algorithm is an O(n^2) algorithm as we do not implement a
        # tree structure to hold this info - for the future
        # we compare every item to be inserted with items already in the list.
        # if the old item starts with new item's name, then we know that the item we
        # are inserting is the parent of an item in the list
        # we then immediately insert it prior to the item.
        # if not we continue iteration and insert at the end.

        inserted = False
        for m in mntlist:
            if not retlist:
                retlist.append(m)
                continue
            for r in retlist:
                if r.startswith(m):
                    retlist.insert(retlist.index(r),m)
                    inserted = True
                    break
            if not inserted:
                retlist.append(m) # append to the end.
            else:
                inserted = False #reset loop
        return retlist
                
    def unmountMntPts(self):
        # unmount pseudo partitions first

        try:
            cmd = ''.join(['umount ', path(self.PRIMITIVE_ROOT) / 'proc'])
            primitive.support.util.runCommand(cmd)
            cmd = ''.join(['umount ', path(self.PRIMITIVE_ROOT) / 'dev'])
            primitive.support.util.runCommand(cmd)
        
            mntpts = self.ordered_mountpoints
            mntpts.reverse()
            for m in mntpts:
                cmd = ''.join(['umount ', self.PRIMITIVE_ROOT, m])
                primitive.support.util.runCommand(cmd)
        except ModuleException,e:
            raise ApplicationException,"Failed to unmount partition! %s " % e

            
    def mountMntPts(self,):
        prefix = path(self.PRIMITIVE_ROOT)

        d = self.diskprofile.mountpoint_dict
        mounted = []
        self.ordered_mountpoints = self.orderMountpoints(d.keys())
        if self.ordered_mountpoints[0] != '/':
            raise ApplicationException,"First mountpoint must be a '/'"
        # Mount and create in order
        for m in self.ordered_mountpoints:
            mntpnt = prefix + m
            if not mntpnt.exists():
                mntpnt.makedirs()
                ul.debug('Made %s dir' % mntpnt)
            
            # mountpoint has an associated partition,
            # and mount it at the mountpoint
            if d.has_key(m):
                try:
                    ul.debug('Try to mount %s' % m)
                    d[m].mount(mntpnt)
                    mounted.append(m)
                except MountFailedError, e:
                    raise MountFailedError, 'Unable to mount %s on %s' % (d[m].path, m)

        for m in ['/']:
            if m not in mounted:
                raise ApplicationException, 'Mountpoint: %s not defined' % m



    def performDiskSetup(self):
        ''' This function sets up the disks and partitioning up for the imaged install'''
        disks_dict = primitive.system.hardware.probe.getDisks()
        disks_str = disks_dict.keys()
        for d in disks_dict.values():
            disks_str += d['partitions']
        disks_str += primitive.system.hardware.probe.getCDROM().keys()

        for dev in disks_str:
            checkAndMakeNode('/dev/' + dev)

        # Disambiguate Disk order
        tmp_disk_profile = DiskProfile(True)
        disk_order = self.disambiguateDiskOrder(tmp_disk_profile)
        # set up nodeinstaller    
#        self.nodeinst.setup(self.ksfile, self.niihost, disk_order)
        self.ksprofile = KickstartFromNIIProfile()
        print self.nodeinst.partitions
        self.nodeinst.source = self.nii_cache
        self.nodeinst.parseNII()
        self.diskprofile = self.ksprofile.prepareKickstartDiskProfile(self.nodeinst, disk_order=disk_order)
        print self.diskprofile.mountpoint_dict
        ul.debug('Committing disk profile')
#        self.nodeinst.commit()
        self.diskprofile.commit()
        self.diskprofile.formatAll()
#        self.selector.popupMsg('Partitioning', 'Finished Partitioning disks.')
        ul.debug('Finished partitioning disks')

        if not self.diskprofile.disk_dict:
            msg = 'Kusu node installer cannot find any hard disks to install '
            msg += 'on. Please correct this and restart.'
            print('Rebooting due to lack of usable disks: %s' %  msg)
            sys.exit(-1)
            #subprocess.call(['reboot'])
        ul.debug('Mounting filesystem')


        self.mountMntPts()

    
    def extractImgInfo(self,nii):
        '''This function parses the NI:qI and return the image info dictionary'''
        parser = make_parser()
        nii_handler = NodeInstInfoHandler()
        parser.setContentHandler(nii_handler)
        parser.parse(nii)
        # set the imageinfo_uri for us to have a base address to obtain the tarballs later.
        self.imageinfo_uri = nii_handler.imageinfo
        print 'The handler is %s' %nii_handler.imageinfo
#        print nii_handler.nodeinfo
        try:
            dest_dir = tempfile.mkdtemp('imagetool')
            status,imginfo_path = FetchCommand(uri=self.imageinfo_uri,
                                               fetchdir=False,
                                               destdir=dest_dir,
                                               lockdir='/tmp',
                                               overwrite=True).execute()
        except CommandFailException,e:
            path(dest_dir).rmtree(ignore_errors=True) # clean up destdir
            raise CommandFailException,\
                'Failed obtaining file. %s' % e
        if not imginfo_path.exists() or not imginfo_path.isfile():
            path(dest_dir).rmtree(ignore_errors=True) #clean up destdir
            raise CommandFailException,'Failed opening template file'
        # we have fetched the file now we exec it
        try:
            try:
                exec_dict = {}
                execfile(imginfo_path,exec_dict)
                imginfo_dict = exec_dict['imginfo']
            finally:
                path(dest_dir).rmtree(ignore_errors=True) #clean up destdir
        except SyntaxError,e:
            raise ApplicationException,"Unable to parse image info :%s" % e
        except KeyError,e:
            raise ApplicationException,'Unable to obtain image info data from file :%s'% e
        return imginfo_dict

    def unpackImages(self,imginfo):
        ''' This function parses image info to download images or create empty directories'''
        if not imginfo['archives']:
            raise ApplicationException,"No archives found, incorrect image info format!"
        empty_dirs = []
        archives = {}
        # collapse all the archives into a single dictionary
        [ archives.update(d) for d in imginfo['archives']  ]

        for k,v in archives.items():
            if not v:
                if not k.endswith(".tgz"):
                    raise ApplicationException,\
                        "Tarballs provided do not end with .tgz,incorrect imginfo format"
                empty_dirs.append(k[:-4]) # strip ".tgz"
                archives.pop(k)
        #create empty dirs
        try:
            print empty_dirs
            for d in empty_dirs:
                dpath = path(self.PRIMITIVE_ROOT)  / d
                if not dpath.exists():
                    dpath.makedirs()
        except IOError,e:
            raise ApplicationException,"Failed creating root filesystem structure :%s"% e

        img_path = self.imageinfo_uri[:-len("imginfo")]
        for k in archives.keys():
            self.unpackTarball(''.join([img_path,k]))

    def unpackTarball(self,uri):
        cmd = ''.join(['wget -O - ', uri, ' | tar xvzf -',' -C ',
                       self.PRIMITIVE_ROOT ])
        primitive.support.util.runCommand(cmd)

    def _provision(self, args):
        """Handler for provision. args is a dict of supported key-value pairs for this action. """
        self.nii_uri = args.get('niihost',None)

#        ul.addSysLogHandler(host=niihost)
        if not self.nii_uri:
            self.nii_uri="http://192.168.1.1/sles_os/niidump.txt" #hardcode for now

   

        try:
            self.nii_host = urlparse.urlparse(self.nii_uri)[1] 
        except:
            self.nii_host = ''
        
        print "Running CLI Based Image installer"
        #1 Grab NII
        try:
            self.nii = RetrieveNIICommand(name = "ImageTool",logged=True, lockdir='/tmp',locked=True, uri=self.nii_uri).execute()
        except CommandFailException,e:
            print e
            sys.exit(-1)
        # parse the information for the node info

        try:
            f = open('/tmp/nii','w')
            f.write(self.nii.read())
            f.close()
        except OSError:
            raise ApplicationException,"Failed to write NII"
        self.nii_cache = '/tmp/nii'
        self.imageinfo_dict = self.extractImgInfo(self.nii_cache)
        #2 Check Disks
        ul.debug('Checking Disks')
        dp = self.performDiskSetup()
        #3 Unpack Images
        self.unpackImages(self.imageinfo_dict)
        #4 Write fstab configuration and other final actions
#        self.finalActions(self.imageinfo_dict)
        #5 Install grub
        self.grubInstall()
        #6 update sysconfig 
        self.updateSysConfig()
        #7 use configtool to pick up config and write it
        self.commitFstab()
        print 'Creating network scripts'
        self.commitNetworks()
        self.mountPseudoFS()
        self.makeInitrd()
        ul.debug('Creating network scripts')
        self.disableRootPw() #interim before cfm
 
        self.unmountMntPts()
    def disableRootPw(self):
        ''' This allows blank passwords to be used ''' 
        f = open(path(self.PRIMITIVE_ROOT) / 'etc/pam.d/common-auth')
        f_lines = f.readlines()
        f.close()
        for l in f_lines:
            if l.startswith('auth') and l.split()[2] == 'pam_unix2.so':
                f_lines.remove(l)
                replace_list = l.split()
                replace_list.append('nullok\n')
                break
        # replace password
        replace_line = '  '.join(replace_list)
        f_lines.append(replace_line)
        f = open(path(self.PRIMITIVE_ROOT) / 'etc/pam.d/common-auth','w')
        f.writelines(f_lines)
        f.close()
        
            
                  
    def commitNetworks(self):
        ''' Commit the network profile'''
        self.ksprofile.prepareKickstartNetworkProfile(self.nodeinst, self.nii_uri)
        networks = self.ksprofile.networkprofile
        print networks
        #  obtain the if template and parse its args.
        img_path = self.imageinfo_uri[:-len("imginfo")]
        if 'if_template' not in self.imageinfo_dict.keys():
            raise ApplicationException, "Unable to load Interface template"
        else:
            if_template = ''.join([img_path,self.imageinfo_dict['if_template']])

        if 'routes_template' not in self.imageinfo_dict.keys():
            raise ApplicationException, "Unable to load routes template"
        else:
            routes_template = ''.join([img_path,self.imageinfo_dict['routes_template']])

        if 'resolv_template' not in self.imageinfo_dict.keys():
            raise ApplicationException, "Unable to load resolv template"
        else:
            resolv_template = ''.join([img_path,self.imageinfo_dict['resolv_template']])

        for intf, v in networks['interfaces'].items():
           args = {}
           n = net.Net(intf)

           ip =  v['ip_address']
           netmask =  v['netmask']
           onboot = v['active_on_boot'] 

           if onboot:
               args['onboot'] = 'yes'
               args['startmode'] = 'auto'
           else:    
               args['onboot'] = 'no'
            
               args['startmode'] = 'off'
           if v['use_dhcp']:
               args['bootproto'] = 'dhcp'
           else:
               args['bootproto'] = 'static'
               args['ip'] = ip
               args['netmask'] = netmask
           aux_dict = {'lockdir':'/tmp', 'locked' : True}
           out = self.simpleConfigPlugin(if_template, aux_dict ,args)
           f = open(path(self.PRIMITIVE_ROOT) / 'etc' / 'sysconfig' / 'network' / 'ifcfg-eth-id-%s' % n.mac, 'w')
           f.write(out)
           f.close()

#        do /etc/sysconfig/route
        if not networks['gw_dns_use_dhcp']: # manual gw and dns
           if networks.has_key('default_gw') and networks['default_gw']:
               gw = networks['default_gw']
               out = self.simpleConfigPlugin(routes_template,aux_dict, {'gw': gw}  )
               f = open(path(self.PRIMITIVE_ROOT) / 'etc' / 'sysconfig' / 'route', 'w')
               f.write(out)
               f.close()
        
        if not networks['fqhn_use_dhcp'] \
           and networks.has_key('fqhn_host') and networks['fqhn_host']:
               hostname = networks['fqhn_host']
               f = open(path(self.PRIMITIVE_ROOT) / 'etc' / 'HOSTNAME', 'w')
               f.write("%s\n" % hostname)
               f.close()

#        do /etc/resolv.conf
        domains = ''
        dns = [networks[key] for key in ['dns1', 'dns2', 'dns3'] \
                   if networks.has_key(key) and networks[key]]
        for i in xrange(len(dns)):
            if dns[i].startswith("http:"):
                dns[i] = urlparse.urlsplit(dns[i])[1]

        args = {'domains' : '', 'nameservers': dns}
        out = self.simpleConfigPlugin(resolv_template,aux_dict, args)
        f = open(path(self.PRIMITIVE_ROOT) / 'etc' / 'resolv.conf', 'w')
        f.write(out)
        f.close()
        

        # Images unpacked and empty dirs created at this point.
#         node_info 
#         nodeinst = NodeInstaller(nii)
        #3 Mount Primitive partitions

    def commitFstab(self):
        ''' This command configures Fstab'''
        img_path = self.imageinfo_uri[:-len("imginfo")]
        print img_path
        if 'fstab_template' not in self.imageinfo_dict.keys():
            raise ApplicationException, "Unable to load FStab template"
        else:
            fstab_uri = ''.join([img_path,self.imageinfo_dict['fstab_template']])
        entry_list = []
        # grab the partitions mounted at primitive root, remove primitive root and send it to fstab
        # cant go wrong with that
        # grab all the partitions.
        partitions_dict = {}
        [partitions_dict.update(d.partition_dict) for d in self.diskprofile.disk_dict.values()]
        for k, v in partitions_dict.iteritems():
            partition = ''.join([v.disk.path,str(k)])
            if v.swap_flag:
                mount_point = 'swap'
            else:
                mount_point = v.mountpoint
            fs_type = v.fs_type
            if  mount_point:
                entry_list.append(''.join([partition,'  ',mount_point, '  ',fs_type, '  defaults 0 0 ']))
#        entry_list  =  [ m for m in mtab_list if m.split()[1].startswith(self.PRIMITIVE_ROOT)]
        #prune /mnt/primitive from this
        
        

#         entry_list.append('/dev/sda2            /                    reiserfs   acl,user_xattr        1 1')
#         entry_list.append('/dev/sda1            swap                    reiserfs   acl,user_xattr        1 1')
        print entry_list
        template_args = { 'comment' : '#Default filled by imaged install',
                          'entries' : entry_list}
        print fstab_uri
        configtool_inputs = { 'name' : 'Fstab Config',
                              'template' :fstab_uri, # direct from imageinfo
                              'plugin' : FstabConfigPlugin,
                              'plugin_args': template_args,
                              'lockdir' : '/tmp', # required for inner fetchtool
                              'locked' : True
                              }
        try:
            fstab_str = ConfigCommand(**configtool_inputs).execute()
        except CommandFailException,e:
            raise ApplicationException ,"Failed obtaining Fstab"
        try:
            f = open(path(self.PRIMITIVE_ROOT) / 'etc/fstab','w')
            f.write(fstab_str)
            f.close()
        except IOError,e :
            raise ApplicationException,"Failed writing fstab"
            

    def grubInstall(self):
        ''' Install grub into the system'''
        ul.debug('Installing grub')
        print 'Installing GRUB'

        dp = self.diskprofile # DiskProfile(True)
        dme = generateDeviceMapEntries(dp)
        device_map = (path(self.PRIMITIVE_ROOT)/'boot'/'grub'/'device.map').open('w')
        device_map.writelines([x+'\n' for x in dme])
        device_map.close()
        first_disk_path = '/dev/' + dp.getBIOSDiskOrder()[0]
        primitive.support.util.runCommand('grub-install --root-directory=%s %s' % \
                                        (self.PRIMITIVE_ROOT, first_disk_path))
        try:
            fc = FetchCommand(uri='file:///menu.lst',
                              fetchdir=False,
                              destdir=path(self.PRIMITIVE_ROOT)/'boot'/'grub',
                              overwrite=True,
                              lockdir='/tmp')
            fc.execute()
        except CommandFailException,e:
            raise ApplicationException,"Failed to install menu.lst %s" % e

    def updateSysConfig(self):
        ''' Update sysconfig ''' 
        # modify sysconfig kernel.
        sysconfig_kernel_path = path(self.PRIMITIVE_ROOT)/'etc'/'sysconfig'/'kernel' 
        ul.debug('Modifying %s' % sysconfig_kernel_path)
        print 'Modifying %s' % sysconfig_kernel_path
        initrd_modules=['ide_core', 'scsi_mod', 'sd_mod', 'st', 'sr_mod',
                        'ahci', 'sg', 'scsi_transport_spi', 'mptbase',
                        'mptscsih', 'mptspi']
        cmd = ' '.join(['sed', '-i',
                        """'s/^INITRD_MODULES=.*/INITRD_MODULES="%s"/g' %s""" % \
                        (' '.join(initrd_modules), sysconfig_kernel_path)])
        primitive.support.util.runCommand(cmd)


    def mountPseudoFS(self):
        # mount proc and dev filesystems
        ul.debug('Mounting the procfs and devfs filesystems.')
        print 'Mounting the procfs and devfs filesystems.'
        primitive.support.util.runCommand('mount -t proc none %s/proc' % \
                                        self.PRIMITIVE_ROOT)
        primitive.support.util.runCommand('mount -o bind /dev %s/dev' % \
                                        self.PRIMITIVE_ROOT)
    def makeInitrd(self):
        # create initrd
        ul.debug('Creating initrd.')
        print 'Creating initrd.'
        # XXX: HARDCODED VALUES: vmlinuz, initrd versions.
        root_path = '/dev/sda3'
        if self.diskprofile and self.diskprofile.mountpoint_dict.has_key('/'):
            root_path = self.diskprofile.mountpoint_dict['/'].path

        # Get the vmlinuz version
        vmlinuz = 'vmlinuz'
        for f in (path(self.PRIMITIVE_ROOT)/'boot').files():
            name = f.basename()
            if name.startswith(vmlinuz):
                version = name[len(vmlinuz):]

        cmd = ['chroot', self.PRIMITIVE_ROOT, '/sbin/mkinitrd', '-k',
               '/boot/vmlinuz%s' % version, '-i',
               '/boot/initrd%s' % version, '-d',
               root_path]
        primitive.support.util.runCommand(' '.join(cmd))

        
            
    def simpleConfigPlugin(self,template,aux_args,args):
        class SimplePlugin(BasePlugin):
            ''' Simple class just cascades template and arguments to cheetah'''
            def validateArgs(self,args_dict):
                pass

        inputs = { 'name' : '',
                   'template'  : template,
                   'plugin' : SimplePlugin,
                   'plugin_args' : args }
        inputs.update(aux_args)
        t = ConfigCommand(**inputs)
        output_str = t.execute()
        return output_str
            
    def _getNii(self, args):
        """Handler for get-nii. args is a dict of supported key-value pairs for this action. """
        niihost = args.get('niihost',None)
        node = args.get('node',None)
        
        ul.debug('niihost : %s' % niihost)
        ul.debug('node : %s' % node)        
        if not niihost:
            msg = self._('Please specify a NII Host server.')
            self.printMsgExit(msg)
            
        if not node:
            msg = self._('Please specify a node name or node ip address.')
            self.printMsgExit(msg)
                  
        nii = RetrieveNIICommand(name = "ImageTool", logged=True , uri=nii_uri).execute()
        if nii: print nii

class FstabConfigPlugin(BasePlugin):
    def validateArgs(self,args_dict):
        '''XXX Fixme - must validate fstab args'''
        pass
    


if __name__ == '__main__':
    # set up tty3 for logging output
    if os.access("/dev/tty3", os.W_OK):
        ul.addFileHandler('/dev/tty3')

    app = ImageTool()
    app.run()


