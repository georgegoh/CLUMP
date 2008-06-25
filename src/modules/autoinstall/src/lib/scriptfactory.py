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
from kusu.util import compat

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

    keys = ['diskprofile', \
            'networkprofile', \
            'packageprofile', \
            'rootpw', \
            'tz', \
            'installsrc', \
            'lang', \
            'keyboard']
    
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
        for key in self.keys:
            if not hasattr(profile, key):
                raise ProfileNotCompleteError, '%s attribute not found' % key

        return True
   
    def getNameSpace(self):
        self.namespace['url'] = self.profile.installsrc
        self.namespace['rootpw'] = self.profile.rootpw
        self.namespace['tz'] = self.profile.tz
        self.namespace['lang'] = self.profile.lang
        self.namespace['langsupport'] = self.profile.lang
        self.namespace['keybd'] = self.profile.keyboard
        self.namespace['packages'] = self.profile.packageprofile 
        self.namespace['partitions'] = self._getPartitions()
        self.namespace['networks'] = self._getNetworks()
        self.namespace['ignoredisk'] = self._getIgnoreDisks()
        self.namespace['mbrdriveorder'] = self._getMBRDriveOrder()
        self.namespace['mbrbootloader'] = self._useMBR()
        self.namespace['kernelparams'] = self._getKernelParams()

        return self.namespace

    def _getNetworks(self):
        # Creates the kickstart option for networking 

        network_lines = []
        networks = self.profile.networkprofile

        if not self.profile.networkprofile:
            # No network
            return network_lines

        dns = [networks[key] for key in ['dns1', 'dns2', 'dns3'] \
               if networks.has_key(key) and networks[key]] 

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
                    if networks.has_key('default_gw') and networks['default_gw']:
                        str = str + ' --gateway=%s'% networks['default_gw']
                    
                    if dns:
                        str = str + ' --nameserver=%s' % ','.join(dns)
                   
                if not networks['fqhn_use_dhcp'] \
                   and networks.has_key('fqhn_host') and networks['fqhn_host']:
                    str += ' --hostname %s' % networks['fqhn_host']
                
                network_lines.append(str)

            else:
                # Do nothing for not configured interfaces
                pass

        return network_lines

    def _useMBR(self):
        for disk in self.profile.diskprofile.disk_dict.values():
            for partition in disk.partition_dict.values():
                if partition.native_type == 'Dell Utility' or partition.dellUP_flag:
                    return False
        return True

    def _getMBRDriveOrder(self):
        drive_list = self.profile.diskprofile.disk_dict.keys()
        return sorted(drive_list)

    def _getIgnoreDisks(self):
        disk_profile = self.profile.diskprofile
        ignore_disks = disk_profile.ignore_disk_dict.keys()

        return ','.join(ignore_disks)

    def _getKernelParams(self):
        return ''

    def _getPartitions(self):

        part_lines = []

        # Translate from parted to anaconda defn
        # parted filesystem type -> anaconda
        fstype_dict = { 'ext2': 'ext2',
                        'ext3': 'ext3',
                        'fat32': 'vfat', 
                        'fat16': 'vfat', 
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
            if not lv.mountpoint: continue 
            str = 'logvol %s --vgname=%s --name=%s --noformat' % \
                  (lv.mountpoint, lv.group.name, lv.name)
            part_lines.append(str)

        return part_lines

class RHEL5KickstartFactory(KickstartFactory):
    def __init__(self, profile, template=None):
        KickstartFactory.__init__(self, profile, template) 
        self.keys.append('instnum')

    def getNameSpace(self):
        self.namespace['url'] = self.profile.installsrc
        self.namespace['rootpw'] = self.profile.rootpw
        self.namespace['tz'] = self.profile.tz
        self.namespace['lang'] = self.profile.lang
        self.namespace['langsupport'] = self.profile.lang
        self.namespace['keybd'] = self.profile.keyboard
        self.namespace['packages'] = self.profile.packageprofile 
        self.namespace['partitions'] = self._getPartitions()
        self.namespace['networks'] = self._getNetworks()
        self.namespace['instnum'] = self.profile.instnum
        self.namespace['ignoredisk'] = self._getIgnoreDisks()
        self.namespace['mbrdriveorder'] = self._getMBRDriveOrder()
        self.namespace['mbrbootloader'] = self._useMBR()
        self.namespace['kernelparams'] = self._getKernelParams()

        return self.namespace

class Fedora7KickstartFactory(KickstartFactory):
    def __init__(self, profile, template=None):
        KickstartFactory.__init__(self, profile, template) 

    def getNameSpace(self):
        self.namespace['url'] = self.profile.installsrc
        self.namespace['rootpw'] = self.profile.rootpw
        self.namespace['tz'] = self.profile.tz
        self.namespace['lang'] = self.profile.lang
        self.namespace['keybd'] = self.profile.keyboard
        self.namespace['packages'] = self.profile.packageprofile 
        self.namespace['partitions'] = self._getPartitions()
        self.namespace['networks'] = self._getNetworks()
        self.namespace['ignoredisk'] = self._getIgnoreDisks()
        self.namespace['mbrdriveorder'] = self._getMBRDriveOrder()
        self.namespace['mbrbootloader'] = self._useMBR()
        self.namespace['kernelparams'] = self._getKernelParams()

        return self.namespace

class Fedora8KickstartFactory(KickstartFactory):
    def __init__(self, profile, template=None):
        KickstartFactory.__init__(self, profile, template) 

    def getNameSpace(self):
        self.namespace['url'] = self.profile.installsrc
        self.namespace['rootpw'] = self.profile.rootpw
        self.namespace['tz'] = self.profile.tz
        self.namespace['lang'] = self.profile.lang
        self.namespace['keybd'] = self.profile.keyboard
        self.namespace['packages'] = self.profile.packageprofile 
        self.namespace['partitions'] = self._getPartitions()
        self.namespace['networks'] = self._getNetworks()
        self.namespace['ignoredisk'] = self._getIgnoreDisks()
        self.namespace['mbrdriveorder'] = self._getMBRDriveOrder()
        self.namespace['mbrbootloader'] = self._useMBR()
        self.namespace['kernelparams'] = self._getKernelParams()

        return self.namespace

class Fedora9KickstartFactory(KickstartFactory):
    def __init__(self, profile, template=None):
        KickstartFactory.__init__(self, profile, template) 

    def getNameSpace(self):
        self.namespace['url'] = self.profile.installsrc
        self.namespace['rootpw'] = self.profile.rootpw
        self.namespace['tz'] = self.profile.tz
        self.namespace['lang'] = self.profile.lang
        self.namespace['keybd'] = self.profile.keyboard
        self.namespace['packages'] = self.profile.packageprofile 
        self.namespace['partitions'] = self._getPartitions()
        self.namespace['networks'] = self._getNetworks()
        self.namespace['ignoredisk'] = self._getIgnoreDisks()
        self.namespace['mbrdriveorder'] = self._getMBRDriveOrder()
        self.namespace['mbrbootloader'] = self._useMBR()
        self.namespace['kernelparams'] = self._getKernelParams()

        return self.namespace


