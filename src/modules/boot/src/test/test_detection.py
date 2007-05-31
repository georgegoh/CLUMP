#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from kusu.boot.distro import DistroFactory
from path import path
import tempfile

class TestCentOSDetection:
    """Test suite for detecting CentOS installation sources"""
    
    def setUp(self):
        """Sets up mock paths"""
        
        self.setupCentOS()
     
    def teardown_method(self):
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
        path(self.centOSLocalPath / 'isolinux/isolinux.bin').touch()
        path(self.centOSLocalPath / 'images').mkdir()
        path(self.centOSLocalPath / 'images/stage2.img').touch()        
        path(self.centOSLocalPath / 'CentOS').mkdir()
        path(self.centOSLocalPath / 'CentOS/RPMS').mkdir()
        path(self.centOSLocalPath / 'CentOS/base').mkdir()


        # create an additional media type 
        # (as in the layout for disc media 2, 3, ..)
        self.additionalCentOSMedia = path(tempfile.mkdtemp(dir='/tmp'))
        path(self.additionalCentOSMedia / 'CentOS').mkdir()
        path(self.additionalCentOSMedia / 'CentOS/RPMS').mkdir()
        
    def teardownCentOS(self):
        """CentOS-centric housekeeping in reverse"""
      
        path(self.centOSLocalPath / 'isolinux/vmlinuz').remove()
        path(self.centOSLocalPath / 'isolinux/initrd.img').remove() 
        path(self.centOSLocalPath / 'isolinux/isolinux.bin').remove() 
        path(self.centOSLocalPath / 'isolinux').rmdir()
        path(self.centOSLocalPath / 'images/stage2.img').remove()
        path(self.centOSLocalPath / 'images').rmdir()
        path(self.centOSLocalPath / 'CentOS/RPMS').rmdir()
        path(self.centOSLocalPath / 'CentOS/base').rmdir()
        path(self.centOSLocalPath / 'CentOS').rmdir()
        self.centOSLocalPath.rmdir()
        
        self.additionalCentOSMedia.rmtree()
        
    def test_IsCentOSCD(self):
        """Test if the CD is a CentOS CD"""
        
        cdObj = DistroFactory(self.centOSLocalPath)
        try:
            assert cdObj.ostype == "centos"
        except:
            assert False

    def test_IsAdditionalCentOSCD(self):
        """Test if the CD is an additional CentOS CD"""
        
        cdObj = DistroFactory(self.additionalCentOSMedia)
        try:
            assert cdObj.ostype == "centos"
        except:
            assert False


    def test_IsNotCentOSCD(self):
        """Test if the CD is not a CentOS CD"""

        cdObj = DistroFactory(self.invalidCentOSLocalPath)
        try:
            assert cdObj.ostype != "centos"
        except:
            assert False

    def test_CentOSCDPathExists(self):
        """Test if the path does indeed contain CentOS media"""
        
        centosObj = DistroFactory(self.centOSLocalPath)
        try:
            assert centosObj.verifyLocalSrcPath() is True
        except:
            assert False
        
    def test_CentOSCDPathNotExists(self):
        """Test if the path does indeed contain CentOS media"""
        
        centosObj = DistroFactory(self.invalidCentOSLocalPath)
        try:
            assert centosObj.verifyLocalSrcPath() is False
        except:
            assert False


class TestFedoraDetection:
    """Test suite for detecting Fedora installation sources"""

    def setUp(self):
        """Sets up mock paths"""

        self.setupFedora()

    def tearDown(self):
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
        
        # create an additional media type 
        # (as in the layout for disc media 2, 3, ..)
        self.additionalFedoraMedia = path(tempfile.mkdtemp(dir='/tmp'))
        path(self.additionalFedoraMedia / 'Fedora').mkdir()
        path(self.additionalFedoraMedia / 'Fedora/RPMS').mkdir()

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
        self.additionalFedoraMedia.rmtree()

    def test_IsFedoraCD(self):
        """Test if the CD is a Fedora CD"""

        cdObj = DistroFactory(self.fedoraLocalPath)
        assert cdObj.ostype == "fedora"

            
    def test_IsAdditionalFedoraCD(self):
        """Test if the CD is an additional Fedora CD"""
        
        cdObj = DistroFactory(self.additionalFedoraMedia)
        assert cdObj.ostype == "fedora"

        
    def test_IsNotFedoraCD(self):
        """Test if the CD is not a Fedora CD"""

        cdObj = DistroFactory(self.invalidFedoraLocalPath)
        assert cdObj.ostype != "fedora"

    def test_FedoraCDPathExists(self):
        """Test if the path does indeed contain Fedora media"""

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        assert fedoraObj.verifyLocalSrcPath() is True


    def test_FedoraCDPathNotExists(self):
        """Test if the path does indeed contain Fedora media"""

        fedoraObj = DistroFactory(self.invalidFedoraLocalPath)
        assert fedoraObj.verifyLocalSrcPath() is False


