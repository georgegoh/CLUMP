#!/usr/bin/env python
# $Id$ 
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
""" Test the buildkit.kitsource module. """

import urllib
from kusu.util import tools
from kusu.buildkit import KitSrcFactory, SourcePackage, setupprofile
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
        """docstring for testVerifyGoodPkg"""
        
        # setup a buildprofile
        bp = setupprofile(self.testkitsrc)
        
        for p in self.GOOD_PKGS:
            filepath = path(p)
            fullname = getDirName(filepath.basename())
            print fullname
            name, ver = fullname.split('-')
            pkg = SourcePackage(name=name,version=ver,buildprofile=bp,filepath=filepath)
            pkg.setup()
            assert pkg.verify() is True
            

