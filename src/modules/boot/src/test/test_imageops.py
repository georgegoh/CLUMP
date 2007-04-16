#!/usr/bin/env python
# $Id: test_imageops.py 209 2007-04-02 05:28:53Z najib $
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

"""Test suite for the kusu.boot.image module. The tests require a fixed set of known data.
   Please ensure that the test data are available in the data/ subdirectory in order
   to make the tests run.
"""

import sys
import os
from kusu.boot.distro import GeneralInstallSrc
from kusu.boot.distro import CopyError
from kusu.boot.distro import FileAlreadyExists
from kusu.boot import image
from path import path
import py
import tempfile


class TestCentOSBootImages:
    """Test suite for CentOS root images. This should only run when the data/* are
       available.
    """
    
    # These tests should only run as root
    if os.environ['USER'] == 'root':
    
        TESTDATADIR = None
    
        # find the testdata directory in current dir
        if path('./data/imageops').exists():
            TESTDATADIR = path('./data/imageops')
    
        # check the kusu path environment for the base dir
        PYTHONPATH = os.environ['PYTHONPATH']
    
        if not PYTHONPATH: disabled = True

        # else we do a walkdown on the subdirs, break on the first instance    
        for k in PYTHONPATH.split(':'):
            for d in path(k).walkdirs('imageops'):
                TESTDATADIR = d
        
        if not TESTDATADIR: disabled = True

        if not path(TESTDATADIR / 'centos/vmlinuz').exists() and \
        not path(TESTDATADIR / 'centos/initrd.img').exists():
        
            disabled = True

    else:
        disabled = True
    
    
    def setup_method(self, method):
        """centos housekeeping"""
        

        self.centOSLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        
        # create a directory and delete it immediately after. 
        self.invalidCentOSLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        self.invalidCentOSLocalPath.rmdir()
        
        path(self.centOSLocalPath / 'isolinux').mkdir()
        
        path(self.TESTDATADIR / 'centos/initrd.img').copy(path(self.centOSLocalPath / 'isolinux'))
        path(self.TESTDATADIR / 'centos/vmlinuz').copy(path(self.centOSLocalPath / 'isolinux'))
        
        self.kernelpath = path(self.centOSLocalPath / 'isolinux/vmlinuz')
        self.rootimgpath = path(self.centOSLocalPath / 'isolinux/initrd.img')
        
        path(self.centOSLocalPath / 'images').mkdir()
        path(self.centOSLocalPath / 'CentOS').mkdir()
        path(self.centOSLocalPath / 'CentOS/RPMS').mkdir()
        path(self.centOSLocalPath / 'CentOS/base').mkdir()
        
        # create a scratch dir for general purposes
        self.scratchdir = path(tempfile.mkdtemp(dir='/tmp'))


        
    def teardown_method(self, method):
        """cleanup"""
            
        self.scratchdir.rmtree()
        self.centOSLocalPath.rmtree()

    
    def test_validOperatingEnvironment(self):
        """Test if created OperatingEnvironment is valid"""
        pass
        
    def test_invalidOperatingEnvironment(self):
        """docstring for test_notValidOperatingEnvironment"""
        pass
        
    def test_validKernelVersion(self):
        """Check if the version string is correct"""
        
        kernelversion = '2.6.9-42.EL'
        
        # create an OperatingEnvironment obj with the testdata values
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        rootimgpath = centosObj.getInitrdPath()
        kernelpath = centosObj.getKernelPath()
        centosEnv = image.OperatingEnvironment(kernelpath=kernelpath, rootimgpath=rootimgpath, ostype=centosObj.ostype)
        
        assert kernelversion == centosEnv.getKernelVersion()
        
    def test_invalidKernelVersion(self):
        """Check if the version string is indeed incorrect"""
        
        kernelversion = 'xxxxxxxx'
        
        # create an OperatingEnvironment obj with the testdata values
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        rootimgpath = centosObj.getInitrdPath()
        kernelpath = centosObj.getKernelPath()
        centosEnv = image.OperatingEnvironment(kernelpath=kernelpath, rootimgpath=rootimgpath, ostype=centosObj.ostype)
        
        assert kernelversion != centosEnv.getKernelVersion()
        
    def test_validArch(self):
        """docstring for test_validArch"""
        pass
        
    def test_invalidArch(self):
        """docstring for test_invalidArch"""
        pass
        
    def test_validRootImgFormat(self):
        """Test if the packing format is correct for centos images"""
        
        # centos initrd.img is ext2 filesystem compressed with gzip
        format = ['ext2', 'gzip']
        
        # create an OperatingEnvironment obj with the testdata values
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        rootimgpath = centosObj.getInitrdPath()
        kernelpath = centosObj.getKernelPath()
        centosEnv = image.OperatingEnvironment(kernelpath=kernelpath, rootimgpath=rootimgpath, ostype=centosObj.ostype)
        centosImgFormat = centosEnv.getRootImgFormat()
        
        # sort and compare
        format.sort()
        centosImgFormat.sort()
        
        assert format == centosImgFormat
        
        
    def test_invalidRootImgFormat(self):
        """Test if the packing format is incorrect for centos images"""
        
        # centos initrd.img is ext2 filesystem compressed with gzip
        # so make sure the format is wrong for this test
        format = ['cpio', 'gzip']
        
        # create an OperatingEnvironment obj with the testdata values
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        rootimgpath = centosObj.getInitrdPath()
        kernelpath = centosObj.getKernelPath()
        centosEnv = image.OperatingEnvironment(kernelpath=kernelpath, rootimgpath=rootimgpath, ostype=centosObj.ostype)
        centosImgFormat = centosEnv.getRootImgFormat()
        
        # sort and compare
        format.sort()
        centosImgFormat.sort()
        
        assert format != centosImgFormat
      
        
    def test_successPackInitramFS(self):
        """docstring for test_successPackInitramFS"""
        pass
        
    def test_failurePackInitramFS(self):
        """docstring for test_failurePackInitramFS"""
        pass
        
    def test_successUnpack(self):
        """docstring for test_successUnpack"""
        pass
        
    def test_failureUnpack(self):
        """docstring for test_failureUnpack"""
        pass
        
    def test_successMakeISOLinuxDir(self):
        """docstring for test_successMakeISOLinuxDir"""
        pass
        
    def test_failureMakeISOLinuxDir(self):
        """docstring for test_failureMakeISOLinuxDir"""
        pass
        
    def test_successMakeBootISO(self):
        """docstring for test_successMakeBootISO"""
        pass
        
    def test_failureMakeBootISO(self):
        """docstring for test_failureMakeBootISO"""
        pass
        
    def test_successMakeBootArchive(self):
        """docstring for test_successMakeBootArchive"""
        pass
        
    def test_failureMakeBootArchive(self):
        """docstring for test_failureMakeBootArchive"""
        pass
