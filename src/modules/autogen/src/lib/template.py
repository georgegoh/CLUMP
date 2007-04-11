#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 

from installprofile import KickstartProfile
from profile.disk import *
from profile.network import Network
from Cheetah.Template import Template


class BaseTemplate:
    namespace = {}
    profile = None

    def __init__(self, template, profile):
        self.template = template
        if _validateProfile(profile):
            self.profile = profile
        else:
            raise Exception

    def setVar(self, key, val):
        self.namespace[key] = val

    def getNameSpace(self):
        pass

    def getNetwork(self):
        pass

    def write(self, f):
        out = open(f, 'w')
        t = Template(file=self.template, searchList=[self.getNameSpace()])  
        out.write(str(t))
        out.close()

    def _validateProfile(self, profile):
        pass

class KickstartTemplate(BaseTemplate):
    
    keys = ['url', 'rootpw', 'tz', 'lang', 'keybd', 'packages', 'partitions', 'networks']

    def getVar(self):
        pass

    def getKeys(self):
        return self.keys
    
    def getNameSpace(self):
        self.namespace['url'] = self.profile.getInstallSRC()
        self.namespace['rootpw'] = self.profile.getRootPw()
        self.namespace['tz'] = self.profile.getTZ()
        self.namespace['lang'] = self.profile.getAttr('lang')
        self.namespace['keybd'] = self.profile.getAttr('keybd')
        self.namespace['packages'] = self.profile.getPackageProfile()
        self.namespace['partitions'] = self.getPartitions()


        # Creates the kickstart option for networking 
        self.namespace['networks'] = \
        ['network --bootproto %s --device %s'  % 
         (net.bootproto.lower(), net.dev) for net in self.profile.getNetworkProfile()]

        return self.namespace

    def getPartitions(self):
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

                if vol.format != True:
                    str = str + ' --noformat'

            elif isinstance(vol.obj, LogVol):
                str = 'logvol %s --vgname=%s --name=%s --fstype=%s --size=%s' % \
                      (vol.mntpoint, vol.obj.volgrp_name, vol.obj.name, vol.fstype, vol.obj.size)
                
            p.append(str)

        return p

    def _validateProfile(self, profile):
        return True

if __name__ == '__main__':
    d = Disk(8000, 'sda') 
    d.addPart('sda1', 1,100, '83')   
    d.addPart('sda2', 2,2000, '8e') #linux lvm
    d.addPart('sda3', 3,2000, '83')

    vg00 = VolGrp('vg00', [d.getPart(2)])
    vg00.addLv('lv00', 1000, '83')
    vg00.addLv('lv01', 512, '82') #swap

    lvol = []
    lvol.append(Vol(d.getPart(1), '/boot', '/boot', 'ext3', True))
    lvol.append(Vol(d.getPart(3), '/data', '/data', 'ext3', True))

    lvol.append(Vol(vg00.getLv('lv00'), '/', '/', 'ext3', True))
    lvol.append(Vol(vg00.getLv('lv01'), 'swap', 'swap', 'swap', True))

    p = DiskProfile()
    p.addDisk(d)
    p.addVolGrp(vg00)
    p.addVol(lvol)

    k = Kickstart()
    k.setRootPw('system')
    k.setNetworkProfile(Network('eth0', 'DHCP'))
    k.setDiskProfile(p)
    k.setPackageProfile(['@Base'])
    k.setTZ('Asia/Singapore')
    k.setInstallSRC('http://172.25.208.218/repo/fedora/6/i386/os/')
    k.setAttr('lang', 'us')
    k.setAttr('keybd', 'us')

    kt = KickstartTemplate('templates/kickstart.tmpl', kt)
    kt.write('/var/www/html/kickstart.cfg')
