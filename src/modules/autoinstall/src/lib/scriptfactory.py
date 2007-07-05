#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 

import os
from path import path
from kusu.util.errors import *

class BaseFactory:
    namespace = {}
    profile = None

    def __init__(self, template, profile):
        self.template = template
         
        if self._validateProfile(profile):
            self.profile = profile
        else:
            raise ProfileNotCompleteError

    def _validateProfile(self, profile):
        return True

class KickstartFactory(BaseFactory):
 
    def __init__(self, profile, template=None):
    
        if template:
            self.template = path(template)
        else:
            kusu_root = os.getenv('KUSU_ROOT', None)

            if not kusu_root:
                kusu_root = '/opt/kusu'

            kusu_dist = os.environ.get('KUSU_DIST', None)
            kusu_distver = os.environ.get('KUSU_DISTVER', None)

            self.template = path(kusu_root) / \
                            'etc' / \
                            'templates' / \
                            'kickstart.tmpl'
       
        if not self.template.exists():
            raise TemplateNotFoundError, '%s not found' % self.template

        if self._validateProfile(profile):
            self.profile = profile

    def _validateProfile(self, profile):
        
        keys = ['diskprofile', \
                'networkprofile', \
                'packageprofile', \
                'rootpw', \
                'tz', \
                'installsrc', \
                'lang', \
                'keyboard']
         
        for key in keys:
            if not getattr(profile, key):
                raise ProfileNotCompleteError, '%s attribute not found' % key

        return True
   
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
        networks = self.profile.networkprofile

        if not self.profile.networkprofile:
            # No network
            return network_lines

        for intf, v in networks['interfaces'].items():
            str = ''

            # Convert to anaconda syntax
            if v['active_on_boot']:
                v['active_on_boot'] = 'yes'
            else:
                v['active_on_boot'] = 'no'

            if v['configure']:
                if v['use_dhcp']:
                    str = 'network --bootproto dhcp --device=%s --onboot=%s' % \
                          (intf, v['active_on_boot'])
                else:
                    str = 'network --bootproto static  --device=%s --ip=%s --netmask=%s --onboot=%s' % \
                          (intf, v['ip_address'], v['netmask'], v['active_on_boot'])

                if not networks['gw_dns_use_dhcp']: # manual gw and dns
                    str = str + ' --gateway=%s --nameserver=%s' % \
                          (networks['default_gw'], networks['dns1']) # Only 1 dns allowed
                   
                if not networks['fqhn_use_dhcp']: # manual hostname
                    str = str + ' --hostname %s' % networks['fqhn']
                
                network_lines.append(str)

            else:
                # Do nothing for not configured interfaces
                pass

        return network_lines

    def _getPartitions(self):

        part_lines = []

        # Translate from parted to anaconda defn
        # parted filesystem type -> anaconda
        fstype_dict = { 'ext2': 'ext2',
                        'ext3': 'ext3',
                        'fat32': 'vfat', 
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
            str = 'part pv.%d --onpart=%s --noformat'  % (cnt, \
                   os.path.sep.join((path(pv.partition.path).splitall()[2:])))
            pv_id[pv.partition.path] = cnt                  
            part_lines.append(str)
            cnt = cnt + 1

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
