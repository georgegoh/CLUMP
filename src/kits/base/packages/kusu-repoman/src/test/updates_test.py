#!/usr/bin/env python
# $Id: updates_test.py 476 2008-01-25 12:36:55Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from kusu.repoman.updates import BaseUpdate
from kusu.util import rpmtool
from kusu.util.tools import cpio_copytree
from kusu.util.testing import download

from path import path
import tempfile
import os
from nose import SkipTest

kusudb = None
prefix = None

def setUp():
    global kusudb
    global prefix
    global dbObj

    prefix = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP']))
    kusudb = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP'])) / 'kusu.db'
    dbObj = db.DB('sqlite', kusudb)

def tearDown():
    global kusudb
    global prefix

    kusudb.parent.rmtree()
    if prefix.exists(): prefix.rmtree()

class TestTool:
    def setUp(self):
        global prefix
        global dbObj

        if not prefix.exists():
            prefix.makedirs()
        
        self.dbs = dbObj
        self.dbs.bootstrap()
 
    def tearDown(self):
        global prefix
        self.dbs.dropTables()
        prefix.rmtree()

    def testNextReleaseNoKits(self):
        global prefix
    
        bu = BaseUpdate('fedora', '6', 'i386', prefix, self.dbs)
        release = bu.getNextRelease('fedora-updates')
        assert release == 1

    def testNextRelease(self):
        global prefix
        
        k = self.dbs.Kits(rname='fedora-updates', version='6_r100')
        k.save()
        k.flush()

        k = self.dbs.Kits(rname='fedora-updates', version='6_r105')
        k.save()
        k.flush()

        k = self.dbs.Kits(rname='fedora-updates', version='6_r102')
        k.save()
        k.flush()

        k = self.dbs.Kits(rname='fedora-updates', version='6_r65')
        k.save()
        k.flush()

        bu = BaseUpdate('fedora', '6', 'i386', prefix, self.dbs)
        release = bu.getNextRelease('fedora-updates')
        assert release == 106

    def testMakeKitScript(self):
        raise SkipTest
        global prefix

        workingDir = path(tempfile.mkdtemp(dir=prefix))
        (workingDir / 'fedora-updates').makedirs()

        bu = BaseUpdate('fedora', '6', 'i386', prefix, self.dbs)
        bu.makeKitScript(workingDir, 'fedora-updates', '6_r100', 100)

        f = open(workingDir / 'fedora-updates' / 'build.kit', 'r')
        lines = f.read()
        f.close()

        assert lines.find("k.version = '6_r100'\n") != -1
        assert lines.find("k.release = '100'\n") != -1
        assert lines.find("k.arch = 'x86'\n") != -1
        assert lines.find("comp = Fedora6Component()\n") != -1

    def testMakeUpdateKit(self):
        raise SkipTest
        global prefix

        bu = BaseUpdate('fedora', '6', 'i386', prefix, self.dbs)

        def prepkit(workingDir,kitName): (workingDir/kitName/'packages').makedirs()
        def makekit(workingDir,DestDir,z): cpio_copytree(workingDir,DestDir)
        bu.prepKit = prepkit
        bu.makeKit = makekit
       
        r = rpmtool.RPM(name = 'foo',
                        version = '1.0',
                        release = '1',
                        arch = 'i386',
                        epoch = 0)
        
        r.filename = path(prefix / r.getFilename())
        r.getFilename().touch()
    
        kitdir, kitname, kitversion, kitrelease, kitarch = bu.makeUpdateKit([r])
   
        assert kitdir / 'fedora-updates' / 'packages' / 'foo-1.0-1.i386.rpm'    

    def testMakeTFTP(self):
        raise SkipTest
        global prefix

        (prefix / 'tftpboot' / 'kusu').makedirs()
        (prefix / 'tftpboot' / 'kusu' / 'initrd-fedora-6-i386.img').touch()

        url = 'http://www.osgdc.org/pub/build/tests/modules/yumupdates/kernel-1-1.1.i386.rpm'
        kernelRPM = prefix / 'kernel-1-1.1.i386.rpm'
        download(url, prefix) 

        rpm = rpmtool.RPM(str(kernelRPM))
        bu = BaseUpdate('fedora', '6', 'i386', prefix, self.dbs)
        vmlinuz, initrd = bu.makeTFTP(rpm, 100)

        assert vmlinuz == 'kernel-fedora-6-i386.100'
        assert initrd == 'initrd-fedora-6-i386.100.img'

    def testAddUpdateKit(self):
        raise SkipTest

        global prefix

        kitdir = path(prefix / 'newUpdateKit')
        kitdir.makedirs()
        f = open((kitdir / 'kitinfo'), 'w')
        f.write("""
kit = {'arch': 'noarch',
 'dependencies': [],
 'description': 'newKit kit.',
 'license': 'LGPL',
 'name': 'newKit',
 'pkgname': 'kit-newKit',
 'release': '0',
 'scripts': [],
 'version': '0.1'}
components = [{'arch': 'noarch',
  'comprelease': '0',
  'compversion': '0.1',
  'description': 'newKit component for Fedora Core 6.',
  'name': 'newKit',
  'ngtypes': [],
  'ostype': 'fedora',
  'osversion': '6',
  'pkgname': 'component-newKit'}]
""")
        f.close()
        (kitdir / 'component-newKit-0.1-0.noarch.rpm').touch()
        (kitdir / 'kit-newKit-0.1-0.noarch.rpm').touch()
 
        bu = BaseUpdate('fedora', '6', 'i386', prefix, self.dbs)
        bu.addUpdateKit(kitdir)

        kits = self.dbs.Kits.select_by(rname = 'newKit')
        assert len(kits) == 1
        assert kits[0].rname == 'newKit'
        
