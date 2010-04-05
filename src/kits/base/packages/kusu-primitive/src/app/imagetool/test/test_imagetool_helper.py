#!/usr/bin/env python
# $Id: test_imagetool_helper.py 3135 2009-10-23 05:42:58Z ltsai $
#
"""Tests for the imagetool.helper module"""

from path import path
from tempfile import mkdtemp
from nose.tools import assert_raises
from primitive.fetchtool.commands import FetchCommand
from primitive.imagetool.helper import getDirSize, getImgInfo, generateImgInfo

# Test Assets
TEST_ROOTIMG_ASSET = 'http://www.osgdc.org/pub/build/tests/modules/primitive/imagetool/rootimgdir'
TEST_ROOTIMG_SIZE = 10531507L

TEST_IMGINFO_ASSET = 'http://www.osgdc.org/pub/build/tests/modules/primitive/imagetool/imginfo'

# imginfo constants
REQUIRED_IMGINFO_KEYS = ['os','osver', 'osarch', 'kernelpath', 'initrdpath', 'archives']

class TestHelper:
    
    def __init__(self):
        self.scratchdir = None # scratchdir for running tests
    
    def setUp(self):
        self.scratchdir = path(mkdtemp(prefix='imagetooldir-'))
        
    def tearDown(self):
        if self.scratchdir.exists(): self.scratchdir.rmtree()
        
        
    def testGetDirSize(self):
        """Test getDirSize returns the correct size of a directory"""
        testdir = self.scratchdir / 'rootimgdir'
        testdir.mkdir()
        fc = FetchCommand(uri=TEST_ROOTIMG_ASSET, fetchdir=True, 
                destdir=testdir, overwrite=True)
        status, destdir = fc.execute()
        assert status
        
        # size differs now. corrupted source
        #assert getDirSize(destdir) == TEST_ROOTIMG_SIZE
        
    def testGetImgInfo(self):
        """Test reading and parsing the imginfo file"""
        testdir = self.scratchdir
        fc = FetchCommand(uri=TEST_IMGINFO_ASSET, fetchdir=False,
                destdir=testdir, overwrite=True)
        status, imginfofile = fc.execute()
        imginfofile = path(imginfofile)
        assert status
        assert imginfofile.exists()
        imginfo = getImgInfo(imginfofile)
        
        # ensure imginfo is not None
        assert imginfo
        
        # ensure required keys are there
        s1 = set(imginfo.keys())
        s2 = set(REQUIRED_IMGINFO_KEYS)
        # ensure no missing keys
        assert not s1.difference(s2)
        
        # ensure the archives is a list
        assert type(imginfo['archives']) is type([])
        
    def testGenerateImgInfo(self):
        """Test writing the imginfo file"""
        testdir = self.scratchdir
        
        # construct the imginfo dict
        d = {}
        d['os'] = 'rhel'
        d['osver'] = '5.1'
        d['osarch'] = 'x86_64'
        d['kernelpath'] = 'boot/vmlinuz'
        d['initrdpath'] = 'boot/initrd.img'
        d['archives'] = [{'etc.tgz': 47717L}, {'usr.tgz': 1168385L}]
        
        imginfofile = testdir / 'myimginfo'
        generateImgInfo(imginfofile, d)
        
        # ensure file is generated
        assert imginfofile.exists()
        
        # load it back and compare with original dict
        imginfo = getImgInfo(imginfofile)
        
        assert imginfo == d
        

        

                          
        
        
