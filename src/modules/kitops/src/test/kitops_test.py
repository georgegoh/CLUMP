#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import tempfile
import urllib
import os
from path import path
from nose import SkipTest

try:
    import subprocess
except:
    from popen5 import subprocess

from nose.tools import raises
from kusu.kitops.kitops import KitOps
from kusu.util.errors import *
import kusu.util.log as kusulog
kl = kusulog.getKusuLog()
kl.addFileHandler(path(os.environ.get('KUSU_TMP', '/tmp/kusu')) /
                       'kusu-kitops.log')


# NOTE: test_kits_url NEEDS a trailing slash
test_kits_url = 'http://www.osgdc.org/pub/build/tests/modules/kitops/'
tmp_prefix = path(os.environ.get('KUSU_TMP', '/tmp'))
tmp_prefix = tmp_prefix / 'kitops_test'
test_kits_path = tmp_prefix / 'kitops_test_isos'
test_kits_base = 'mock-kit-base-0.1-0.noarch.iso'
test_kits_fc6i386_1 = 'mock-FC-6-i386-disc1.iso'
test_kits_fc6i386_2 = 'mock-FC-6-i386-disc2.iso'

temp_mount = None

def assertRoot():
    if os.getuid() != 0:
        raise SkipTest

def setUp():
    global temp_mount
    global tmp_prefix

    print tmp_prefix
    print type(tmp_prefix)

    if not tmp_prefix.exists():
        tmp_prefix.makedirs()

    temp_mount = path(tempfile.mkdtemp(prefix='kot', dir=tmp_prefix))

def tearDown():
    global tmp_prefix

    tmp_prefix.rmtree()

class TestKitOps:
    def setUp(self):
        global temp_mount

        self.temp_mount = temp_mount
        self.koinst = KitOps()

    def tearDown(self):
        global temp_mount

        if self.temp_mount.ismount():
            unmountKit(self.temp_mount)

    def testSetPrefix(self):
        some_prefix = '/some/prefix'
        self.koinst.setPrefix(some_prefix)
        
        assert self.koinst.prefix == some_prefix
        assert self.koinst.kits_dir.startswith(some_prefix)
        assert self.koinst.pxeboot_dir.startswith(some_prefix)

    def testSetKitMedia(self):
        kitmedia = '/path/to/kit/media'
        self.koinst.setKitMedia(kitmedia)
        
        assert self.koinst.kitmedia == kitmedia

    def testSetDB(self):
        db = {'test_db': True}
        self.koinst.setDB(db)

        assert self.koinst._KitOps__db == db

    def testSetTmpPrefix(self):
        tmp_prefix = '/path/to/tmp'
        self.koinst.setTmpPrefix(tmp_prefix)
        
        assert self.koinst.tmpprefix == tmp_prefix

    def testGetOSDist(self):
        for kit in [test_kits_base, test_kits_fc6i386_1, test_kits_fc6i386_2]:
            self.checkGetOSDist(kit)

    def checkGetOSDist(self, kit):
        from kusu.boot.distro import DistroFactory

        needKit(kit)
        mountKit(test_kits_path / kit, self.temp_mount)
 
        self.koinst.mountpoint = self.temp_mount
        kitops_osdist = self.koinst.getOSDist()
        bmt_osdist = DistroFactory(str(self.temp_mount))

        unmountKit(self.temp_mount)

        assert kitops_osdist.__dict__ == bmt_osdist.__dict__, \
            'kitops.getOSDist() does not check out for kit %s' % kit

    def testAddKitPrepareISO(self):
        assertRoot()

        needKit(test_kits_base)

        self.koinst.kitmedia = test_kits_path / test_kits_base

        self.koinst.addKitPrepare()
        koinst_mountpoint = self.koinst.mountpoint
        assert koinst_mountpoint is not None, 'Error mounting ISO'

        koinst_mountpoint_isdir = self.koinst.mountpoint.isdir()
        koinst_mountpoint_ismount = self.koinst.mountpoint.ismount()

        unmountKit(self.koinst.mountpoint)

        assert koinst_mountpoint_isdir, \
                'Mount point %s is not a directory' % koinst_mountpoint
        assert koinst_mountpoint_ismount, \
                'Mount point %s is not a mount point' % koinst_mountpoint

    def testAddKitPrepareMountPoint(self):
        assertRoot()

        needKit(test_kits_base)

        mountKit(test_kits_path / test_kits_base, self.temp_mount)
        self.koinst.kitmedia = self.temp_mount

        self.koinst.addKitPrepare()
        koinst_mountpoint = self.koinst.mountpoint
        assert koinst_mountpoint is not None, 'Mountpoint invalid'

        koinst_mountpoint_isdir = self.koinst.mountpoint.isdir()
        koinst_mountpoint_ismount = self.koinst.mountpoint.ismount()

        unmountKit(self.koinst.mountpoint)

        assert koinst_mountpoint_isdir, \
                'Mount point %s is not a directory' % koinst_mountpoint
        assert koinst_mountpoint_ismount, \
                'Mount point %s is not a mount point' % koinst_mountpoint

    def testAddKitPrepareNetISO(self):
        assertRoot()

        self.koinst.kitmedia = test_kits_url + test_kits_base

        self.koinst.addKitPrepare()
        koinst_mountpoint = self.koinst.mountpoint
        assert koinst_mountpoint is not None, 'Mountpoint invalid'

        koinst_mountpoint_isdir = self.koinst.mountpoint.isdir()
        koinst_mountpoint_ismount = self.koinst.mountpoint.ismount()

        unmountKit(self.koinst.mountpoint)
        self.koinst.dlkitiso.remove()

        assert koinst_mountpoint_isdir, \
                'Mount point %s is not a directory' % koinst_mountpoint
        assert koinst_mountpoint_ismount, \
                'Mount point %s is not a mount point' % koinst_mountpoint
        
    @raises(UnrecognizedKitMediaError)
    def testAddKitPrepareInvalid(self):
        self.koinst.kitmedia = '/path/to/invalid/kit'

        self.koinst.addKitPrepare()
        koinst_mountpoint = self.koinst.mountpoint
        koinst_mountpoint_isdir = self.koinst.mountpoint.isdir()
        koinst_mountpoint_ismount = self.koinst.mountpoint.ismount()

        unmountKit(self.koinst.mountpoint)
        self.koinst.dlkitiso.remove()

        assert koinst_mountpoint_isdir, \
                'Mount point %s is not a directory' % koinst_mountpoint
        assert koinst_mountpoint_ismount, \
                'Mount point %s is not a mount point' % koinst_mountpoint

    def test_unmount_only_if_we_mounted(self):
        assertRoot()

        needKit(test_kits_base)

        self.koinst.kitmedia = test_kits_path / test_kits_base

        self.koinst.mountMedia(self.koinst.kitmedia, True)
        current_mountpoint = self.koinst.mountpoint

        assert current_mountpoint is not None, 'Error mounting ISO'

        assert current_mountpoint.isdir(), \
            'Mount point %s is not a directory' % current_mountpoint
        assert current_mountpoint.ismount(), \
            'Mount point %s is not a mount point' % current_mountpoint

        self.koinst.unmountMedia()

        assert not current_mountpoint.exists(), \
            'Mountpoint %s not removed' % current_mountpoint

    def test_dont_unmount_if_already_mounted(self):
        assertRoot()

        needKit(test_kits_base)

        mountKit(test_kits_path / test_kits_base, self.temp_mount)
        self.koinst.kitmedia = self.temp_mount
        self.koinst.medialoc = path(self.temp_mount)
        self.koinst.mountpoint = path(self.temp_mount)

        self.koinst.unmountMedia()

        assert self.temp_mount.exists(), \
            'Mount point %s removed' % self.temp_mount
        assert self.temp_mount.isdir(), \
            'Mount point %s not a directory' % self.temp_mount
        assert self.temp_mount.ismount(), \
            'Mount point %s not a mount point' % self.temp_mount

        unmountKit(self.temp_mount)

def needKit(kit):
    if not path(test_kits_path / kit).exists():
        downloadFiles(kit)

def downloadFiles(fn):
    if not test_kits_path.exists():
        test_kits_path.makedirs()

    urllib.urlretrieve(test_kits_url + fn, test_kits_path / fn)

def mountKit(kit, mntpt):
    mountP = subprocess.Popen('mount -o loop %s %s' % (kit, mntpt), shell=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return mountP.communicate()

def unmountKit(mntpt):
    umountP = subprocess.Popen('umount %s' % mntpt, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return umountP.communicate()
