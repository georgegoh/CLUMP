#!/usr/bin/env python
# $Id: test_extraction.py 476 2008-01-25 12:36:55Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from kusu.boot.distro import DistroFactory
from kusu.util.errors import *
from path import path
from nose.tools import raises
from nose import SkipTest
import tempfile

#class TestCentOSExtraction:
#    """Test suite for extraction of kernel/initrd from CentOS installation sources.
#    
#    These tests should only be run as a non-root user."""
#    
#
#    def setUp(self):
#        """Sets up mock paths"""
#        raise SkipTest
#
#        # check if this is run non-root else skip it.
#        if os.getuid() == 0:
#            raise SkipTest
#            
#        self.setupCentOS()
#     
#    def tearDown(self):
#        """Clean up after done"""
#
#        self.teardownCentOS()
#        
#    def setupCentOS(self):
#        """CentOS-centric housekeeping"""
# 
#        self.centOSLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
#        self.additionalCentOSLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
#        
#        # create a directory and delete it immediately after. 
#        self.invalidCentOSLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
#        self.invalidCentOSLocalPath.rmdir()
#        
#        path(self.centOSLocalPath / 'isolinux').mkdir()
#        path(self.centOSLocalPath / 'isolinux/vmlinuz').touch()
#        path(self.centOSLocalPath / 'isolinux/initrd.img').touch()
#        path(self.centOSLocalPath / 'isolinux/isolinux.bin').touch()
#        path(self.centOSLocalPath / 'images').mkdir()
#        path(self.centOSLocalPath / 'images/stage2.img').touch()        
#        path(self.centOSLocalPath / 'CentOS').mkdir()
#        path(self.centOSLocalPath / 'CentOS/RPMS').mkdir()
#        path(self.centOSLocalPath / 'CentOS/base').mkdir()
#        
#        path(self.additionalCentOSLocalPath / 'CentOS').mkdir()
#        path(self.additionalCentOSLocalPath / 'CentOS/RPMS').mkdir()
#
#        # create a scratch dir for general purposes
#        self.scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
#        
#        
#    def teardownCentOS(self):
#        """CentOS-centric housekeeping in reverse"""
#      
#        self.scratchdir.rmtree()
#        self.centOSLocalPath.rmtree()
#        self.additionalCentOSLocalPath.rmtree()
#        
#    def test_getKernelPath(self):
#        """Try to get the kernel from the installation source"""
#        
#        centosObj = DistroFactory(self.centOSLocalPath)
#        print centosObj
#        kernelpath = path(self.centOSLocalPath / 'isolinux/vmlinuz')
#        print 'centosObj:',centosObj.getKernelPath()
#        print 'src:', kernelpath
#        assert centosObj.getKernelPath() == kernelpath
#        
#    def test_notGetKernelPath(self):
#        """detect if the kernel is not available"""
#
#        centosObj = DistroFactory(self.invalidCentOSLocalPath)
#        kernelpath = path(self.centOSLocalPath / 'isolinux/vmlinuz')
#        assert centosObj.getKernelPath() != kernelpath
#        
#    def test_getInitrdPath(self):
#        """Try to get the initrd from the installation source"""
#
#        centosObj = DistroFactory(self.centOSLocalPath)
#        initrdpath = path(self.centOSLocalPath / 'isolinux/initrd.img')
#        assert centosObj.getInitrdPath() == initrdpath
#
#    def test_notGetInitrdPath(self):
#        """detect if the initrd is not available"""
#
#        centosObj = DistroFactory(self.invalidCentOSLocalPath)
#        initrdpath = path(self.centOSLocalPath / 'isolinux/initrd.img')
#        assert centosObj.getInitrdPath() != initrdpath        
#        
#    def test_copyKernelToDir(self):
#        """Test copying the kernel file to a directory path"""
#        
#        destpath = self.scratchdir
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyKernel(destpath)
#        assert path(self.scratchdir / 'vmlinuz').exists() is True
#        
#    @raises(CopyError)
#    def test_copyKernelToNoWritePermsDir(self):
#        """Test copying kernel file to a directory where the user have no write permission.
#        This should raise the CopyError Exception"""
#        
#        destpath = path('/root')
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyKernel(destpath)
#        
#    def test_copyInitrdToDir(self):
#        """Test copying the initrd file to a directory path"""
#
#        destpath = self.scratchdir
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyInitrd(destpath)
#        assert path(self.scratchdir / 'initrd.img').exists() is True
#
#    @raises(CopyError)
#    def test_copyInitrdToNoWritePermsDir(self):
#        """Test copying initrd file to a directory where the user have no write permission.
#        This should raise the CopyError Exception"""
#
#        destpath = path('/root')
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyInitrd(destpath)
#    
#    def test_copyKernelToFile(self):
#        """Test copying the kernel file to another file path."""
#
#        destpath = self.scratchdir / 'newvmlinuz'
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyKernel(destpath,overwrite=True)
#        assert path(self.scratchdir / 'newvmlinuz').exists() is True
#
#    def test_copyInitrdToFile(self):
#        """Test copying the initrd file to another file path"""
#
#        destpath = self.scratchdir / 'newinitrd.img'
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyKernel(destpath,overwrite=True)
#        assert path(self.scratchdir / 'newinitrd.img').exists() is True
#
#    @raises(FileAlreadyExists)
#    def test_notOverwriteKernelToFile(self):
#        """Test overwriting the kernel file to another file path. This should raise the FileAlreadyExists exception."""
#
#        destpath = self.scratchdir / 'noOverwriteVmlinuz'
#        destpath.touch()
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyKernel(destpath,overwrite=False)
#
#    @raises(FileAlreadyExists)
#    def test_notOverwriteInitrdToFile(self):
#        """Test overwriting the initrd file to another file path. This should raise the FileAlreadyExists exception."""
#
#        destpath = self.scratchdir / 'noOverwriteInitrd.img'
#        destpath.touch()
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyInitrd(destpath,overwrite=False)
#
#    @raises(CopyError)
#    def test_copyKernelToNoWritePermsFile(self):
#        """Test copying kernel file to a file path where the user have no write permission.
#        This should raise the CopyError Exception"""
#
#        destpath = path('/root/newvmlinuz')
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyKernel(destpath,overwrite=True)
#
#    @raises(CopyError)        
#    def test_copyInitrdToNoWritePermsFile(self):
#        """Test copying initrd file to a file path where the user have no write permission.
#        This should raise the CopyError Exception"""
#
#        destpath = path('/root/newinitrd.img')
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyInitrd(destpath,overwrite=True)
#        
#    @raises(CopyError)
#    def test_overwriteKernelToNoWritePermsFile(self):
#        """Test copying kernel file to a file path where the user have no write permission.
#        This should raise the CopyError Exception"""
#
#        destpath = path('/root/newvmlinuz')
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyKernel(destpath,overwrite=False)
#
#    @raises(CopyError)
#    def test_overwriteInitrdToNoWritePermsFile(self):
#        """Test copying initrd file to a file path where the user have no write permission.
#        This should raise the CopyError Exception"""
#
#        destpath = path('/root/newinitrd.img')
#        centosObj = DistroFactory(self.centOSLocalPath)
#        centosObj.copyInitrd(destpath,overwrite=False)     
#
#    @raises(CopyError)        
#    def test_additionalCentosNoCopyKernel(self):
#        """Test copying the kernel file for additional media.
#        This should raise the CopyError Exception."""
#        
#        destpath = path('/root/newvmlinuz')
#        centosObj = DistroFactory(self.additionalCentOSLocalPath)
#        centosObj.copyKernel(destpath,overwrite=False)
#        
#    @raises(CopyError)        
#    def test_additionalCentosNoCopyInitrd(self):
#        """Test copying the initrd file for additional media.
#        This should raise the CopyError Exception."""
#        
#        destpath = path('/root/newinitrd')
#        centosObj = DistroFactory(self.additionalCentOSLocalPath)
#        centosObj.copyInitrd(destpath,overwrite=False)
#        
#    def test_additionalCentosInvalidKernelPath(self):
#        """Test getting the kernel path. This should return the None object"""
#        
#        centosObj = DistroFactory(self.additionalCentOSLocalPath)
#        assert centosObj.getKernelPath() == None
#        
#    def test_additionalCentosInvalidInitrdPath(self):
#        """Test getting the initrd path. This should return the None object"""
#        
#        centosObj = DistroFactory(self.additionalCentOSLocalPath)
#        assert centosObj.getInitrdPath() == None

        
class TestRHEL5Extraction:
    """Test suite for extraction of kernel/initrd from RHEL 5 installation sources.
    
    These tests should only be run as a non-root user."""
    

    def setUp(self):
        """Sets up mock paths"""

        # check if this is run non-root else skip it.
        if os.getuid() == 0:
            raise SkipTest
            
        self.setupRHEL()
     
    def tearDown(self):
        """Clean up after done"""

        self.teardownRHEL()
        
    def setupRHEL(self):
        """RHEL-centric housekeeping"""

        self.rhelLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        self.additionalRHELLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        
        # create a directory and delete it immediately after. 
        self.invalidRHELLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        self.invalidRHELLocalPath.rmdir()

        path(self.rhelLocalPath / 'isolinux').mkdir()
        path(self.rhelLocalPath / 'isolinux/vmlinuz').touch()
        path(self.rhelLocalPath / 'isolinux/initrd.img').touch()
        path(self.rhelLocalPath / 'isolinux/isolinux.bin').touch()
        path(self.rhelLocalPath / 'images').mkdir()
        path(self.rhelLocalPath / 'images/stage2.img').touch()
        path(self.rhelLocalPath / 'Server').mkdir()
        path(self.rhelLocalPath / 'Server/repodata').mkdir()
        path(self.rhelLocalPath / 'Cluster').mkdir()
        path(self.rhelLocalPath / 'Cluster/repodata').mkdir()
        path(self.rhelLocalPath / 'ClusterStorage').mkdir()
        path(self.rhelLocalPath / 'ClusterStorage/repodata').mkdir()
        path(self.rhelLocalPath / 'VT').mkdir()
        path(self.rhelLocalPath / 'VT/repodata').mkdir()

        path(self.additionalRHELLocalPath / 'Server').mkdir()
        path(self.additionalRHELLocalPath / 'Server/repodata').mkdir()
        path(self.additionalRHELLocalPath / 'Cluster').mkdir()
        path(self.additionalRHELLocalPath / 'Cluster/repodata').mkdir()
        path(self.additionalRHELLocalPath / 'ClusterStorage').mkdir()
        path(self.additionalRHELLocalPath / 'ClusterStorage/repodata').mkdir()
        path(self.additionalRHELLocalPath / 'VT').mkdir()
        path(self.additionalRHELLocalPath / 'VT/repodata').mkdir()
 
        # create a scratch dir for general purposes
        self.scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
        
        
    def teardownRHEL(self):
        """RHEL-centric housekeeping in reverse"""
      
        self.scratchdir.rmtree()
        self.rhelLocalPath.rmtree()
        self.additionalRHELLocalPath.rmtree()
        
    def test_getKernelPath(self):
        """Try to get the kernel from the installation source"""
        
        rhelObj = DistroFactory(self.rhelLocalPath)
        kernelpath = path(self.rhelLocalPath / 'isolinux/vmlinuz')
        assert rhelObj.getKernelPath() == kernelpath
        
    def test_notGetKernelPath(self):
        """detect if the kernel is not available"""

        rhelObj = DistroFactory(self.invalidRHELLocalPath)
        kernelpath = path(self.rhelLocalPath / 'isolinux/vmlinuz')
        assert rhelObj.getKernelPath() != kernelpath
        
    def test_getInitrdPath(self):
        """Try to get the initrd from the installation source"""

        rhelObj = DistroFactory(self.rhelLocalPath)
        initrdpath = path(self.rhelLocalPath / 'isolinux/initrd.img')
        assert rhelObj.getInitrdPath() == initrdpath

    def test_notGetInitrdPath(self):
        """detect if the initrd is not available"""

        rhelObj = DistroFactory(self.invalidRHELLocalPath)
        initrdpath = path(self.rhelLocalPath / 'isolinux/initrd.img')
        assert rhelObj.getInitrdPath() != initrdpath        
        
    def test_copyKernelToDir(self):
        """Test copying the kernel file to a directory path"""
        
        destpath = self.scratchdir
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyKernel(destpath)
        assert path(self.scratchdir / 'vmlinuz').exists() is True
        
    @raises(CopyError)
    def test_copyKernelToNoWritePermsDir(self):
        """Test copying kernel file to a directory where the user have no write permission.
        This should raise the CopyError Exception"""
        
        destpath = path('/root')
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyKernel(destpath)
        
    def test_copyInitrdToDir(self):
        """Test copying the initrd file to a directory path"""

        destpath = self.scratchdir
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyInitrd(destpath)
        assert path(self.scratchdir / 'initrd.img').exists() is True

    @raises(CopyError)
    def test_copyInitrdToNoWritePermsDir(self):
        """Test copying initrd file to a directory where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root')
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyInitrd(destpath)
    
    def test_copyKernelToFile(self):
        """Test copying the kernel file to another file path."""

        destpath = self.scratchdir / 'newvmlinuz'
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyKernel(destpath,overwrite=True)
        assert path(self.scratchdir / 'newvmlinuz').exists() is True

    def test_copyInitrdToFile(self):
        """Test copying the initrd file to another file path"""

        destpath = self.scratchdir / 'newinitrd.img'
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyKernel(destpath,overwrite=True)
        assert path(self.scratchdir / 'newinitrd.img').exists() is True

    @raises(FileAlreadyExists)
    def test_notOverwriteKernelToFile(self):
        """Test overwriting the kernel file to another file path. This should raise the FileAlreadyExists exception."""

        destpath = self.scratchdir / 'noOverwriteVmlinuz'
        destpath.touch()
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyKernel(destpath,overwrite=False)

    @raises(FileAlreadyExists)
    def test_notOverwriteInitrdToFile(self):
        """Test overwriting the initrd file to another file path. This should raise the FileAlreadyExists exception."""

        destpath = self.scratchdir / 'noOverwriteInitrd.img'
        destpath.touch()
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyInitrd(destpath,overwrite=False)

    @raises(CopyError)
    def test_copyKernelToNoWritePermsFile(self):
        """Test copying kernel file to a file path where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root/newvmlinuz')
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyKernel(destpath,overwrite=True)

    @raises(CopyError)        
    def test_copyInitrdToNoWritePermsFile(self):
        """Test copying initrd file to a file path where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root/newinitrd.img')
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyInitrd(destpath,overwrite=True)
        
    @raises(CopyError)
    def test_overwriteKernelToNoWritePermsFile(self):
        """Test copying kernel file to a file path where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root/newvmlinuz')
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyKernel(destpath,overwrite=False)

    @raises(CopyError)
    def test_overwriteInitrdToNoWritePermsFile(self):
        """Test copying initrd file to a file path where the user have no write permission.
        This should raise the CopyError Exception"""

        destpath = path('/root/newinitrd.img')
        rhelObj = DistroFactory(self.rhelLocalPath)
        rhelObj.copyInitrd(destpath,overwrite=False)     

    @raises(CopyError)        
    def test_additionalCentosNoCopyKernel(self):
        """Test copying the kernel file for additional media.
        This should raise the CopyError Exception."""
        
        destpath = path('/root/newvmlinuz')
        rhelObj = DistroFactory(self.additionalRHELLocalPath)
        rhelObj.copyKernel(destpath,overwrite=False)
        
    @raises(CopyError)        
    def test_additionalCentosNoCopyInitrd(self):
        """Test copying the initrd file for additional media.
        This should raise the CopyError Exception."""
        
        destpath = path('/root/newinitrd')
        rhelObj = DistroFactory(self.additionalRHELLocalPath)
        rhelObj.copyInitrd(destpath,overwrite=False)
        
    def test_additionalCentosInvalidKernelPath(self):
        """Test getting the kernel path. This should return the None object"""
        
        rhelObj = DistroFactory(self.additionalRHELLocalPath)
        assert rhelObj.getKernelPath() == None
        
    def test_additionalCentosInvalidInitrdPath(self):
        """Test getting the initrd path. This should return the None object"""
        
        rhelObj = DistroFactory(self.additionalRHELLocalPath)
        assert rhelObj.getInitrdPath() == None
 
