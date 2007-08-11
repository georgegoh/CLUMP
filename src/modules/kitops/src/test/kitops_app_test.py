#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#

import os
import tempfile
import urllib
from path import path
from nose import SkipTest

try:
    import subprocess
except:
    from popen5 import subprocess

import kusu.core.database as db
from kusu.kitops.kitops import KitOps

# NOTE: test_kits_url NEEDS a trailing slash
test_kits_url = 'http://www.osgdc.org/pub/build/tests/modules/kitops/'
tmp_prefix = path(os.environ.get('KUSU_TMP', '/tmp'))
test_kits_path = tmp_prefix / 'kitops_test_isos'

temp_root = None
temp_mount = None
kusudb = None
db_driver = 'sqlite' # set to one of 'mysql' 'sqlite'
dbinfo_str = ''

def setUp():
    global temp_root
    global temp_mount
    global tmp_prefix

    databasePrep()

    if not tmp_prefix.exists():
        tmp_prefix.mkdir()

    temp_root = path(tempfile.mkdtemp(prefix='kot', dir=tmp_prefix))
    temp_mount = path(tempfile.mkdtemp(prefix='kot', dir=tmp_prefix))

def tearDown():
    global temp_root
    global temp_mount

    databaseCleanup()

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

        self.kit_iso = 'mock-kit-base-0.1-1.noarch.iso'
        downloadFiles(self.kit_iso)

        self.kit = test_kits_path / self.kit_iso
        self.kit_rpm = 'kit-base-0.1-0.noarch.rpm'
        self.kit_name = 'base'
        self.kit_ver = '0.1'
        self.kit_arch = 'noarch'
        self.kits_dir_name = self.kits_dir / self.kit_name
        self.kits_dir_ver = self.kits_dir_name / self.kit_ver
        self.kits_dir_arch = self.kits_dir_ver / self.kit_arch

        assert self.kit.exists(), 'Base kit ISO does not exist!'

        self.kusudb = kusudb
        self.kusudb.createTables()
        self.kusudb.bootstrap()

        mountP = subprocess.Popen('mount -o loop %s %s 2> /dev/null' %
                                  (self.kit, self.temp_mount), shell=True)
        mountP.wait()

    def tearDown(self):
        self.kusudb.flush()
        self.kusudb.dropTables()

        # wipe out installed files
        if self.depot_dir.exists():
            self.depot_dir.rmtree()

        umountP = subprocess.Popen('umount %s 2> /dev/null' % self.temp_mount,
                                   shell=True)
        umountP.wait()

    def testAddKit(self):
        # we need to be root
        assertRoot()

        addP = subprocess.Popen('kitops -a -m %s %s -p %s' %
                                (self.kit, dbinfo_str, self.temp_root),
                                shell=True)
        rv = addP.wait()

        assert rv == 0, 'kitops returned error: %s' % rv

        # verify the kit RPM is installed
        rpm_installed = isRPMInstalled('kit-' + self.kit_name)
        if rpm_installed:
            # clean up after this test
            rpmP = subprocess.Popen('rpm --quiet -e --nodeps kit-%s' %
                                    self.kit_name, shell=True)

        assert  rpm_installed, 'RPM kit-%s is not installed' % self.kit_name

        # assert all directories exist
        assert self.depot_dir.exists(), \
               'Depot dir %s does not exist' % self.depot_dir
        assert self.kits_dir.exists(), \
               'Kits dir %s does not exist' % self.kits_dir
        assert self.kits_dir_name.exists(), \
               'Kit dir %s does not exist' % self.kits_dir_name
        assert self.kits_dir_ver.exists(), \
               'Kit ver dir %s does not exist' % self.kits_dir_ver
        assert self.kits_dir_arch.exists(), \
               'Kit ver dir %s does not exist' % self.kits_dir_arch

        # assert contents are the same
        assert areContentsEqual(self.temp_mount / self.kit_name,
                                self.kits_dir_arch, '*.rpm'), \
               'RPM files in %s and %s are not equal' % \
               (self.temp_mount / self.kit_name, self.kits_dir_arch)

        # check DB for information
        kits = self.kusudb.Kits.select()
        
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
        assert kit.arch == self.kit_arch, \
               'Arch: %s, expected: %s' % (kit.arch, self.kit_arch)

        # the base kit has two components
        cmps = self.kusudb.Components.select()
        assert len(cmps) == 2, 'Components in DB: %d, expected: 2' % len(cmps)

        # check component data
        cmp = self.kusudb.Components.selectfirst_by(cname='component-base-node')
        assert cmp.kid == kit.kid, 'Component not linked to kit by kid'
        assert cmp.cname == 'component-base-node', \
               'Component name: %s, expected: component-base-node' % cmp.cname
        assert cmp.cdesc == 'Component for Kusu Node Base', \
               'Component description: ' + \
               '%s, expected: Component for Kusu Node Base' % cmp.cdesc
        assert cmp.os == '', 'OS: %s, expected empty string' % cmp.os
        # node component associated only with compute nodegroup
        assert len(cmp.nodegroups) != 0, \
            'Component %s not associated with any nodegroups' % cmp.cname
        for ng in cmp.nodegroups:
            assert ng.type == 'compute' or ng.type == 'installer', \
                'Component %s ' % cmp.cname + \
                'associated with nodegroup %s, ' % ng.ngname + \
                "type %s; expecting 'installer' or 'compute' type" % ng.type

        cmp = self.kusudb.Components.selectfirst_by(
                                            cname='component-base-installer')
        assert cmp.kid == kit.kid, 'Component not linked to kit by kid'
        assert cmp.cname == 'component-base-installer', \
               'Component name: %s, ' % cmp.cname + \
               'expected: component-base-installer'
        assert cmp.cdesc == 'Component for Kusu Installer Base', \
           'Component description: ' + \
           '%s, expected: Component for Kusu Installer Base' % cmp.cname
        assert cmp.os == '', 'OS: %s, expected empty string' % cmp.os
        # node component associated only with installer nodegroup
        assert len(cmp.nodegroups) == 1, \
            'Component %s associated with more than one nodegroup' % cmp.cname
        assert cmp.nodegroups[0].ngname == 'installer', \
            'Component %s not associated with installer nodegroup' % cmp.cname

        # kit stored in packages table
        ngs = self.kusudb.NodeGroups.select()
        for ng in ngs:
            if ng.type == 'installer':
                for pkg in ng.packages:
                    assert pkg.packagename == 'kit-base', \
                                'Package associated with %s ' % ng.ngname + \
                                'nodegroup is %s, ' % pkg.packagename + \
                                'expected kit-base'
            else:
                for pkg in ng.packages:
                    assert pkg.packagename != 'kit-base', \
                                   'kit-base package associated ' \
                                   'with %s nodegroup' % ng.ngname

    def testDeleteKit(self):
        # we need to be root
        assertRoot()

        # perform database setup
        self.prepareDatabase()

        # copy RPM files
        if not self.kits_dir_arch.exists():
            self.kits_dir_arch.makedirs()
            
        srcP = subprocess.Popen('tar cf - --exclude %s *.rpm' % self.kit_rpm,
                                cwd=self.temp_mount / self.kit_name,
                                shell=True, stdout=subprocess.PIPE)
        dstP = subprocess.Popen('tar xf -', cwd=self.kits_dir_arch, shell=True,
                                stdin=srcP.stdout)
        dstP.communicate()

        # install kit RPM
        rpmP = subprocess.Popen('rpm --quiet -i %s' % self.kit_rpm,
                                cwd=self.temp_mount / self.kit_name, shell=True)
        rpmP.wait()

        assert isRPMInstalled('kit-' + self.kit_name), 'Need RPM installed'

        # remove the kit using kitops
        addP = subprocess.Popen('kitops -e --kitname %s %s -p %s' %
                                (self.kit_name, dbinfo_str, self.temp_root),
                                shell=True)
        rv = addP.wait()

        assert rv == 0, 'kitops returned error: %s' % rv

        # assert database entries removed
        kits = self.kusudb.Kits.select()
        assert len(kits) == 0, 'Kits still remain in the DB'
        
        cmps = self.kusudb.Components.select()
        assert len(cmps) == 0, 'Components still remain in the DB'

        pkgs = self.kusudb.Packages.select_by(packagename = 'kit-' + self.kit_name)
        assert len(pkgs) == 0, 'Packages still remain in the DB'

        ng_has_comps = self.kusudb.NGHasComp.select()
        assert len(ng_has_comps) == 0, \
                   'Nodegroups have components still remain in DB'

        ngs = self.kusudb.NodeGroups.select()
        for ng in ngs:
            assert len(ng.components) == 0, \
                'Nodegroup %s still has %s component(s)' % (ng.ngname,
                                                            len(ng.components))
            #assert len(ng.packages) == 0, \
            #    'Nodegroup %s still has %s package(s)' % (ng.ngname,
            #                                              len(ng.packages))

        # assert files erased
        assert not self.kits_dir_arch.exists(), \
                    'Kit arch dir %s still exists' % self.kits_dir_arch
        assert not self.kits_dir_ver.exists(), \
                    'Kit version dir %s still exists' % self.kits_dir_ver
        assert not self.kits_dir_name.exists(), \
                    'Kit dir %s still exists' % self.kits_dir_name

        # assert RPM removed
        assert not isRPMInstalled('kit-' + self.kit_name), \
                   'RPM kit-%s is still installed' % self.kit_name

    def testListKits(self):
        assertRoot()

        # first, test listing nothing
        lines = listKits()
        wantlines = ['+-----+-------------+---------+--------------+-------' + \
                     '-+-----------+-------------+',
                     '| Kit | Description | Version | Architecture | OS Kit' + \
                     ' | Removable | Node Groups |',
                     '+-----+-------------+---------+--------------+-------' + \
                     '-+-----------+-------------+',
                     '+-----+-------------+---------+--------------+-------' + \
                     '-+-----------+-------------+']
        assert lines == wantlines, 'List error! ' + \
            'Received:\n%s\nExpected:\n%s\n' % ('\n'.join(lines),
                                                '\n'.join(wantlines))

        # perform database setup
        self.prepareDatabase()

        lines = listKits()
        wantlines = ['+------+-------------+---------+--------------+------' + \
                     '--+-----------+-------------+',
                     '| Kit  | Description | Version | Architecture | OS Ki' + \
                     't | Removable | Node Groups |',
                     '+------+-------------+---------+--------------+------' + \
                     '--+-----------+-------------+',
                     '| base | Base Kit    | 0.1     | noarch       | No   ' + \
                     '  | Yes       | installer   |',
                     '|      |             |         |              |      ' + \
                     '  |           | compute     |',
                     '+------+-------------+---------+--------------+------' + \
                     '--+-----------+-------------+']

        assert lines == wantlines, 'List error! ' + \
            'Received:\n%s\nExpected:\n%s\n' % ('\n'.join(lines),
                                                '\n'.join(wantlines))

        new_arch = 'x86_64'
        new_isOS = True
        new_removable = False

        kit = self.kusudb.Kits.selectfirst_by(rname='base')
        kit.arch = new_arch
        kit.isOS = new_isOS
        kit.removable = new_removable
        self.kusudb.flush()

        lines = listKits()
        wantlines = ['+------+-------------+---------+--------------+------' + \
                     '--+-----------+-------------+',
                     '| Kit  | Description | Version | Architecture | OS Ki' + \
                     't | Removable | Node Groups |',
                     '+------+-------------+---------+--------------+------' + \
                     '--+-----------+-------------+',
                     '| base | Base Kit    | 0.1     | x86_64       | Yes  ' + \
                     '  | No        | installer   |',
                     '|      |             |         |              |      ' + \
                     '  |           | compute     |',
                     '+------+-------------+---------+--------------+------' + \
                     '--+-----------+-------------+']

        assert lines == wantlines, 'List error! ' + \
            'Received:\n%s\nExpected:\n%s\n' % ('\n'.join(lines),
                                                '\n'.join(wantlines))

        lines = listKits('lsf')
        wantlines = ['+-----+-------------+---------+--------------+-------' + \
                     '-+-----------+-------------+',
                     '| Kit | Description | Version | Architecture | OS Kit' + \
                     ' | Removable | Node Groups |',
                     '+-----+-------------+---------+--------------+-------' + \
                     '-+-----------+-------------+',
                     '+-----+-------------+---------+--------------+-------' + \
                     '-+-----------+-------------+']
        assert lines == wantlines, 'List error! ' + \
            'Received:\n%s\nExpected:\n%s\n' % ('\n'.join(lines),
                                                '\n'.join(wantlines))

    def prepareDatabase(self):
        # insert data into DB
        # create a new kit with removable set to True
        newkit = self.kusudb.Kits(rname=self.kit_name, rdesc='Base Kit',
                                  version='0.1', isOS=False, removable=True)
        component_node = self.kusudb.Components(cname='component-base-node',
                                        cdesc='Component for Kusu Node Base')
        component_installer = self.kusudb.Components(
                                    cname='component-base-installer',
                                    cdesc='Component for Kusu Installer Base')

        newkit.components.append(component_node)
        newkit.components.append(component_installer)

        ng = self.kusudb.NodeGroups.selectfirst_by(ngname='compute')
        ng.components.append(component_node)

        ng = self.kusudb.NodeGroups.selectfirst_by(ngname='installer')
        ng.components.append(component_installer)
        ng.packages.append(self.kusudb.Packages(packagename='kit-base'))

        newkit.save()
        self.kusudb.flush()

        # drop this session, start with new untainted session when asserting
        self.kusudb.ctx.del_current()

class TestMetaKit:
    def setUp(self):
        global temp_root
        global temp_mount
        global kusudb

        self.temp_root = temp_root
        self.temp_mount = temp_mount
        self.depot_dir = self.temp_root / 'depot'
        self.kits_dir = self.depot_dir / 'kits'

        self.kit_iso = 'mock-kit-chipmunks-0.1-0.noarch.iso'
        downloadFiles(self.kit_iso)

        self.kit = test_kits_path / self.kit_iso
        
        self.kit_members = 3
        self.kit_rpms = ['kit-alvin-0.1-0.i386.rpm',
                         'kit-simon-0.1-0.i386.rpm',
                         'kit-theodore-0.1-0.i386.rpm']
        self.kit_names = ['alvin', 'simon', 'theodore']
        self.kit_ver = '0.1'
        self.kit_arch = 'noarch'
        self.kits_dir_names = [self.kits_dir / name for name in self.kit_names]
        self.kits_dir_vers = \
            [dirname / self.kit_ver for dirname in self.kits_dir_names]
        self.kits_dir_archs = \
            [dirver / self.kit_arch for dirver in self.kits_dir_vers]

        assert self.kit.exists(), 'Chipmunk kit ISO does not exist!'

        self.kusudb = kusudb
        self.kusudb.createTables()
        self.kusudb.bootstrap()

        mountP = subprocess.Popen('mount -o loop %s %s 2> /dev/null' %
                                  (self.kit, self.temp_mount), shell=True)
        mountP.wait()

    def tearDown(self):
        self.kusudb.flush()
        self.kusudb.dropTables()

        # wipe out installed files
        if self.depot_dir.exists():
            self.depot_dir.rmtree()

        umountP = subprocess.Popen('umount %s 2> /dev/null' % self.temp_mount,
                                   shell=True)
        umountP.wait()

    def testAddMetaKit(self):
        # we need to be root
        assertRoot()

        addP = subprocess.Popen('kitops -a -m %s %s -p %s' %
                                (self.kit, dbinfo_str, self.temp_root),
                                shell=True)
        rv = addP.wait()

        assert rv == 0, 'kitops returned error: %s' % rv

        rpms = {}
        for x in xrange(self.kit_members):
            kitname = self.kit_names[x]
            # verify the kit RPM is installed
            rpm_installed = isRPMInstalled('kit-' + kitname)
            rpms[self.kit_names[x]] = rpm_installed
            if rpm_installed:
                # clean up after this test
                rpmP = subprocess.Popen('rpm --quiet -e --nodeps kit-%s' %
                                        kitname, shell=True)

        for x in xrange(self.kit_members):
            assert rpms[self.kit_names[x]], \
                'RPM kit-%s is not installed' % self.kit_names[x]

        # assert all directories exist
        assert self.depot_dir.exists(), \
               'Depot dir %s does not exist' % self.depot_dir
        assert self.kits_dir.exists(), \
               'Kits dir %s does not exist' % self.kits_dir
        for x in xrange(self.kit_members):
            assert self.kits_dir_names[x].exists(), \
                   'Kit dir %s does not exist' % self.kits_dir_names[x]
            assert self.kits_dir_vers[x].exists(), \
                   'Kit ver dir %s does not exist' % self.kits_dir_vers[x]
            assert self.kits_dir_archs[x].exists(), \
                   'Kit ver dir %s does not exist' % self.kits_dir_archs[x]

        # assert contents are the same
        for x in xrange(self.kit_members):
            assert areContentsEqual(self.temp_mount / self.kit_names[x],
                                    self.kits_dir_archs[x], '*.rpm'), \
                   'RPM files in %s and %s are not equal' % \
                   (self.temp_mount / self.kit_names[x], self.kits_dir_archs[x])

        # check DB for information
        kits = self.kusudb.Kits.select()
        
        # we are expecting only one kit
        assert len(kits) == self.kit_members, \
            'Kits in DB: %d, expected: %d' % (len(kits), self.kit_members)

        # check the kit's data
        for x in xrange(self.kit_members):
            kitname = self.kit_names[x]
            kit = kits[x]
            assert kit.rname == kitname, \
                   'Kit name: %s, expected %s' % (kit.rname, kitname)
            assert kit.rdesc == '%s kit.' % kitname, \
                   'Description: %s, expected: %s kit.' % (kit.rdesc, kitname)
            assert kit.version == '0.1', \
                   'Version: %s, expected: 0.1' % kit.version
            assert not kit.isOS, \
                   'Expected isOS to be False for kit %s' % kitname
            assert not kit.removable, 'Expected removable to be False ' + \
                   'for kit %s' % kitname
            assert kit.arch == self.kit_arch, \
                   'Arch: %s, expected: %s' % (kit.arch, self.kit_arch)

        # each kit has one component
        cmps = self.kusudb.Components.select()
        assert len(cmps) == self.kit_members, \
            'Components in DB: %d, expected: %d' % (len(cmps), self.kit_members)

        # check component data
        for x in xrange(self.kit_members):
            kitname = self.kit_names[x]
            cmp = self.kusudb.Components.selectfirst_by(
                            cname='component-%s' % kitname)
            assert cmp.kid == kits[x].kid, \
                'Component component-%s ' % kitname + \
                'not linked to kit by kid'
            assert cmp.cname == 'component-%s' % kitname, \
                   'Component name: %s, ' % cmp.cname + \
                   'expected: component-%s' % kitname
            assert cmp.cdesc == '%s component for Fedora Core 6.' % kitname, \
                   'Component description: ' + \
                   '%s, expected: ' % cmp.cdesc + \
                   '%s component for Fedora Core 6.' % kitname
            assert cmp.os == 'fedora', 'OS: %s, expected: fedora' % cmp.os
            # node component associated only with compute nodegroup
            assert len(cmp.nodegroups) != 0, \
                'Component %s not associated with any nodegroups' % cmp.cname

            if kitname == 'alvin':
                gotCompute = False
                gotInstaller = False

                for ng in cmp.nodegroups:
                    if ng.type == 'compute': gotCompute = True
                    if ng.type == 'installer': gotInstaller = True

                assert gotCompute, 'Component %s ' % cmp.cname + \
                    'not associated with any compute type nodegroup'
                assert gotInstaller, 'Component %s ' % cmp.cname + \
                    'not associated with any installer type nodegroup'
            elif kitname == 'simon':
                gotInstaller = False
                
                for ng in cmp.nodegroups:
                    if ng.type == 'installer': gotInstaller = True

                assert gotInstaller, 'Component %s ' % cmp.cname + \
                    'not associated with any installer type nodegroup'
            elif kitname == 'theodore':
                gotCompute = False
                
                for ng in cmp.nodegroups:
                    if ng.type == 'compute': gotCompute = True

                assert gotInstaller, 'Component %s ' % cmp.cname + \
                    'not associated with any compute type nodegroup'

        # kit stored in packages table
        ngs = self.kusudb.NodeGroups.select()
        for ng in ngs:
            if ng.type == 'installer':
                for pkg in ng.packages:
                    match = False
                    for x in xrange(self.kit_members):
                        kitname = self.kit_names[x]
                        if pkg.packagename == 'kit-%s' % kitname:
                            match = True
                            break
                        
                    assert match, 'Package %s not ' % pkg.packagename + \
                            'assciated with with %s nodegroup' % ng.ngname
            else:
                for pkg in ng.packages:
                    for x in xrange(self.kit_members):
                        kitname = self.kit_names[x]
                        assert pkg.packagename != 'kit-%s' % kitname, \
                           'kit-%s package associated ' % kitname + \
                           'with %s nodegroup' % ng.ngname

class TestFedoraCore6i386:
    def setUp(self):
        global temp_root
        global temp_mount
        global kusudb

        self.temp_root = temp_root
        self.temp_mount = temp_mount
        self.depot_dir = self.temp_root / 'depot'
        self.kits_dir = self.depot_dir / 'kits'
        self.pxe_dir = self.temp_root / 'tftpboot/kusu'

        self.kit_iso1 = 'mock-FC-6-i386-disc1.iso' 
        self.kit_iso2 = 'mock-FC-6-i386-disc2.iso' 
        self.kit1 = test_kits_path / self.kit_iso1
        self.kit2 = test_kits_path / self.kit_iso2
        if not self.kit1.exists():
            downloadFiles(self.kit_iso1)
        if not self.kit2.exists():
            downloadFiles(self.kit_iso2)

        self.kit_name = 'fedora'
        self.kit_ver = '6'
        self.kit_arch = 'i386'
        self.kit_longname = '%s-%s-%s' % \
                                (self.kit_name, self.kit_ver, self.kit_arch)
        self.kit_initrd = self.pxe_dir / ('initrd-%s.img' % self.kit_longname)
        self.kit_kernel = self.pxe_dir / ('kernel-%s' % self.kit_longname)
        self.kits_dir_name = self.kits_dir / self.kit_name
        self.kits_dir_ver = self.kits_dir_name / self.kit_ver
        self.kits_dir_arch = self.kits_dir_ver / self.kit_arch

        assert self.kit1.exists(), 'Fedora Core 6 i386 CD1 ISO does not exist!'
        assert self.kit2.exists(), 'Fedora Core 6 i386 CD2 ISO does not exist!'

        self.kusudb = kusudb
        self.kusudb.createTables()
        self.kusudb.bootstrap()

        mountP = subprocess.Popen('mount -o loop %s %s 2> /dev/null' %
                                  (self.kit1, self.temp_mount), shell=True)
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

    def testAddKitOneDisc(self):
        # we need to be root
        assertRoot()

        # passing "N" to kitops to stop at one disc
        add_echo = "N"
        addP = subprocess.Popen('echo "%s" | ' % add_echo +
                                'kitops -a -m %s %s -p %s &> /dev/null' %
                                (self.kit1, dbinfo_str, self.temp_root),
                                shell=True)
        rv = addP.wait()

        assert rv == 0, 'kitops returned error: %s' % rv

        self.assertOSKitDirs()

        # assert contents are the same
        assert areDirTreesIdentical(self.temp_mount, self.kits_dir_arch), \
               'Directory trees %s and %s are not equal' % \
               (self.temp_mount, self.kits_dir_arch)

        self.assertOSKitDBInfo()

    def testAddKitTwoDiscs(self):
        # we need to be root
        assertRoot()

        # passing disc 2 to kitops
        add_echo = "y\n%s\nN" % self.kit2
        addP = subprocess.Popen('echo "%s" | ' % add_echo +
                                'kitops -a -m %s %s -p %s &> /dev/null' %
                                (self.kit1, dbinfo_str, self.temp_root),
                                shell=True)
        rv = addP.wait()

        assert rv == 0, 'kitops returned error: %s' % rv

        self.assertOSKitDirs()

        # the two discs contain more than 1000 files when combined
        files = len([f for f in path(self.kits_dir / self.kit_name).walk()])
        assert files >= 1000, 'Found %d files, expecting more than 1000' % files

        self.assertOSKitDBInfo()

    def assertOSKitDirs(self):
        # assert all directories exist
        assert self.depot_dir.exists(), \
               'Depot dir %s does not exist' % self.depot_dir
        assert self.kits_dir.exists(), \
               'Kits dir %s does not exist' % self.kits_dir
        assert self.kits_dir_name.exists(), \
               'Kit dir %s does not exist' % self.kits_dir_name
        assert self.kits_dir_ver.exists(), \
               'Kit ver dir %s does not exist' % self.kits_dir_ver
        assert self.kits_dir_arch.exists(), \
               'Kit arch dir %s does not exist' % self.kits_dir_arch
        assert self.pxe_dir.exists(), \
               'PXE boot dir %s does not exist' % self.pxe_dir

        # also assert the initrd and kernel are copied
        assert self.kit_initrd.exists(), \
               'Initrd %s does not exist' % self.kit_initrd
        assert self.kit_kernel.exists(), \
               'Kernel %s does not exist' % self.kit_kernel

    def assertOSKitDBInfo(self):
        # check DB for information
        kits = self.kusudb.Kits.select()
        
        # we are expecting only one kit
        assert len(kits) == 1, 'Kits in DB: %d, expected: 1' % len(kits)

        # check the kit's data
        kit = kits[0]
        assert kit.rname == self.kit_name, \
               'Kit name: %s, expected %s' % (kit.rname, self.kit_name)
        assert kit.rdesc == 'OS kit for fedora 6 i386', \
               'Description: %s, expected: OS kit for fedora 6 i386' % kit.rdesc
        assert kit.version == '6', 'Version: %s, expected: 6' % kit.version
        assert kit.isOS, 'Expected isOS to be True'
        assert not kit.removable, 'Expected removable to be False'
        assert kit.arch == 'i386', 'Arch: %s, expected: i386' % kit.arch

        # the fedora 6 kit has one 'mock' component
        cmps = self.kusudb.Components.select()
        assert len(cmps) == 1, 'Components in DB: %d, expected: 1' % len(cmps)

        # check component data
        cmp = self.kusudb.Components.selectfirst_by(cname=self.kit_longname)
        assert cmp.kid == kit.kid, 'Component not linked to kit by kid'
        assert cmp.cname == self.kit_longname, \
               'Component name: %s, expected: %s' % \
               (cmp.cname, self.kit_longname)
        assert cmp.cdesc == '%s mock component' % self.kit_longname, \
               'Component description: %s, expected: %s mock component' % \
               (cmp.cname, self.kit_longname)
        # node component associated with all nodegroups
        assert len(cmp.nodegroups) == 4, \
            'Component %s not associated with two nodegroups' % cmp.cname
        ngnames = []
        for ng in cmp.nodegroups:
            ngnames.append(ng.ngname)
        ngnames.sort()
        assert ngnames[0] == 'compute', \
            'Component %s not associated with compute nodegroup' % cmp.cname
        assert ngnames[1] == 'compute-diskless', \
            'Component %s not associated with compute nodegroup' % cmp.cname
        assert ngnames[2] == 'compute-imaged', \
            'Component %s not associated with compute nodegroup' % cmp.cname
        assert ngnames[3] == 'installer', \
            'Component %s not associated with installer nodegroup' % cmp.cname

def listKits(name=''):
    ls_fd, ls_fn = tempfile.mkstemp(prefix='kot', dir=tmp_prefix)

    if name:
        name = '--kitname %s' % name
    lsP = subprocess.Popen('kitops -l %s %s -p %s' %
                           (name, dbinfo_str, temp_root),
                           shell=True, stdout=ls_fd)
    lsP.wait()

    ls_file = os.fdopen(ls_fd)
    ls_file.seek(0)
    lines = [line.strip() for line in ls_file.readlines()]
    ls_file.close()
    path(ls_fn).remove()

    return lines

def areDirTreesIdentical(s, d):
    """
    Compare contents of two directories and returns True if equal.

    Arguments:
    s -- source directory
    d -- destination directory
    """

    s_list = [f.abspath().replace(s.abspath() + '/', '') for f in s.walk()]
    d_list = [f.abspath().replace(d.abspath() + '/', '') for f in d.walk()]

    s_list.sort()
    d_list.sort()

    return s_list == d_list

def areContentsEqual(s, d, glob_pattern, omit=[]):
    """
    Compare contents of two directories and returns True if equal.

    Arguments:
    s -- source directory
    d -- destination directory
    glob_pattern -- pattern of files to look at (ie: if '*.rpm', ls *.rpm)
    omit -- files to ignore in comparison (ie: ls *.rpm | grep -v hi.rpm)
    """

    s_list = [f.basename() for f in s.glob(glob_pattern)]
    d_list = [f.basename() for f in d.glob(glob_pattern)]

    for item in omit:
        try:
            s_list.remove(item)
        except ValueError:
            pass

        # to ensure exception from s remove does not preempt d remove
        try:
            d_list.remove(item)
        except ValueError:
            pass

    s_list.sort()
    d_list.sort()

    return s_list == d_list

def isRPMInstalled(pattern):
    """
    Return True if RPM matching pattern is currently installed.
    """

    rpmP = subprocess.Popen('rpm -qa %s' % pattern, shell=True,
                            stdout=subprocess.PIPE)
    out, err = rpmP.communicate()

    return out != ''

def assertRoot():
    if os.getuid() != 0:
        raise SkipTest

def databasePrep():
    global dbinfo_str
    global kusudb

    if db_driver == 'mysql':
        dbinfo = ['mysql', 'kitops_test', 'root', '']
        dbinfo_str = \
                '--dbdriver=%s --dbdatabase=%s --dbuser=%s --dbpassword=%s' % \
                (dbinfo[0], dbinfo[1], dbinfo[2], dbinfo[3])
        kusudb = db.DB(dbinfo[0], dbinfo[1], dbinfo[2], dbinfo[3])
        kusudb.createDatabase()
    elif db_driver == 'sqlite':
        dbinfo = ['sqlite', '/tmp/kusu-test-kitops.db']
        dbinfo_str = '--dbdriver=%s --dbdatabase=%s' % (dbinfo[0], dbinfo[1])
        kusudb = db.DB(dbinfo[0], dbinfo[1])

def databaseCleanup():
    global kusudb

    if db_driver == 'mysql':
        kusudb.dropDatabase()
    elif db_driver == 'sqlite':
        try:
            os.unlink('/tmp/kusu-test-kitops.db')
        except:
            pass

def downloadFiles(fn):
    if not test_kits_path.exists():
        test_kits_path.makedirs()

    urllib.urlretrieve(test_kits_url + fn, test_kits_path / fn)
