#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import kusu.util.log as kusulog
from path import path

logger = kusulog.getKusuLog('installer.final')

def setupNetwork():
    # Use dhcpc from busybox
    # Assume eth0 for now
    from kusu.networktool import networktool

    interface = networktool.Interface('lo')
    interface.up()
    #interface = interface.setStaticIP(('127.0.0.1', '255.0.0.0'))

    interface = networktool.Interface('eth0')
    interface.up()
    interface = interface.setDHCP()
   
def copyKits(prefix, database):
    # Assume a Fedora 6 repo
    # Assume a fedora 6 distro: /mnt/sysimage
    from kusu.util import util

    url = str(database.get('Kits', 'FedoraURL')[0])

    prefix = path(prefix)
    util.verifyDistro(url, 'fedora', '6')
    util.copy(url, prefix + '/depot')

    
def makeRepo(self):
    pass

def genAutoInstallScript(disk_profile, database):
    from kusu.autoinstall.scriptfactory import KickstartFactory
    from kusu.autoinstall.autoinstall import Script
    from kusu.autoinstall.installprofile import Kickstart
    from kusu.networktool.network import Network

    # redhat based for now
    #kusu_dist = os.environ.get('KUSU_DIST', None)
    #kusu_distver = os.environ.get('KUSU_DISTVER', None)

    kusu_tmp = os.environ.get('KUSU_TMP', None)

    # is None
    if not kusu_tmp: 
        install_script = '/tmp/install_script'
    else:
        install_script = path(kusu_tmp) / 'install_script'

    k = Kickstart()
    k.rootpw = database.get('Root Password', 'RootPasswd')[0]
    n = Network('eth0')
    n.bootproto = 'dhcp'
    k.networkprofile = [n]
    k.diskprofile = disk_profile
    k.packageprofile = ['@Base']
    k.tz = database.get('Time zone', 'Zone')[0]
    k.installsrc = 'http://127.0.0.1/'
    k.lang = database.get('Language', 'Language')[0]
    k.keyboard = database.get('Keyboard', 'Keyboard')[0]

    template = path(os.getenv('KUSU_ROOT', None)) / \
               'etc' / \
               'templates' / \
               'kickstart.tmpl'

    kf = KickstartFactory(str(template))
    script = Script(kf)
    script.setProfile(k)
    script.write(install_script)

def migrate(prefix):
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
            logger.debug('Moved %s -> %s' % (f, dest))
            f.move(dest)

def mountKusuMntPts(prefix, disk_profile):
    prefix = path(prefix)

    d = {}
    for disk in disk_profile.disk_dict.values():
        for id, p in disk.partition_dict.items():
            d[p.mountpoint] = p
   
    for lv in disk_profile.lv_dict.values():
        d[lv.mountpoint] = lv

    # Mount and create in order
    for m in ['/', '/root', '/depot', '/depot/repos', '/depot/kits']:
        mntpnt = prefix + m

        if not mntpnt.exists():
            mntpnt.makedirs()
            logger.debug('Made %s dir' % mntpnt)
        
        # mountpoint has an associated partition,
        # and mount it at the mountpoint
        if d.has_key(m):
            d[m].mount(mntpnt)

