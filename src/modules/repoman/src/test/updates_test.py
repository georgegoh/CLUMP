#!/usr/bin/env python
# $Id$
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
        global prefix

        workingDir = path(tempfile.mkdtemp(dir=prefix))
        (workingDir / 'fedora-updates').makedirs()

        bu = BaseUpdate('fedora', '6', 'i386', prefix, self.dbs)
        bu.makeKitScript(workingDir, 'fedora-updates', 100)

        f = open(workingDir / 'fedora-updates' / 'build.kit', 'r')
        lines = f.read()
        f.close()

        assert lines.find("k.version = '6_r100'") != -1
        assert lines.find("k.release = '100'") != -1
        assert lines.find("k.arch = 'i386'") != -1
        assert lines.find("comp = Fedora6Component") != -1

    def testMakeUpdateKit(self):
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
    
        kitdir = bu.makeUpdateKit([r])
   
        assert kitdir / 'fedora-updates' / 'packages' / 'foo-1.0-1.i386.rpm'    

    def testMakeTFTP(self):
        global prefix

        (prefix / 'tftpboot' / 'kusu').makedirs()
        (prefix / 'tftpboot' / 'kusu' / 'initrd-fedora-6-i386.img').touch()

        url = 'http://www.osgdc.org/pub/build/tests/modules/yumupdates/kernel-1-1.1.i386.rpm'
        kernelRPM = prefix / 'kernel-1-1.1.i386.rpm'
        download(url, prefix) 

        rpm = rpmtool.RPM(str(kernelRPM))
        bu = BaseUpdate('fedora', '6', 'i386', prefix, self.dbs)
        vmlinuz, initrd = bu.makeTFTP(rpm, 100)

        assert vmlinuz == prefix / 'tftpboot' / 'kusu' / 'kernel-fedora-6-i386.100'
        assert initrd == prefix / 'tftpboot' / 'kusu' / 'initrd-fedora-6-i386.100.img'

