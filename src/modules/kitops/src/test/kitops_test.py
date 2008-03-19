#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import tempfile
import urllib
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

from kusu.core import database as db

# NOTE: test_kits_url NEEDS a trailing slash
test_kits_url = 'http://www.osgdc.org/pub/build/tests/modules/kitops/'
tmp_prefix = path(tempfile.mkdtemp(prefix='kitops_test',
                                   dir=os.environ.get('KUSU_TMP', '/tmp')))
test_kits_path = tmp_prefix / 'kitops_test_isos'
test_kits_base = 'mock-kit-base-0.1-0.noarch.iso'
test_kits_fc6i386_1 = 'mock-FC-6-i386-disc1.iso'
test_kits_fc6i386_2 = 'mock-FC-6-i386-disc2.iso'

# test db
kusudb = tmp_prefix / 'kusu.db'
dbs = db.DB('sqlite', kusudb)

temp_mount = None

def assertRoot():
    if os.getuid() != 0:
        raise SkipTest

def setup():
    global temp_mount
    global tmp_prefix

    if not tmp_prefix.exists():
        tmp_prefix.makedirs()

    temp_mount = path(tempfile.mkdtemp(prefix='kot', dir=tmp_prefix))

def teardown():
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

class TestKitDeletion:
    def setUp(self):
        dbs.createTables()
        self.koinst = KitOps()

        # Let's set some variables in our kitops object.
        self.koinst.prefix = tmp_prefix
        self.koinst.kits_dir = tmp_prefix / 'depot/kits/'
        self.koinst.pxeboot_dir = tmp_prefix / 'tftpboot/kusu/'
        self.koinst._KitOps__db = dbs

    def tearDown(self):
        dbs.dropTables()

    def test_delete_kit(self):
        kn = 'kit1'
        kv = '1.0'
        ka = 'i386'
        create_mock_kit(kn, kv, ka)

        # Let's set some variables in our kitops object.
        self.koinst.prefix = tmp_prefix
        self.koinst.kits_dir = tmp_prefix / 'depot/kits/'
        self.koinst.pxeboot_dir = tmp_prefix / 'tftpboot/kusu/'

        self.koinst._KitOps__db = dbs

        # Perform the deletion.
        self.koinst.deleteKit(kn)

        # Make sure everything went as planned.
        # Check kit no longer in database.
        kit = dbs.Kits.selectfirst_by(rname=kn)
        assert kit is None, "Kit '%s' not removed" % kn

        # Components are to be removed.
        comps = dbs.Components.select()
        for comp in comps:
            assert not comp.cname.startswith("component-%s" % kn), \
                "Component '%s' for kit '%s' not removed" % (comp.cname, kn)

        # Directory check.
        kits_dir = tmp_prefix / 'depot/kits'
        kit_dir_name = kits_dir / kn
        kit_dir_ver = kit_dir_name / kv
        kit_dir_arch = kit_dir_ver / ka
        assert kits_dir.exists(), 'Kits dir %s does not exist' % kits_dir
        assert not kit_dir_arch.exists(), \
                    'Kit arch dir %s still exists' % kit_dir_arch
        assert not kit_dir_ver.exists(), \
                    'Kit version dir %s still exists' % kit_dir_ver
        assert not kit_dir_name.exists(), \
                    'Kit dir %s still exists' % kit_dir_name

    def test_delete_kit_version(self):
        kn = 'kit1'
        kv = '1.0'
        ka = 'i386'
        create_mock_kit(kn, kv, ka)

        # Perform the deletion.
        self.koinst.deleteKit(kn, kv)

        # Make sure everything went as planned.
        # Check kit no longer in database.
        kit = dbs.Kits.selectfirst_by(rname=kn)
        assert kit is None, "Kit '%s' not removed" % kn

        # Components are to be removed.
        comps = dbs.Components.select()
        for comp in comps:
            assert not comp.cname.startswith("component-%s" % kn), \
                "Component '%s' for kit '%s' not removed" % (comp.cname, kn)

        # Directory check.
        kits_dir = tmp_prefix / 'depot/kits'
        kit_dir_name = tmp_prefix / ('depot/kits/%s' % kn)
        kit_dir_ver = kit_dir_name / kv
        kit_dir_arch = kit_dir_ver / ka
        assert kits_dir.exists(), 'Kits dir %s does not exist' % kits_dir
        assert not kit_dir_arch.exists(), \
                    'Kit arch dir %s still exists' % kit_dir_arch
        assert not kit_dir_ver.exists(), \
                    'Kit version dir %s still exists' % kit_dir_ver
        assert not kit_dir_name.exists(), \
                    'Kit dir %s still exists' % kit_dir_name

    def test_delete_kit_version_arch(self):
        kn = 'kit1'
        kv = '1.0'
        ka = 'i386'
        create_mock_kit(kn, kv, ka)

        # Perform the deletion.
        self.koinst.deleteKit(kn, kv, ka)

        # Make sure everything went as planned.
        # Check kit no longer in database.
        kit = dbs.Kits.selectfirst_by(rname=kn)
        assert kit is None, "Kit '%s' not removed" % kn

        # Components are to be removed.
        comps = dbs.Components.select()
        for comp in comps:
            assert not comp.cname.startswith("component-%s" % kn), \
                "Component '%s' for kit '%s' not removed" % (comp.cname, kn)

        # Directory check.
        kits_dir = tmp_prefix / 'depot/kits'
        kit_dir_name = tmp_prefix / ('depot/kits/%s' % kn)
        kit_dir_ver = kit_dir_name / kv
        kit_dir_arch = kit_dir_ver / ka
        assert kits_dir.exists(), 'Kits dir %s does not exist' % kits_dir
        assert not kit_dir_arch.exists(), \
                    'Kit arch dir %s still exists' % kit_dir_arch
        assert not kit_dir_ver.exists(), \
                    'Kit version dir %s still exists' % kit_dir_ver
        assert not kit_dir_name.exists(), \
                    'Kit dir %s still exists' % kit_dir_name

    def test_delete_kit_multiple(self):
        kn = 'kit1'
        kv = '1.0'
        kv2 = '1.1'
        ka = 'i386'
        ka2 = 'x86_64'
        create_mock_kit(kn, kv, ka)
        create_mock_kit(kn, kv, ka2)
        create_mock_kit(kn, kv2, ka2)

        # Perform the deletion.
        self.koinst.deleteKit(kn)

        # Make sure everything went as planned.
        # Check kit no longer in database.
        kit = dbs.Kits.selectfirst_by(rname=kn)
        assert kit is None, "Kit '%s' not removed" % kn

        # Components are to be removed.
        comps = dbs.Components.select()
        for comp in comps:
            assert not comp.cname.startswith("component-%s" % kn), \
                "Component '%s' for kit '%s' not removed" % (comp.cname, kn)

        # Directory check.
        kits_dir = tmp_prefix / 'depot/kits'
        kit_dir_name = tmp_prefix / ('depot/kits/%s' % kn)
        kit_dir_ver = kit_dir_name / kv
        kit_dir_arch = kit_dir_ver / ka
        assert kits_dir.exists(), 'Kits dir %s does not exist' % kits_dir
        assert not kit_dir_arch.exists(), \
                    'Kit arch dir %s still exists' % kit_dir_arch
        assert not kit_dir_ver.exists(), \
                    'Kit version dir %s still exists' % kit_dir_ver
        assert not kit_dir_name.exists(), \
                    'Kit dir %s still exists' % kit_dir_name

    def test_delete_kit_version_multiple(self):
        kn = 'kit1'
        kn2 = 'kit2'
        kv = '1.0'
        kv2 = '1.1'
        ka = 'i386'
        ka2 = 'x86_64'
        create_mock_kit(kn, kv, ka)
        create_mock_kit(kn, kv, ka2)
        create_mock_kit(kn, kv2, ka2)

        # Perform the deletion.
        self.koinst.deleteKit(kn, kv)

        # Make sure everything went as planned.
        # Check kit no longer in database.
        kit = dbs.Kits.selectfirst_by(rname=kn, version=kv)
        assert kit is None, "Kits '%s-%s' not removed" % (kn, kv)

        # Also check other kit still in the database.
        kit = dbs.Kits.selectfirst_by(rname=kn, version=kv2)
        assert kit is not None, "Kit '%s-%s' removed" % (kn, kv2)

        # Components are to be removed.
        comps = dbs.Components.select()
        klong = '%s-%s' % (kn, kv)
        for comp in comps:
            assert not comp.cname.startswith("component-%s" % klong), \
                "Component '%s' for kit '%s' not removed" % (comp.cname, kn)

        # Directory check.
        kits_dir = tmp_prefix / 'depot/kits'
        kit_dir_name = tmp_prefix / ('depot/kits/%s' % kn)
        kit_dir_ver = kit_dir_name / kv
        kit_dir_arch = kit_dir_ver / ka
        assert kits_dir.exists(), 'Kits dir %s does not exist' % kits_dir
        assert not kit_dir_arch.exists(), \
                    'Kit arch dir %s still exists' % kit_dir_arch
        assert not kit_dir_ver.exists(), \
                    'Kit version dir %s still exists' % kit_dir_ver
        assert kit_dir_name.exists(), \
                    'Kit dir %s does not exist' % kit_dir_name

        kit_dir_name = tmp_prefix / ('depot/kits/%s' % kn)
        kit_dir_ver = kit_dir_name / kv2
        kit_dir_arch = kit_dir_ver / ka2
        assert kit_dir_arch.exists(), \
                    'Kit arch dir %s does not exist' % kit_dir_arch
        assert kit_dir_ver.exists(), \
                    'Kit version dir %s does not exist' % kit_dir_ver
        assert kit_dir_name.exists(), \
                    'Kit dir %s does not exist' % kit_dir_name

    def test_delete_kit_version_arch_multiple(self):
        kn = 'kit1'
        kv = '1.0'
        kv2 = '1.1'
        ka = 'i386'
        ka2 = 'x86_64'
        create_mock_kit(kn, kv, ka)
        create_mock_kit(kn, kv, ka2)
        create_mock_kit(kn, kv2, ka2)

        # Perform the deletion.
        self.koinst.deleteKit(kn, kv, ka)

        # Make sure everything went as planned.
        # Check kit no longer in database.
        kit = dbs.Kits.selectfirst_by(rname=kn, version=kv, arch=ka)
        assert kit is None, "Kit '%s-%s-%s' not removed" % (kn, kv, ka)

        # Also check other kit still in the database.
        kit = dbs.Kits.selectfirst_by(rname=kn, version=kv, arch=ka2)
        assert kit is not None, "Kit '%s-%s-%s' removed" % (kn, kv, ka2)
        kit = dbs.Kits.selectfirst_by(rname=kn, version=kv2, arch=ka2)
        assert kit is not None, "Kit '%s-%s-%s' removed" % (kn, kv2, ka2)

        # Components are to be removed.
        comps = dbs.Components.select()
        klong = '%s-%s-%s' % (kn, kv, ka)
        for comp in comps:
            assert not comp.cname.startswith("component-%s" % klong), \
                "Component '%s' for kit '%s' not removed" % (comp.cname, kn)

        # Directory check.
        kits_dir = tmp_prefix / 'depot/kits'
        kit_dir_name = tmp_prefix / ('depot/kits/%s' % kn)
        kit_dir_ver = kit_dir_name / kv
        kit_dir_arch = kit_dir_ver / ka
        assert kits_dir.exists(), 'Kits dir %s does not exist' % kits_dir
        assert not kit_dir_arch.exists(), \
                    'Kit arch dir %s still exists' % kit_dir_arch
        assert kit_dir_ver.exists(), \
                    'Kit version dir %s does not exist' % kit_dir_ver
        assert kit_dir_name.exists(), \
                    'Kit dir %s does not exist' % kit_dir_name

        # Perform another deletion.
        self.koinst.deleteKit(kn, kv2, ka2)

        # Make sure everything went as planned.
        # Check kit no longer in the database.
        kit = dbs.Kits.selectfirst_by(rname=kn, version=kv2, arch=ka2)
        assert kit is None, "Kit '%s-%s-%s' not removed" % (kn, kv2, ka2)

        # Also check other kit still in the database.
        kit = dbs.Kits.selectfirst_by(rname=kn, version=kv, arch=ka2)
        assert kit is not None, "Kit '%s-%s-%s' removed" % (kn, kv, ka2)

        # Components are to be removed.
        comps = dbs.Components.select()
        klong = '%s-%s-%s' % (kn, kv2, ka2)
        for comp in comps:
            assert not comp.cname.startswith("component-%s" % klong), \
                "Component '%s' for kit '%s' not removed" % (comp.cname, kn)

        # Directory check.
        kits_dir = tmp_prefix / 'depot/kits'
        kit_dir_name = tmp_prefix / ('depot/kits/%s' % kn)
        kit_dir_ver = kit_dir_name / kv2
        kit_dir_arch = kit_dir_ver / ka2
        assert kits_dir.exists(), 'Kits dir %s does not exist' % kits_dir
        assert not kit_dir_arch.exists(), \
                    'Kit arch dir %s still exists' % kit_dir_arch
        assert not kit_dir_ver.exists(), \
                    'Kit version dir %s still exists' % kit_dir_ver
        assert kit_dir_name.exists(), \
                    'Kit dir %s does not exist' % kit_dir_name

def create_mock_kit(kn, kv, ka):
    assert kn is not None and kv is not None and ka is not None, \
        "Don't pass None into this function! Thank you."

    # Create the kit.
    kit = dbs.Kits(rname=kn, rdesc="Kit '%s'" % kn, version=kv,
                   isOS=False, removable=True, arch=ka)
    kit.save()
    kit.flush()

    # Create some components for the kit.
    klong = '%s-%s-%s' % (kn, kv, ka)
    for x in xrange(2):
        comp = dbs.Components(kid=kit.kid,
                              cname="component-%s-%d" % (klong, x),
                              cdesc="Component %d for kit '%s'" % (x, klong))
        comp.save()
        comp.flush()

    # Create the kit directory and put a file inside.
    kit_dir = tmp_prefix / ('depot/kits/%s/%s/%s' % (kn, kv, ka))
    if not kit_dir.exists():
        kit_dir.makedirs()

    (kit_dir / 'kitinfo').touch()

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
