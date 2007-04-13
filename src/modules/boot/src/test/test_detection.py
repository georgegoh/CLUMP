#!/usr/bin/env python
# $Id: test_detection.py 194 2007-03-29 07:36:10Z najib $
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from kusu.boot.distro import GeneralInstallSrc
from kusu.ext.path import path
import tempfile

class TestCentOSDetection:
    """Test suite for detecting CentOS installation sources"""
    
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
        
        
    def teardownCentOS(self):
        """CentOS-centric housekeeping in reverse"""
      
        path(self.centOSLocalPath / 'isolinux/vmlinuz').remove()
        path(self.centOSLocalPath / 'isolinux/initrd.img').remove()  
        path(self.centOSLocalPath / 'isolinux').rmdir()
        path(self.centOSLocalPath / 'images').rmdir()
        path(self.centOSLocalPath / 'CentOS/RPMS').rmdir()
        path(self.centOSLocalPath / 'CentOS/base').rmdir()
        path(self.centOSLocalPath / 'CentOS').rmdir()
        self.centOSLocalPath.rmdir()
        
    def test_IsCentOSCD(self):
        """Test if the CD is a CentOS CD"""
        
        cdObj = GeneralInstallSrc(self.centOSLocalPath)
        assert cdObj.ostype == "centos"

    def test_IsNotCentOSCD(self):
        """Test if the CD is not a CentOS CD"""

        cdObj = GeneralInstallSrc(self.invalidCentOSLocalPath)
        assert cdObj.ostype != "centos"

    def test_CentOSCDPathExists(self):
        """Test if the path does indeed contain CentOS media"""
        
        centosObj = GeneralInstallSrc(self.centOSLocalPath)
        assert centosObj.verifyLocalSrcPath() is True
        
    def test_CentOSCDPathNotExists(self):
        """Test if the path does indeed contain CentOS media"""
        
        centosObj = GeneralInstallSrc(self.invalidCentOSLocalPath)
        assert centosObj.verifyLocalSrcPath() is False


class TestFedoraDetection:
    """Test suite for detecting Fedora installation sources"""

    def setup_method(self, method):
        """Sets up mock paths"""

        self.setupFedora()

    def teardown_method(self, method):
        """Clean up after done"""

        self.teardownFedora()

    def setupFedora(self):
        """Fedora-centric housekeeping"""

        self.fedoraLocalPath = path(tempfile.mkdtemp(dir='/tmp'))

        # create a directory and delete it immediately after. 
        self.invalidFedoraLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        self.invalidFedoraLocalPath.rmdir()

        path(self.fedoraLocalPath / 'isolinux').mkdir()
        path(self.fedoraLocalPath / 'isolinux/vmlinuz').touch()
        path(self.fedoraLocalPath / 'isolinux/initrd.img').touch()
        path(self.fedoraLocalPath / 'images').mkdir()
        path(self.fedoraLocalPath / 'Fedora').mkdir()
        path(self.fedoraLocalPath / 'Fedora/RPMS').mkdir()
        path(self.fedoraLocalPath / 'Fedora/base').mkdir()

    def teardownFedora(self):
        """Fedora-centric housekeeping in reverse"""

        path(self.fedoraLocalPath / 'isolinux/vmlinuz').remove()
        path(self.fedoraLocalPath / 'isolinux/initrd.img').remove()
        path(self.fedoraLocalPath / 'isolinux').rmdir()
        path(self.fedoraLocalPath / 'images').rmdir()
        path(self.fedoraLocalPath / 'Fedora/RPMS').rmdir()
        path(self.fedoraLocalPath / 'Fedora/base').rmdir()
        path(self.fedoraLocalPath / 'Fedora').rmdir()
        self.fedoraLocalPath.rmdir()

    def test_IsFedoraCD(self):
        """Test if the CD is a Fedora CD"""

        cdObj = GeneralInstallSrc(self.fedoraLocalPath)
        assert cdObj.ostype == "fedora"
        
    def test_IsNotFedoraCD(self):
        """Test if the CD is not a Fedora CD"""

        cdObj = GeneralInstallSrc(self.invalidFedoraLocalPath)
        assert cdObj.ostype != "fedora"

    def test_FedoraCDPathExists(self):
        """Test if the path does indeed contain Fedora media"""

        fedoraObj = GeneralInstallSrc(self.fedoraLocalPath)
        assert fedoraObj.verifyLocalSrcPath() is True

    def test_FedoraCDPathNotExists(self):
        """Test if the path does indeed contain Fedora media"""

        fedoraObj = GeneralInstallSrc(self.invalidFedoraLocalPath)
        assert fedoraObj.verifyLocalSrcPath() is False

