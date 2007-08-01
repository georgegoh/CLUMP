#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from kusu.boot.distro import DistroFactory
from path import path
import tempfile

class TestCentOS4Detection:
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



class TestFedora6Detection:
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
        path(self.fedoraLocalPath / 'isolinux/isolinux.bin').touch()
        path(self.fedoraLocalPath / 'isolinux/vmlinuz').touch()
        path(self.fedoraLocalPath / 'isolinux/initrd.img').touch()
        path(self.fedoraLocalPath / 'images').mkdir()
        path(self.fedoraLocalPath / 'images/stage2.img').touch()
        path(self.fedoraLocalPath / 'Fedora').mkdir()
        path(self.fedoraLocalPath / 'Fedora/RPMS').mkdir()
        path(self.fedoraLocalPath / 'Fedora/base').mkdir()

        f = open(path(self.fedoraLocalPath / '.discinfo'), 'w')
        f.write('1161131669.029329\n')
        f.write('Fedora Core 6\n')
        f.write('i386\n')
        f.write('1,2,3,4,5\n')
        f.write('Fedora/base\n')
        f.write('Fedora/RPMS\n')
        f.write('Fedora/pixmaps\n')
        f.close()
        
        # create an additional media type 
        # (as in the layout for disc media 2, 3, ..)
        self.additionalFedoraMedia = path(tempfile.mkdtemp(dir='/tmp'))
        path(self.additionalFedoraMedia / 'Fedora').mkdir()
        path(self.additionalFedoraMedia / 'Fedora/RPMS').mkdir()

    def teardownFedora(self):
        """Fedora-centric housekeeping in reverse"""

        path(self.fedoraLocalPath / 'isolinux/vmlinuz').remove()
        path(self.fedoraLocalPath / 'isolinux/initrd.img').remove()
        path(self.fedoraLocalPath / 'isolinux/isolinux.bin').remove()
        path(self.fedoraLocalPath / 'isolinux').rmdir()
        path(self.fedoraLocalPath / 'images/stage2.img').remove()
        path(self.fedoraLocalPath / 'images').rmdir()
        path(self.fedoraLocalPath / 'Fedora/RPMS').rmdir()
        path(self.fedoraLocalPath / 'Fedora/base').rmdir()
        path(self.fedoraLocalPath / 'Fedora').rmdir()
        path(self.fedoraLocalPath / '.discinfo').remove()
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

    def test_FedoraCDArch(self):
        """Test if the arch is correct for the Fedora media"""

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        assert fedoraObj.getArch() == 'i386'

        

class TestRHEL5Detection:
    """Test suite for detecting RHEL 5 installation sources"""

    def setUp(self):
        """Sets up mock paths"""

        self.setupRHEL(5)

    def tearDown(self):
        """Clean up after done"""

        self.teardownRHEL(5)

    def setupRHEL(self, version):
        """RHEL-centric housekeeping"""

        # Can be moved to allow all RHEL test to use the same setup
        if version == 5:
            self.rhelLocalPath = path(tempfile.mkdtemp(dir='/tmp'))

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
    
            f = open(path(self.rhelLocalPath / '.discinfo'), 'w')
            f.write('1170972069.396645\n')
            f.write('Red Hat Enterprise Linux Server 5\n')
            f.write('i386\n')
            f.write('1\n')
            f.write('Server/base\n')
            f.write('Server/RPMS\n')
            f.write('Server/pixmaps\n')
            f.close()

            # create an additional media type 
            # (as in the layout for disc media 2, 3, ..)
            self.additionalRHELMedia = path(tempfile.mkdtemp(dir='/tmp'))
            path(self.additionalRHELMedia / 'Server').mkdir()
            path(self.additionalRHELMedia / 'Cluster').mkdir()
            path(self.additionalRHELMedia / 'ClusterStorage').mkdir()
            path(self.additionalRHELMedia / 'VT').mkdir()
 
        elif version == '4':
            pass

    def teardownRHEL(self, version):
        """RHEL-centric housekeeping in reverse"""

        if version == 5:
            path(self.rhelLocalPath / 'isolinux/vmlinuz').remove()
            path(self.rhelLocalPath / 'isolinux/initrd.img').remove()
            path(self.rhelLocalPath / 'isolinux/isolinux.bin').remove()
            path(self.rhelLocalPath / 'isolinux').rmdir()
            path(self.rhelLocalPath / 'images/stage2.img').remove()
            path(self.rhelLocalPath / 'images').rmdir()
            path(self.rhelLocalPath / 'Server/repodata').rmdir()
            path(self.rhelLocalPath / 'Server').rmdir()
            path(self.rhelLocalPath / 'Cluster/repodata').rmdir()
            path(self.rhelLocalPath / 'Cluster').rmdir()
            path(self.rhelLocalPath / 'ClusterStorage/repodata').rmdir()
            path(self.rhelLocalPath / 'ClusterStorage').rmdir()
            path(self.rhelLocalPath / 'VT/repodata').rmdir()
            path(self.rhelLocalPath / 'VT').rmdir()
            path(self.rhelLocalPath / '.discinfo').remove()
            self.rhelLocalPath.rmdir()
            self.additionalRHELMedia.rmtree()
        elif version == '4':
            pass

    def test_IsRHELCD(self):
        """Test if the CD is a RHEL CD"""

        cdObj = DistroFactory(self.rhelLocalPath)
        assert cdObj.ostype == "rhel"

            
    def test_IsAdditionalRHELCD(self):
        """Test if the CD is an additional RHEL CD"""
        
        cdObj = DistroFactory(self.additionalRHELMedia)
        assert cdObj.ostype == "rhel"

        
    def test_IsNotRHELCD(self):
        """Test if the CD is not a RHEL CD"""

        cdObj = DistroFactory(self.invalidRHELLocalPath)
        assert cdObj.ostype != "rhel"

    def test_RHELCDPathExists(self):
        """Test if the path does indeed contain RHEL media"""

        rhelObj = DistroFactory(self.rhelLocalPath)
        assert rhelObj.verifyLocalSrcPath() is True


    def test_RHELCDPathNotExists(self):
        """Test if the path does indeed contain RHEL media"""

        rhelObj = DistroFactory(self.invalidRHELLocalPath)
        assert rhelObj.verifyLocalSrcPath() is False

    def test_RHELCDArch(self):
        """Test if the arch is correct for the RHEL media"""
        
        rhelObj = DistroFactory(self.rhelLocalPath)
        assert rhelObj.getArch() == 'i386'


