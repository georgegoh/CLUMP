#!/usr/bin/env python
#
# $Id$
#
# Copyright 2008 Platform Computing Inc.
import os
import time
import md5crypt
import urlparse
from path import path
from tempfile import mkdtemp
from primitive.support import compat
from primitive.fetchtool.commands import FetchCommand
from primitive.core.errors import TemplateNotFoundException
from primitive.core.errors import AutoInstallConfigNotCompleteException

class KickstartFactory(object):

    keys = ['diskprofile',
            'networkprofile',
            'packageprofile',
            'rootpw',
            'tz',
            'tz_utc',
            'installsrc',
            'lang',
            'keyboard',
            'diskorder']
 
    def __init__(self, **kwargs):
        self.template_dir = path(mkdtemp(prefix='KickstartFactory-'))
        valid_conf, missing = self._validateConf(kwargs)
        if valid_conf:
            self.conf = kwargs
        else:
            raise AutoInstallConfigNotCompleteException, \
                  '%s attributes not found in config.' % missing
        self.setTemplatePath(kwargs)
        self.namespace = {}

    def __del__(self):
        self.template_dir.rmtree()


    def setTemplatePath(self, conf):
        protocol = urlparse.urlparse(conf['template_uri'])[0]
        fc = FetchCommand(uri=conf['template_uri'], fetchdir=False,
                          destdir=self.template_dir, overwrite=True)
        fc.execute()

        self.template = self.template_dir / \
                        path(conf['template_uri']).basename()
        if not self.template.exists():
            raise TemplateNotFoundException, \
                  '%s template not found' % self.template
    

    def _validateConf(self, conf):
        valid = True
        missing = []
        for key in self.keys:
            if not conf.has_key(key):
                valid = False
                missing.append(key)
        return valid, missing

  
    def getNameSpace(self):
        self.namespace['url'] = self.conf['installsrc']
        self.namespace['rootpw'] = self._getMD5Password()
        self.namespace['tz'] = self.conf['tz']
        self.namespace['tz_utc'] = self.conf['tz_utc']
        self.namespace['lang'] = self.conf['lang']
        self.namespace['langsupport'] = self.conf['lang']
        self.namespace['keybd'] = self.conf['keyboard']
        self.namespace['packages'] = self.conf['packageprofile']
        self.namespace['partitions'] = self._getPartitions()
        self.namespace['networks'] = self._getNetworks()
        self.namespace['ignoredisk'] = self._getIgnoreDisks()
        self.namespace['mbrdriveorder'] = ','.join(self.conf['diskorder'])
        self.namespace['mbrbootloader'] = self._useMBR()
        self.namespace['kernelparams'] = self._getKernelParams()
        self.namespace['partitionrules'] = self._getPartitionRules()
        self.namespace['swap_label'] = self._getSwapLabel()
        self.namespace['swap_path'] = self._getSwapPath()
        self.namespace['swap_devbasename'] = self._getSwapDevBasename()
        return self.namespace

    def _getMD5Password(self):
        return md5crypt.md5crypt(str(self.conf['rootpw']), (str(time.time())))

    def _getIgnoreDisks(self):
        dp = self.conf['diskprofile']
        if not dp:
            return ''
        ignore_disks = dp.ignore_disk_dict.keys()
        return ','.join(ignore_disks)

    def __getSwap(self):
        dp = self.conf['diskprofile']
        if not dp:
            return None
        disk = dp.disk_dict[self.conf['diskorder'][0]]
        for p in disk.partition_dict.values():
            if p.fs_type == 'linux-swap':
                return p
        return None

    def _getSwapLabel(self):
        swap = self.__getSwap()
        if swap:
            return swap.label
        return ''

    def _getSwapPath(self):
        swap = self.__getSwap()
        if swap:
            return swap.path
        return ''

    def _getSwapDevBasename(self):
        swap = self._getSwapPath()
        return os.path.basename(swap)

    def _useMBR(self):
        dp = self.conf['diskprofile']
        if not dp:
            return True
        for disk in dp.disk_dict.values():
            for partition in disk.partition_dict.values():
                if partition.native_type=='Dell Utility' or partition.dellUP_flag:
                    return False
        if hasattr(dp, 'use_mbr'):
            return dp.use_mbr
        return True

    def _getPartitions(self):
        part_lines = []

        # Translate from parted to anaconda defn
        # parted filesystem type -> anaconda
        fstype_dict = { 'ext2': 'ext2',
                        'ext3': 'ext3',
                        'fat32': 'vfat', 
                        'fat16': 'vfat',
                        'ntfs': 'ntfs', 
                        'linux-swap': 'swap',
                        None: None}

        # Handles normal partitions without, pv, vg, lv 
        disk_profile = self.conf['diskprofile']
        if not disk_profile:
            return []
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
               
                if p.label:
                    str = str + ' --label=%s' % p.label

                str = str + ' --fstype=%s' % fs_type

                # Drop the /dev 
                str = str + ' --onpart=%s' % \
                      os.path.sep.join((path(p.path).splitall()[2:])) 
        
                if fs_type != 'swap':
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


    def _getPartitionRules(self):
        """ Using the rules from self.conf['partitionrules'], convert
            into anaconda kickstart style rules. The expected format
            of the rules in self.conf['partitionrules'] is a list of
            objects which have the following attributes:
                i. mntpnt
                ii. fstype
                iii. size
        """
        partition_lines = []
        # wipe all existing partitions.
        partition_lines.append('clearpart all')
        # Return default rules if custom rules do not exist.
        if not self.conf.has_key('partitionrules'):
            partition_lines.append('part /boot --fstype ext3 --size=100')
            partition_lines.append('part / --fstype ext3 --size=12000')
            partition_lines.append('part swap --fstype swap --size=2000')
            partition_lines.append('part /var --fstype ext3 --size=2000')
            partition_lines.append('part /data --fstype ext3 --size=14000 --grow')
            partition_lines.append('volgroup VolGroup00 --pesize=32768 pv.2')
            partition_lines.append('logvol swap --fstype swap --name=LogVol01 --vgname=VolGroup00 --size=496 --grow --maxsize=992')
            partition_lines.append('logvol / --fstype ext3 --name=LogVol00 -- vgname=VolGroup00 --size=1024 --grow')
            return partition_lines

        for r in self.conf['partitionrules']:
            # only deal with physical partitions with FS defined.
            if r.fstype=='linux-swap':
                partition_lines.append('part swap --fstype swap --size=%s' %
                                       r.size)
            elif r.fstype and r.options=='fill':
                partition_lines.append('part %s --fstype %s --size=%s --grow' %
                                       (r.mntpnt, r.fstype, r.size))
            elif r.fstype:
                partition_lines.append('part %s --fstype %s --size=%s' %
                                       (r.mntpnt, r.fstype, r.size))
        return partition_lines

    def _getNetworks(self):
        # Creates the kickstart option for networking 

        network_lines = []
        networks = self.conf['networkprofile']

        if not self.conf['networkprofile']:
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

    def _getKernelParams(self):
        return ''


class RHEL5KickstartFactory(KickstartFactory):
    def __init__(self, **kwargs):
        KickstartFactory.__init__(self, **kwargs) 
        self.keys.append('instnum')

    def getNameSpace(self):
        self.namespace['instnum'] = self.conf['instnum']
        return KickstartFactory.getNameSpace(self)
