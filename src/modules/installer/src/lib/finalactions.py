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
from kusu.util.verify import *
from kusu.util.errors import *
from path import path

logger = kusulog.getKusuLog('installer.final')

def setupDisks(disk_profile):
    disk_profile.commit()
    disk_profile.formatAll()
 
def setupNetwork():
    # Use dhcpc from busybox
    # Assume eth0 for now
    from kusu.networktool import networktool

    interface = networktool.Interface('lo')
    interface.up()
    #interface = interface.setStaticIP(('127.0.0.1', '255.0.0.0'))

    #interface = networktool.Interface('eth0')
    #interface.up()
    #interface = interface.setDHCP()
   
def makeRepo(kiprofile):
    db = kiprofile.getDatabase()
    rfactory = RepoFactory(db, '/mnt/kusu')

    session = db.createSession()
    #Guaranteed by installer screens. Only 1 OS kit for the platform
    #we are installing
    kit = session.query(db.kits).select_by(isOS)[0]
    ngname = 'installer-%s-%s-%s' % (kit.rname, kit.version, k.arch)
    session.close()

    repo = rfactory.make(ngname, 'Repo for ' + ngname)
    
    #Makes symlink in $KUSU_TMP/www
    kusu_tmp = os.environ.get('KUSU_TMP', None)
    repo.repo_path.symlink(path(kusu_tmp) / 'www')

def genAutoInstallScript(disk_profile, kiprofile):
    from kusu.autoinstall.scriptfactory import KickstartFactory
    from kusu.autoinstall.autoinstall import Script
    from kusu.autoinstall.installprofile import Kickstart

    # redhat based for now
    #kusu_dist = os.environ.get('KUSU_DIST', None)
    #kusu_distver = os.environ.get('KUSU_DISTVER', None)

    kusu_tmp = os.environ.get('KUSU_TMP', None)

    # is None
    if not kusu_tmp: 
        install_script = '/tmp/install_script'
    else:
        install_script = path(kusu_tmp) / 'install_script'


    # Build kickstart object
    # Retrieve all the data required
    db=kiprofile.getDatabase()
    k = Kickstart(db)
    k.rootpw = kiprofile['RootPasswd'] 

    if kiprofile.has_key('Network'):
        k.networkprofile = kiprofile['Network']
    else:
        k.networkprofile = {}

    k.diskprofile = disk_profile
    k.tz = kiprofile['Timezone']
    k.lang = kiprofile['Language']
    k.installsrc = 'http://127.0.0.1/' 
    k.keyboard = kiprofile['Keyboard']

    script = Script(KickstartFactory(k))
    script.write(install_script)

def migrate(prefix):
    dest = path(prefix) + '/root'
    
    kusu_tmp = os.environ.get('KUSU_TMP', None)
    kusu_log = os.environ.get('KUSU_LOGFILE', None)

    if not kusu_tmp or not kusu_log:
        kusu_tmp = '/tmp/kusu'
        kusu_log = '/tmp/kusu/kusu.log'

    kusu_tmp = path(kusu_tmp)
    kusu_log = path(kusu_log)

    files = [kusu_tmp / 'kusu.db', kusu_log]

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

