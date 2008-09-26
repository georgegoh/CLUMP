#!/usr/bin/env python
# $Id: test_imageops.py 476 2008-01-25 12:36:55Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
#
# This testsuite will go through the various operations in the
# BootMediaTool api. This testsuite will need to be run as root and
# requires the mock ISOs from [[insert site to get mock ISOs]]. The
# mock ISOs should be placed in a directory and an environment variable
# named KUSU_MOCK_ISODIR should be pointed to this directory.



from kusu.boot.tool import BootMediaTool
from path import path
import tempfile
from nose import SkipTest
import os
import subprocess
import time

def clearLoopDevices():
    """ Everytime a loop device is used, there's a chance it's not
        freed properly. This method should be called at the end of 
        tearDown methods to help alleviate this
    """
    t = subprocess.Popen('losetup -a',shell=True,stdout=subprocess.PIPE)
    v = t.communicate()[0]
    if not v:
        # if there are no used loop devices, then all is good
        return
    
    li = v.split('\n')
    usedLoopDevices = []
    for l in li:
        # only look for our own mounted point and not others!
        if l.find('mock') > -1:
            usedLoopDevices.append(l.split(':')[0])
        
    for loopDev in usedLoopDevices:
        cmd = 'losetup -d %s' % loopDev
        t = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        t.communicate()
        
    return

class TestBootImageOps:
    """ Test suite for b-m-t image operations. 
        Requires root to run and KUSU_MOCK_ISODIR to be set! 
    """
    
    def setUp(self):
        """ Housecleaning. """
        
        if os.getuid() != 0:
            # if not root, skip tests
            raise SkipTest
            
        if 'KUSU_MOCK_ISODIR' not in os.environ:
            raise SkipTest
        
        # get the iso and mount it
        self.isodir = path(os.environ['KUSU_MOCK_ISODIR'])
        self.iso = self.isodir / 'mock-FC-6-i386-disc1.iso'
        
        if not self.iso.exists():
            raise SkipTest
        
        self.tmpdir = path(tempfile.mkdtemp(dir='/tmp'))
        self.mountpt = self.tmpdir / 'mnt'
        self.mountpt.mkdir()
        cmd = 'mount -o loop,ro %s %s' % (self.iso,self.mountpt)
        mountP = subprocess.Popen(cmd,shell=True,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        mountP.communicate()

    def tearDown(self):
        """ Cleanup """

        if self.mountpt.exists():
            cmd = 'umount %s' % self.mountpt
            umountP = subprocess.Popen(cmd,shell=True,
                stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            umountP.communicate()
            
        if self.tmpdir.exists(): self.tmpdir.rmtree()
        
        # clear loop devices
        clearLoopDevices()
            
    def testUnpackRootImg(self):
        """ Test unpackRootImg method  """
        bmt = BootMediaTool()
        rootdir = self.tmpdir / 'rootfs'
        rootdir.mkdir()
        initrd = bmt.getInitrdPath(self.mountpt)
        bmt.unpackRootImg(initrd,rootdir)

        # the /init file should be in the rootfs directory
        # TODO: need better checks than this!
        assert path(rootdir / 'init').exists()
        
    def testPackRootImg(self):
        """ Test packRootImg method """
        
        # first we need to create a rootfs directory
        bmt = BootMediaTool()
        rootdir = self.tmpdir / 'rootfs'
        rootdir.mkdir()
        initrd = bmt.getInitrdPath(self.mountpt)
        bmt.unpackRootImg(initrd,rootdir)
        
        # next we create the new initramfs image
        rootimg = self.tmpdir / 'myinitram.img'
        bmt.packRootImg(rootdir,rootimg)

        # ensure it exists
        assert rootimg.exists()
        

        
        
        