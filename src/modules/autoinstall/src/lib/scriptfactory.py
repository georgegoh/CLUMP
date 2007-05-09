#!/usr/bin/env python
#
# $Id$
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
        self.namespace['url'] = self.profile.installsrc
        self.namespace['rootpw'] = self.profile.rootpw
        self.namespace['tz'] = self.profile.tz
        self.namespace['lang'] = self.profile.lang
        self.namespace['keybd'] = self.profile.keyboard
        self.namespace['packages'] = self.profile.packageprofile
        self.namespace['partitions'] = self._getPartitions()
        self.namespace['networks'] = self._getNetworks()

        return self.namespace

    def _getNetworks(self):
        # Creates the kickstart option for networking 

        network_lines = []
        networks = self.profile.networkprofile.net_dict.values()
        for network in networks:
            str = ''

            if network.bootproto == 'dhcp':
                str = 'network --bootproto dhcp --device %s' % network.dev
            #elif network.bootproto == 'static':
            #    str = 'network --bootproto static  --device %s' % network.dev
            else:
                pass #Ignore other types

            if str:            
                network_lines.append(str)

        return network_lines

    def _getPartitions(self):

        part_lines = []

        fstype_dict = { 'ext2': 'ext2',
                        'ext3': 'ext3',
                        'vfat': 'vfat', # Need to check this
                        'linux-swap': 'swap',
                        None: None}

        # Handles normal partitions without, pv, vg, lv 
        disk_profile = self.profile.diskprofile
        for disk in disk_profile.disk_dict.values():
            for id, p in disk.partition_dict.items():
                fs_type = fstype_dict[p.fs_type]

                # Ignore other type of partitions             
                if p.type.lower() in ['extended']: 
                    continue
                
                # Ignore physical volume
                if p.lvm_flag:
                    continue

                # Ignore empty partitions
                if not p.mountpoint and not fs_type:
                    continue

                if p.mountpoint:
                    str = 'part %s' % p.mountpoint

                elif fs_type == 'swap':
                    str = 'part swap'
                else:
                    # Ignore other bits like empty mount point
                    continue 
                
                str = str + ' --fstype=%s' % fs_type

                # Drop the /dev 
                str = str + ' --onpart=%s' % \
                      os.path.sep.join((path(p.path).splitall()[2:])) 
                
                str = str + ' --noformat'

                part_lines.append(str) 


        # Handles LVM

        # Dictionary for kickstart pv.<id> for physical volumes
        # and vol ggroup association
        pv_id = {}  
     
        cnt = 1
        #PV
        for pv in disk_profile.pv_dict.values(): 
            str = 'part pv.%d --onpart=%s --noformat'  % (cnt,
                   os.path.sep.join((path(pv.partition.path).splitall()[2:])))
            pv_id[pv.partition.path] = cnt                  
            part_lines.append(str)

        #VG
        for vg in disk_profile.lvg_dict.values(): 
            str = 'volgroup %s %s --noformat' % (vg.name, ' '.join(['pv.%s' % \
                  pv_id[pv.partition.path] for pv in vg.pv_dict.values()]))
            part_lines.append(str)
       
        #LV
        for lv in disk_profile.lv_dict.values(): 
            str = 'logvol %s --vgname=%s --name=%s --noformat' % \
                  (lv.mountpoint, lv.group.name, lv.name)
            part_lines.append(str)


        return part_lines
