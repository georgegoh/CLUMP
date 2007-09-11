#!/usr/bin/env python
# $Id$ 
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
""" Test the buildkit.kitsource module. """

import urllib
from kusu.util import tools
from kusu.buildkit import KitSrcFactory, setupprofile, Fedora6Component, DefaultKit, processKitInfo
from kusu.buildkit import BinaryPackage, SourcePackage, DistroPackage, RPMPackage, SRPMPackage
from kusu.buildkit.builder import getDirName
from path import path
from nose import SkipTest


TMPDIR = path(tools.mkdtemp(prefix='kitsrc-test-'))
TEST_ASSETS_URL = 'http://www.osgdc.org/pub/build/tests/modules/buildkit/'
GOOD_PKGS = ['hello-2.3.tar.gz', 'hello-2.3.tbz2']
BAD_PKGS = ['dummy-2.3.tar.gz']
TEST_PKGS = GOOD_PKGS + BAD_PKGS

def downloadAssets():
    global TMPDIR
    dlpath = '%s/assets' % TMPDIR
    dlpath = path(dlpath)
    for p in TEST_PKGS:
        urllib.urlretrieve(TEST_ASSETS_URL + p, dlpath / p)

def setUp():
    global TMPDIR
    if not path(TMPDIR / 'assets').exists():
        path(TMPDIR / 'assets').mkdir()
        downloadAssets()
    
def tearDown():
    global TMPDIR
    if TMPDIR.exists(): TMPDIR.rmtree()
    
def getAssetsPath(p):
    global TMPDIR
    return '%s/assets/%s' % (TMPDIR,p)

class TestGNUBuildTarballPkg(object):
    """docstring for TestGNUBuildTarballPkg"""

    def setUp(self):
        
        global TMPDIR
        global GOOD_PKGS
        global BAD_PKGS
        assetdir = TMPDIR / 'assets'
        self.scratchdir = path(tools.mkdtemp(dir=TMPDIR))
        self.GOOD_PKGS = [getAssetsPath(p) for p in GOOD_PKGS ]
        self.BAD_PKGS = [getAssetsPath(p) for p in BAD_PKGS ]
        
        # set up kitsource directory
        self.testkitsrc = self.scratchdir / 'testkit'
        KitSrcFactory(self.testkitsrc).prepareSrcPath()
        
    def tearDown(self):
        if self.scratchdir.exists(): self.scratchdir.rmtree()


    def testSetupProfile(self):
        """ Test for correct buildprofile. """
        bp = setupprofile(self.testkitsrc)
        assert bp.builddir == self.testkitsrc / 'artifacts'
        assert bp.tmpdir == self.testkitsrc / 'tmp'
            
    def testFedoraComponentInfo(self):
        """ Test that a componentinfo is defined correctly. """
        
        # create a fedora 6 component
        fc = Fedora6Component()
        fc.name = 'test'

        assert fc.name == 'test'        
        assert fc.ostype == 'fedora'
        assert fc.osversion == '6'
        assert fc.compversion == '0.1'
        assert fc.comprelease == '0'
        assert fc.ngtypes == ['installer','compute']
        
    def testKitInfo(self):
        """ Test that a kitinfo is defined correctly. """
        
        # set buildprofile
        bp = setupprofile(self.testkitsrc)
        
        # create a default kitinfo
        kit = DefaultKit()
        kit.name = 'testkit'
        kit.buildprofile = bp
        kit.setup()
        
        assert kit.name == 'testkit'
        assert kit.license == 'LGPL'
        assert kit.version == '0.1'
        assert kit.release == '0'
        assert kit.arch == 'noarch'
        
    def testCorrectKitInfoFile(self):
        """ Test that a kitinfo is generated correctly. """
        
        f = path(self.scratchdir / 'kitinfo')
        
        # define a couple of components
        c1 = Fedora6Component()
        c1.name = 'comp1'
        
        c2 = Fedora6Component()
        c2.name = 'comp2'
        
        # and kit too
        k = DefaultKit()
        k.name = 'testkit'
        
        # add the components to the kit
        # both addComponent and addComp means the same thing, it's just syntatic sugar
        k.addComponent(c1)
        k.addComp(c2)
        
        k.generateKitInfo(f)
        kit, components = processKitInfo(f)

        assert kit['name'] == 'testkit'
        assert kit['license'] == 'LGPL' 
        assert kit['version'] == '0.1'
        assert kit['release'] == '0'
        assert kit['arch'] == 'noarch'
        
        assert len(components) == 2
        names = [comp['name'] for comp in components]
        names.sort()
        compnames = ['comp1','comp2']
        compnames.sort()
        assert names == compnames

        
    def testBinaryPackage(self):
        """ Test the BinaryPackage setup."""
        
        pkg = BinaryPackage()
        pkg.name = 'foo'
        
        assert pkg.srctype == 'binary'
        assert pkg.name == 'foo'

        
    def testSRPMPackage(self):
        """ Test the BinaryPackage setup."""

        pkg = SRPMPackage()
        pkg.name = 'foo'

        assert pkg.srctype == 'srpm'
        assert pkg.name == 'foo'

        
        
            

