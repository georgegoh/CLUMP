#!/usr/bin/env python
#
# $Id: template.py 196 2007-03-29 08:03:42Z ltsai $
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 

from path import path
import os

class BaseFactory:
    namespace = {}
    profile = None

    def __init__(self, template):
        self.template = template

    def setProfile(self, profile):
        if self._validateProfile(profile):
            self.profile = profile
        else:
            raise Exception

    def _validateProfile(self, profile):
        return True

class KickstartFactory(BaseFactory):
    
    def getNameSpace(self):
        #self.namespace['url'] = self.profile.getInstallSRC()
        #self.namespace['rootpw'] = self.profile.getRootPw()
        #self.namespace['tz'] = self.profile.getTZ()
        #self.namespace['lang'] = self.profile.getAttr('lang')
        #self.namespace['keybd'] = self.profile.getAttr('keybd')
        #self.namespace['packages'] = self.profile.getPackageProfile()
        #self.namespace['partitions'] = self._getPartitions()

        self.namespace['url'] = self.profile.installsrc
        self.namespace['rootpw'] = self.profile.rootpw
        self.namespace['tz'] = self.profile.tz
        self.namespace['lang'] = self.profile.lang
        self.namespace['keybd'] = self.profile.keyboard
        self.namespace['packages'] = self.profile.packageprofile
        self.namespace['partitions'] = self._getPartitions()


        # Creates the kickstart option for networking 
        self.namespace['networks'] = \
        ['network --bootproto %s --device %s'  % 
         (net.bootproto.lower(), net.dev) for net in self.profile.networkprofile]

        return self.namespace

    def _getPartitions(self):

        part_lines = []

        fstype_dict = { 'ext2': 'ext2',
                        'ext3': 'ext3',
                        'vfat': 'vfat', # Need to check this
                        'linux-swap': 'swap',
                        None: None}

        #disk_profile = self.profile.getDiskProfile()
        disk_profile = self.profile.diskprofile
        for disk in disk_profile.disk_dict.values():
            for id, p in disk.partitions_dict.items():
                fs_type = fstype_dict[p.fs_type]
                #print id, p.path, p.mountpoint, fs_type, p.type

                # Ignore other type of partitions             
                if p.type.lower() in ['extended']: 
                    continue

                # Ignore empty partitions
                if not p.mountpoint and not fs_type:
                    continue

                if p.mountpoint:
                    str = 'part %s' % p.mountpoint

                elif fs_type == 'swap':
                    str = 'part swap'
                else:
                    continue
                
                str = str + ' --fstype=%s' % fs_type

                # Drop the /dev 
                str = str + ' --onpart=%s' % \
                      os.path.sep.join((path(p.path).splitall()[2:])) 
                
                str = str + ' --noformat'

                part_lines.append(str) 

        return part_lines

        pv_id = {}  
        p = []
            
        cnt = 1
        disk_profile = self.profile.getDiskProfile()
        for disk in disk_profile.getDisk():
            for part in disk.getPart():
                if part.part_id == '8e':
                    str = 'part pv.%d --onpart=%s'  % (cnt,part.dev)
                    pv_id[part.dev] = cnt                  
                    p.append(str)

        for vg in disk_profile.getVolGrp():
            str = 'volgroup %s %s' % (vg.name, ' '.join(['pv.%s' % pv_id[part.dev] for part in vg.getPart()]))
            p.append(str)
        
        for vol in disk_profile.getVol():
            if isinstance(vol.obj, Partition):
                str = 'part %s' % vol.mntpoint
                if vol.fstype is not None:
                    str = str + ' --fstype=%s' % vol.fstype

                if vol.obj.dev is not None:
                    str = str + ' --onpart=%s' % vol.obj.dev 
            
                #if vol.obj.size is not None:
                #   str = str + ' --size=%s' % vol.obj.size

                str = str + ' --noformat'

            elif isinstance(vol.obj, LogVol):
                str = 'logvol %s --vgname=%s --name=%s --fstype=%s --size=%s' % \
                      (vol.mntpoint, vol.obj.volgrp_name, vol.obj.name, vol.fstype, vol.obj.size)
                
            p.append(str)

        
        return p



