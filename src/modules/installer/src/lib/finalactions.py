#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from path import path

def setupNetwork(self):
    # Use dhcpc from busybox
    # Assume eth0 for now
    from kusu.networktool import networktool

    interface = networktool.Interface('lo')
    interface.up()
    #interface = interface.setStaticIP(('127.0.0.1', '255.0.0.0'))

    interface = networktool.Interface('eth0')
    interface.up()
    interface = interface.setDHCP()
   
def copyKits(self, prefix):
    # Assume a Fedora 6 repo
    # Assume a fedora 6 distro: /mnt/sysimage
    from kusu.util import util

    url = str(self.database.get('Kits', 'FedoraURL')[0])

    prefix = path(prefix)
    util.verifyDistro(url, 'fedora', '6')
    util.copy(url, prefix + '/depot')

    
def makeRepo(self):
    pass

def genAutoInstallScript(self, disk_profile):
    from kusu.autoinstall.scriptfactory import KickstartFactory
    from kusu.autoinstall.autoinstall import Script
    from kusu.autoinstall.installprofile import Kickstart
    from kusu.networktool.network import Network

    # redhat based for now
    #kusu_dist = os.environ.get('KUSU_DIST', None)
    #kusu_distver = os.environ.get('KUSU_DISTVER', None)


    install_script = '/tmp/install_script'

    k = Kickstart()
    k.rootpw = self.database.get('Root Password', 'RootPasswd')[0]
    k.networkprofile = [Network('eth0')]
    k.diskprofile = disk_profile
    k.packageprofile = ['@Base']
    k.tz = self.database.get('Time zone', 'Zone')[0]
    k.installsrc = 'http://127.0.0.1/'
    k.lang = self.database.get('Language', 'Language')[0]
    k.keyboard = self.database.get('Keyboard', 'Keyboard')[0]

    template = path(os.getenv('KUSU_ROOT', None)) / \
               'etc' / \
               'templates' / \
               'kickstart.tmpl'

    kf = KickstartFactory(str(template))
    script = Script(kf)
    script.setProfile(k)
    script.write(install_script)

def migrate(self, prefix):
    dest = path(prefix) + '/root'
    
    kusu_tmp = os.environ.get('KUSU_TMP', None)
    kusu_log = os.environ.get('KUSU_LOGFILE', None)

    if not kusu_tmp or not kusu_log:
        raise Exception

    kusu_tmp = path(kusu_tmp)
    kusu_log = path(kusu_log)

    #files = [kusu_tmp / 'kusu.db', kusu_log]
    files = [path('/kusu.db'), kusu_log]

    for f in files:
        if f.exists():
            self.logger.debug('Moved %s -> %s' % (f, dest))
            f.move(dest)

def mountKusuMntPts(self, prefix, disk_profile):
    prefix = path(prefix)

    d = {}
    for disk in disk_profile.disk_dict.values():
        for id, p in disk.partition_dict.items():
            d[p.mountpoint] = p
   
    for lv in disk_profile.lv_dict.values():
        d[lv.mountpoint] = lv

    # Mount /, /root, /depot in order
    for m in ['/', '/root', '/depot']:
        mntpnt = prefix + m

        if not mntpnt.exists():
            mntpnt.makedirs()
            self.logger.debug('Made %s dir' % mntpnt)
        
        # mountpoint has an associated partition,
        # and mount it at the mountpoint
        if d.has_key(m):
            d[m].mount(mntpnt)
            self.logger.debug('Mounted %s on %s' % (d[m].mountpoint, mntpnt))

