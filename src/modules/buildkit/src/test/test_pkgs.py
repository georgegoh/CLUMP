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


TMPDIR = None
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
    TMPDIR = path(tools.mkdtemp(prefix='kitsrc-test-'))
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
        
    def testVerifyGoodPkgs(self):
        """ Test good packages can be setup and verified. """
        
        # setup a buildprofile
        bp = setupprofile(self.testkitsrc)
        
        for p in self.GOOD_PKGS:
            filepath = path(p)
            fullname = getDirName(filepath.basename())
            name, ver = fullname.split('-')
            pkg = SourcePackage(name=name,version=ver,buildprofile=bp,filepath=filepath)
            pkg.setup()
            assert pkg.verify() is True
            
    def testFedoraComponentInfo(self):
        """ Test that a componentinfo is defined correctly. """
        
        # create a fedora 6 component
        fc = Fedora6Component(name='test')

        assert fc.componentinfo.name == 'test'        
        assert fc.componentinfo.ostype == 'fedora'
        assert fc.componentinfo.osversion == '6'
        assert fc.componentinfo.compversion == '0.1'
        assert fc.componentinfo.comprelease == '0'
        assert fc.componentinfo.ngtypes == ['installer','compute']
        
    def testKitInfo(self):
        """ Test that a kitinfo is defined correctly. """
        
        # create a default kitinfo
        kit = DefaultKit(name='testkit')
        
        assert kit.kitinfo.name == 'testkit'
        assert kit.kitinfo.license == 'LGPL'
        assert kit.kitinfo.version == '0.1'
        assert kit.kitinfo.release == '0'
        assert kit.kitinfo.arch == 'noarch'
        
    def testCorrectKitInfoFile(self):
        """ Test that a kitinfo is generated correctly. """
        
        f = path(self.scratchdir / 'kitinfo')
        
        # define a couple of components
        c1 = Fedora6Component(name='comp1')
        c2 = Fedora6Component(name='comp2')
        
        # and kit too
        k = DefaultKit(name='testkit')
        
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
        """ Test the BinaryPackage setup. Incomplete! """
        
        pkg = BinaryPackage(name='foo')
        
        assert pkg.srctype == 'binarydist'
        assert pkg.name == 'foo'

        
    def testSRPMPackage(self):
        """ Test the BinaryPackage setup. Incomplete! """

        pkg = SRPMPackage(name='foo')

        assert pkg.srctype == 'srpm'
        assert pkg.name == 'foo'

        
        
            

