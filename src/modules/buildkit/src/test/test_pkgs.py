#!/usr/bin/env python
# $Id$ 
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
""" Test the buildkit.kitsource module. """

import urllib
from kusu.util import tools
from kusu.buildkit import kitsource, build
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
        # disable for now
        raise SkipTest
        
        global TMPDIR
        global GOOD_PKGS
        global BAD_PKGS
        assetdir = TMPDIR / 'assets'
        self.scratchdir = path(tools.mkdtemp(dir=TMPDIR))
        self.GOOD_PKGS = [getAssetsPath(p) for p in GOOD_PKGS ]
        self.BAD_PKGS = [getAssetsPath(p) for p in BAD_PKGS ]
        
    def tearDown(self):
        if self.scratchdir.exists(): self.scratchdir.rmtree()
        
    def testVerifyGoodPkgs(self):
        """docstring for testVerifyGoodPkg"""
        
        for p in self.GOOD_PKGS:
            pp = build.PackageProfile(p.split('.')[0])
            pp.filepath = p            
            pkg = kitsource.GNUBuildTarballPkg(pp)
            assert pkg.verify() is True
            
    def testVerifyBadPkgs(self):
        """docstring for testVerifyBadPkg"""
        for p in self.BAD_PKGS:
            pp = build.PackageProfile(p.split('.')[0])
            pp.filepath = p            
            pkg = kitsource.GNUBuildTarballPkg(pp)
            assert pkg.verify() is False
            
    def testInstallPkg(self):
        """docstring for testInstallPkg"""
        pp = build.PackageProfile('hello')
        # get the hello pkg
        li = [p for p in self.GOOD_PKGS if 'hello' in p]
        if not li: raise SkipTest
        pp.filepath = li[0]
        print 'pp.filepath:', pp.filepath
        print 'pp.dirname:', pp.dirname
        pp.installroot = '/opt/hello'
        pp.buildroot = self.scratchdir / 'root'
        pp.builddir = self.scratchdir / 'tmp'
        pp.buildroot.mkdir()
        pp.builddir.mkdir()

        pkg = kitsource.GNUBuildTarballPkg(pp)
        pkg.install()
        assert path(pp.buildroot / 'bin/hello').exists()
            
    
            
            
            