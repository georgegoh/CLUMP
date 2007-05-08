#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from kusu.boot.distro import GeneralInstallSrc
from kusu.boot.distro import CopyError
from kusu.boot.distro import FileAlreadyExists
from path import path
import py
import tempfile

class TestCentOSExtraction:
    """Test suite for extraction of kernel/initrd from CentOS installation sources.
    
    These tests should only be run as a non-root user."""
    
    if os.environ['USER'] == 'root': disabled = True

    def setup_method(self, method):
        """Sets up mock paths"""
        
        self.setupCentOS()
     
    def teardown_method(self, method):
        """Clean up after done"""

        self.teardownCentOS()
        
    def setupCentOS(self):
        """CentOS-centric housekeeping"""
 
        self.centOSLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        
        # create a directory and delete it immediately after. 
        self.invalidCentOSLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        self.invalidCentOSLocalPath.rmdir()
        
        path(self.centOSLocalPath / 'isolinux').mkdir()
        path(self.centOSLocalPath / 'isolinux/vmlinuz').touch()
        path(self.centOSLocalPath / 'isolinux/initrd.img').touch()
        path(self.centOSLocalPath / 'images').mkdir()
        path(self.centOSLocalPath / 'CentOS').mkdir()
        path(self.centOSLocalPath / 'CentOS/RPMS').mkdir()
        path(self.centOSLocalPath / 'CentOS/base').mkdir()
        
        # create a scratch dir for general purposes
        self.scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
        
        
    def teardownCentOS(self):
        """CentOS-centric housekeeping in reverse"""
      
        self.scratchdir.rmtree()
        self.centOSLocalPath.rmtree()
        
    def test_getKernelPath(self):
        """Try to get the kernel from the installation source"""
        
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        kernelpath = path(self.centOSLocalPath / 'isolinux/vmlinuz')
        assert centosObj.getKernelPath() == kernelpath
        
    def test_notGetKernelPath(self):
        """detect if the kernel is not available"""

        centosObj = GeneralInstallSrc(self.invalidCentOSLocalPath)
        kernelpath = path(self.centOSLocalPath / 'isolinux/vmlinuz')
        assert centosObj.getKernelPath() != kernelpath
        
    def test_getInitrdPath(self):
        """Try to get the initrd from the installation source"""

        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        initrdpath = path(self.centOSLocalPath / 'isolinux/initrd.img')
        assert centosObj.getInitrdPath() == initrdpath

    def test_notGetInitrdPath(self):
        """detect if the initrd is not available"""

        centosObj = GeneralInstallSrc(self.invalidCentOSLocalPath)
        initrdpath = path(self.centOSLocalPath / 'isolinux/initrd.img')
        assert centosObj.getInitrdPath() != initrdpath        
        
    def test_copyKernelToDir(self):
        """Test copying the kernel file to a directory path"""
        
        destpath = self.scratchdir
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        centosObj.copyKernel(destpath)
        assert path(self.scratchdir / 'vmlinuz').exists() is True
        
        
    def test_copyKernelToNoWritePermsDir(self):
        """Test copying kernel file to a directory where the user have no write permission.
        This should raise the CopyError Exception"""
        
        destpath = path('/root')
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        py.test.raises(CopyError,centosObj.copyKernel,destpath)
        
    def test_copyInitrdToDir(self):
        """Test copying the initrd file to a directory path"""

        destpath = self.scratchdir
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        centosObj.copyInitrd(destpath)
        assert path(self.scratchdir / 'initrd.img').exists() is True

    def test_copyInitrdToNoWritePermsDir(self):
        """Test copying initrd file to a directory where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root')
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        py.test.raises(CopyError,centosObj.copyInitrd,destpath)
    
    def test_copyKernelToFile(self):
        """Test copying the kernel file to another file path."""

        destpath = self.scratchdir / 'newvmlinuz'
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        centosObj.copyKernel(destpath,overwrite=True)
        assert path(self.scratchdir / 'newvmlinuz').exists() is True

    def test_copyInitrdToFile(self):
        """Test copying the initrd file to another file path"""

        destpath = self.scratchdir / 'newinitrd.img'
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        centosObj.copyKernel(destpath,overwrite=True)
        assert path(self.scratchdir / 'newinitrd.img').exists() is True

    def test_notOverwriteKernelToFile(self):
        """Test overwriting the kernel file to another file path. This should raise the FileAlreadyExists exception."""

        destpath = self.scratchdir / 'noOverwriteVmlinuz'
        destpath.touch()
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        py.test.raises(FileAlreadyExists, "centosObj.copyKernel(destpath,overwrite=False)")

    def test_notOverwriteInitrdToFile(self):
        """Test overwriting the initrd file to another file path. This should raise the FileAlreadyExists exception."""

        destpath = self.scratchdir / 'noOverwriteInitrd.img'
        destpath.touch()
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        py.test.raises(FileAlreadyExists, "centosObj.copyInitrd(destpath,overwrite=False)")

    def test_copyKernelToNoWritePermsFile(self):
        """Test copying kernel file to a file path where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root/newvmlinuz')
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        py.test.raises(CopyError,centosObj.copyKernel,destpath,overwrite=True)
        
    def test_copyInitrdToNoWritePermsFile(self):
        """Test copying initrd file to a file path where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root/newinitrd.img')
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        py.test.raises(CopyError,centosObj.copyInitrd,destpath,overwrite=True)
        
    def test_overwriteKernelToNoWritePermsFile(self):
        """Test copying kernel file to a file path where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root/newvmlinuz')
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        py.test.raises(CopyError,centosObj.copyKernel,destpath,overwrite=False)

    def test_overwriteInitrdToNoWritePermsFile(self):
        """Test copying initrd file to a file path where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root/newinitrd.img')
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        py.test.raises(CopyError,centosObj.copyInitrd,destpath,overwrite=False)     
        