#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import sys
if os.getuid() != 0:
    sys.exit("Test must be run as root.")

import tempfile
import subprocess
from path import path

import kusu.core.database as db
from kusu.kitops.kitops import KitOps

test_kits = path('/home/mike/kusudev/isos')
saved_kusu_root = None
temp_root = None
temp_mount = None
kusudb = None

def setUp():
    global saved_kusu_root
    global temp_root
    global temp_mount
    global kusudb

    saved_kusu_root = os.environ.get('KUSU_ROOT', None)
    temp_root = path(tempfile.mkdtemp(prefix='kot'))
    temp_mount = path(tempfile.mkdtemp(prefix='kot'))

    os.environ['KUSU_ROOT'] = str(temp_root)

    kusudb = db.DB('mysql', 'test', 'nobody')

def tearDown():
    global saved_kusu_root
    global temp_root

    if saved_kusu_root is not None:
        os.environ['KUSU_ROOT'] = saved_kusu_root

    temp_root.rmtree()
    temp_mount.rmtree()

class TestBaseKit:
    def setUp(self):
        global temp_root
        global temp_mount
        global kusudb

        self.temp_root = temp_root
        self.temp_mount = temp_mount
        self.depot_dir = self.temp_root / 'depot'
        self.kits_dir = self.depot_dir / 'kits'

        self.kit = test_kits / 'kit-base-0.1-0.noarch.iso'
        self.kit_rpm = 'kit-base-0.1-0.noarch.rpm'
        self.kit_name = 'base'
        self.kit_ver = '0.1'

        self.kusudb = kusudb
        self.kusudb.createTables()
        self.kusudb.bootstrap()
        self.dbs = self.kusudb.createSession()

        mountP = subprocess.Popen('mount -o loop %s %s 2> /dev/null' %
                                  (self.kit, self.temp_mount), shell=True)
        mountP.wait()

    def tearDown(self):
        # destroy the database
        kusudb.dropTables()

        # wipe out installed files
        if self.depot_dir.exists():
            self.depot_dir.rmtree()

        umountP = subprocess.Popen('umount %s 2> /dev/null' % self.temp_mount,
                                   shell=True)
        umountP.wait()

    def testAddKit(self):
        addP = subprocess.Popen('kitops -a -m %s' % self.kit, shell=True)
        rv = addP.wait()

        assert rv == 0, 'kitops returned error: %s' % rv

        # assert all directories exist
        assert self.depot_dir.exists(), \
               'Depot dir %s does not exist' % self.depot_dir
        assert self.kits_dir.exists(), \
               'Kits dir %s does not exist' % self.kits_dir
        assert path(self.kits_dir / self.kit_name).exists(), \
               'Kit dir %s does not exist' % self.kits_dir / self.kit_name
        assert path(self.kits_dir / self.kit_name / self.kit_ver).exists(), \
               'Kit ver dir %s does not exist' % self.kits_dir /  \
                                                 self.kit_name / self.kit_ver

        # assert contents are the same
        assert areContentsEqual(self.temp_mount / self.kit_name,
                                self.kits_dir / self.kit_name / self.kit_ver,
                                '*.rpm', [self.kit_rpm]), \
               'RPM files in %s and %s are not equal' % \
               (self.temp_mount / self.kit_name,
                self.kits_dir / self.kit_name / self.kit_ver)

        # check DB for information
        kits = self.dbs.query(self.kusudb.kits).select()
        
        # we are expecting only one kit
        assert len(kits) == 1, 'Kits in DB: %d, expected: 1' % len(kits)

        # check the kit's data
        kit = kits[0]
        assert kit.rname == self.kit_name, \
               'Kit name: %s, expected %s' % (kit.rname, self.kit_name)
        assert kit.rdesc == 'Base Kit', \
               'Description: %s, expected: Base Kit' % kit.rdesc
        assert kit.version == '0.1', 'Version: %s, expected: 0.1' % kit.version
        assert not kit.isOS, 'Expected isOS to be False'
        assert not kit.removable, 'Expected removable to be False'
        assert kit.arch == None, 'Arch: %s, expected: NULL/None' % kit.arch

        # the base kit has two components
        cmps = self.dbs.query(self.kusudb.components).select()
        assert len(cmps) == 2, 'Components in DB: %d, expected: 2' % len(cmps)

        # check component data
        cmp = self.dbs.query(self.kusudb.components).selectfirst_by(\
                                                        cname='base-node')
        assert cmp.kid == kit.kid, 'Component not linked to kit by kid'
        assert cmp.cname == 'base-node', \
               'Component name: %s, expected: base-node' % cmp.cname
        assert cmp.cdesc == 'Component for Kusu Node Base', \
               'Component name: %s, expected: Component for Kusu Node Base' % \
               cmp.cname
        assert cmp.os == None, 'OS: %s, expected: NULL/None' % cmp.os
        # node component associated only with compute nodegroup
        assert len(cmp.nodegroups) == 1, \
            'Component %s associated with more than one nodegroup' % cmp.cname
        assert cmp.nodegroups[0].ngname == 'compute', \
            'Component %s not associated with compute nodegroup' % cmp.cname

        cmp = self.dbs.query(self.kusudb.components).selectfirst_by(\
                                                        cname='base-installer')
        assert cmp.kid == kit.kid, 'Component not linked to kit by kid'
        assert cmp.cname == 'base-installer', \
               'Component name: %s, expected: base-installer' % cmp.cname
        assert cmp.cdesc == 'Component for Kusu Installer Base', \
           'Component name: %s, expected: Component for Kusu Installer Base' % \
               cmp.cname
        assert cmp.os == None, 'OS: %s, expected: NULL/None' % cmp.os
        # node component associated only with installer nodegroup
        assert len(cmp.nodegroups) == 1, \
            'Component %s associated with more than one nodegroup' % cmp.cname
        assert cmp.nodegroups[0].ngname == 'installer', \
            'Component %s not associated with installer nodegroup' % cmp.cname

        # verify the kit RPM is installed
        assert isRPMInstalled('kit-' + self.kit_name), \
               'RPM kit-%s is not installed' % self.kit_name

        # clean up after this test
        rpmP = subprocess.Popen('rpm --quiet -e --nodeps kit-%s' %
                                self.kit_name, shell=True)
        self.depot_dir.rmtree()

    def testDeleteKit(self):
        # insert data into DB
        # create a new kit with removable set to True
        newkit = db.Kits(rname=self.kit_name, rdesc='Base Kit', version='0.1',
                         isOS=False, removable=True)
        newkit.components.append(db.Components(cname='base-node',
                                    cdesc='Component for Kusu Node Base'))
        newkit.components.append(db.Components(cname='base-installer',
                                    cdesc='Component for Kusu Installer Base'))
        self.dbs.save(newkit)
        self.dbs.flush()

        cmp = self.dbs.query(self.kusudb.components).selectfirst_by(\
                                                        cname='base-node')
        ng = self.dbs.query(self.kusudb.nodegroups).selectfirst_by(\
                                                        ngname='compute')
        ng.components.append(cmp)

        cmp = self.dbs.query(self.kusudb.components).selectfirst_by(\
                                                        cname='base-installer')
        ng = self.dbs.query(self.kusudb.nodegroups).selectfirst_by(\
                                                        ngname='installer')
        ng.components.append(cmp)

        self.dbs.flush()

        # copy RPM files
        kit_dir = self.kits_dir / self.kit_name / self.kit_ver
        if not kit_dir.exists():
            kit_dir.makedirs()
            
        srcP = subprocess.Popen('tar cf - --exclude %s *.rpm' % self.kit_rpm,
                                cwd=self.temp_mount / self.kit_name,
                                shell=True, stdout=subprocess.PIPE)
        dstP = subprocess.Popen('tar xf -', cwd=kit_dir, shell=True,
                                stdin=srcP.stdout)
        dstP.communicate()

        # install kit RPM
        rpmP = subprocess.Popen('rpm --quiet -i %s' % self.kit_rpm,
                                cwd=self.temp_mount / self.kit_name, shell=True)
        rpmP.wait()

        # remove the kit using kitops
        addP = subprocess.Popen('kitops -e %s' % self.kit_name, shell=True)
        rv = addP.wait()

        assert rv == 0, 'kitops returned error: %s' % rv

        # assert database entries removed
        kits = self.dbs.query(self.kusudb.kits).select()
        assert len(kits) == 0, 'Kits still remain in the DB'
        
        cmps = self.dbs.query(self.kusudb.components).select()
        assert len(cmps) == 0, 'Components still remain in the DB'

        ng_has_comps = self.dbs.query(self.kusudb.ng_has_comp).select()
        assert len(ng_has_comps) == 0, \
                   'Nodegroups have components still remain in DB'

        # assert files erased
        assert not kit_dir.exists(), 'Kit ver dir %s still exists' % kit_dir

        # assert RPM removed
        assert not isRPMInstalled('kit-' + self.kit_name), \
                   'RPM kit-%s is still installed' % self.kit_name

    def testListKits(self):
        pass

def areContentsEqual(src, dest, glob_pattern, omit=[]):
    """
    Compare contents of two directories and returns True if equal.

    Arguments:
    src -- source directory
    dest -- destination directory
    glob_pattern -- pattern of files to look at (ie: if '*.rpm', ls *.rpm)
    omit -- files to ignore in comparison (ie: ls *.rpm | grep -v hi.rpm)
    """

    src_list = [f.basename() for f in src.glob(glob_pattern)]
    dest_list = [f.basename() for f in dest.glob(glob_pattern)]

    for item in omit:
        try:
            src_list.remove(item)
        except ValueError:
            pass

        # to ensure exception from src remove does not preempt dest remove
        try:
            dest_list.remove(item)
        except ValueError:
            pass

    return src_list.sort() == dest_list.sort()

def isRPMInstalled(pattern):
    """
    Return True if RPM matching pattern is currently installed.
    """

    tmp_fd, tmp_fn = tempfile.mkstemp()

    # run the command and store output in temp file
    rpmP = subprocess.Popen('rpm -qa %s' % pattern, shell=True, stdout=tmp_fd)
    rpmP.wait()

    tmp_fn = path(tmp_fn)
    tmp_size = tmp_fn.getsize() # will be zero if no output from rpmP

    os.close(tmp_fd)
    tmp_fn.remove()

    return tmp_size != 0
