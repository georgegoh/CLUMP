#!/usr/bin/env python
# $Id: test_detection.py 2110 2009-02-27 21:36:10Z ggoh $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import os
from kusu.boot.distro import DistroFactory
from path import path
import tempfile
import urllib

url = 'http://www.osgdc.org/pub/build/tests/modules/boot/'
centos_release = {'0': 'centos-release-notes-5.0.0-2.i386.rpm',
                  '1': 'centos-release-notes-5.1.0-2.i386.rpm',
                  '2': 'centos-release-notes-5.2-2.i386.rpm'}
rhel_release = {'0': 'redhat-release-5Server-5.0.0.9.i386.rpm', 
                '1': 'redhat-release-5Server-5.1.0.2.i386.rpm', 
                '2': 'redhat-release-5Server-5.2.0.4.i386.rpm'}

sles_content = {'0': 'PRODUCT SUSE SLES\nVERSION 10\n',
                '1': 'PRODUCT SUSE_SLES_SP1\nVERSION 10.1-0\n',
                '2': 'PRODUCT SUSE_SLES_SP2\nVERSION 10.2-0\n'}

opensuse_content = {'3': 'PRODUCT openSUSE-DVD5-download\nVERSION 10.3\n'}

def downloadFiles(fn):
    global url

    urllib.urlretrieve(url + fn.basename(), fn)
                                                                     
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

        # set up some kernel packages
        path(self.centOSLocalPath / 'CentOS/RPMS/kernel-2.6.9-99.i586.rpm').touch()
        path(self.centOSLocalPath / 'CentOS/RPMS/kernel-devel-2.6.9-99.noarch.rpm').touch()
        path(self.centOSLocalPath / 'CentOS/RPMS/kernel-docs-2.6.9-99.noarch.rpm').touch()


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
        path(self.centOSLocalPath / 'CentOS/RPMS').rmtree()
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
            
    def test_CentosGetKernelPackages(self):
        """ Test to get the kernel packages. """
        
        centosObj = DistroFactory(self.centOSLocalPath)
        li = [path(self.centOSLocalPath / 'CentOS/RPMS/kernel-2.6.9-99.i586.rpm')]
        
        assert centosObj.getKernelPackages() == li
        assert centosObj.getKernelRpms() == li


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
        
        # set up some kernel packages
        path(self.fedoraLocalPath / 'Fedora/RPMS/kernel-2.6.9-99.i586.rpm').touch()
        path(self.fedoraLocalPath / 'Fedora/RPMS/kernel-devel-2.6.9-99.noarch.rpm').touch()
        path(self.fedoraLocalPath / 'Fedora/RPMS/kernel-docs-2.6.9-99.noarch.rpm').touch()
        
        # create an additional media type 
        # (as in the layout for disc media 2, 3, ..)
        self.additionalFedoraMedia = path(tempfile.mkdtemp(dir='/tmp'))
        path(self.additionalFedoraMedia / 'Fedora').mkdir()
        path(self.additionalFedoraMedia / 'Fedora/RPMS').mkdir()

        f = open(path(self.additionalFedoraMedia / '.discinfo'), 'w')
        f.write('1161131669.029329\n')
        f.write('Fedora Core 6\n')
        f.write('i386\n')
        f.write('2\n')
        f.write('Fedora/base\n')
        f.write('Fedora/RPMS\n')
        f.write('Fedora/pixmaps\n')
        f.close()

    def teardownFedora(self):
        """Fedora-centric housekeeping in reverse"""

        path(self.fedoraLocalPath / 'isolinux/vmlinuz').remove()
        path(self.fedoraLocalPath / 'isolinux/initrd.img').remove()
        path(self.fedoraLocalPath / 'isolinux/isolinux.bin').remove()
        path(self.fedoraLocalPath / 'isolinux').rmdir()
        path(self.fedoraLocalPath / 'images/stage2.img').remove()
        path(self.fedoraLocalPath / 'images').rmdir()
        path(self.fedoraLocalPath / 'Fedora/RPMS').rmtree()
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
        assert cdObj.getVersion() == "6"
        assert cdObj.getArch() == "i386"
        
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

    def test_FedoraCDVersion(self):
        """Test if the version is correct for the Fedora media"""

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        assert fedoraObj.getVersion() == '6'

    def test_FedoraGetKernelPackages(self):
        """ Test to get the kernel packages. """

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        li = [path(self.fedoraLocalPath / 'Fedora/RPMS/kernel-2.6.9-99.i586.rpm')]

        assert fedoraObj.getKernelPackages() == li
        assert fedoraObj.getKernelRpms() == li

class TestFedora7Detection:
    """Test suite for detecting Fedora 7 installation sources"""

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

        f = open(path(self.fedoraLocalPath / '.discinfo'), 'w')
        f.write('1180276843.561677\n')
        f.write('"Fedora 7"\n')
        f.write('i386\n')
        f.write('1\n')
        f.write('Fedora/base\n')
        f.write('/srv/pungi/f7gold/7/Fedora/i386/os/Fedora\n')
        f.write('Fedora/pixmaps\n')
        f.close()

        # set up some kernel packages
        path(self.fedoraLocalPath / 'Fedora/kernel-2.6.21-1.3194.fc7.i586.rpm').touch()
        path(self.fedoraLocalPath / 'Fedora/kernel-devel-2.6.21-1.3194.fc7.i586.rpm').touch()
        path(self.fedoraLocalPath / 'Fedora/kernel-doc-2.6.21-1.3194.fc7.noarch.rpm').touch()
        
    def teardownFedora(self):
        """Fedora-centric housekeeping in reverse"""

        path(self.fedoraLocalPath / 'isolinux/vmlinuz').remove()
        path(self.fedoraLocalPath / 'isolinux/initrd.img').remove()
        path(self.fedoraLocalPath / 'isolinux/isolinux.bin').remove()
        path(self.fedoraLocalPath / 'isolinux').rmdir()
        path(self.fedoraLocalPath / 'images/stage2.img').remove()
        path(self.fedoraLocalPath / 'images').rmdir()
        path(self.fedoraLocalPath / 'Fedora').rmtree()
        path(self.fedoraLocalPath / '.discinfo').remove()
        self.fedoraLocalPath.rmdir()

    def test_IsFedoraCD(self):
        """Test if the CD is a Fedora CD"""

        cdObj = DistroFactory(self.fedoraLocalPath)
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

    def test_FedoraCDVersion(self):
        """Test if the version is correct for the Fedora media"""

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        assert fedoraObj.getVersion() == '7'

    def test_FedoraGetKernelPackages(self):
        """ Test to get the kernel packages. """

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        li = [path(self.fedoraLocalPath / 'Fedora/kernel-2.6.21-1.3194.fc7.i586.rpm')]

        assert fedoraObj.getKernelPackages() == li
        assert fedoraObj.getKernelRpms() == li
 
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
            
            # set up some kernel packages
            path(self.rhelLocalPath / 'Server/kernel-2.6.9-99.i586.rpm').touch()
            path(self.rhelLocalPath / 'Server/kernel-devel-2.6.9-99.noarch.rpm').touch()
            path(self.rhelLocalPath / 'Server/kernel-docs-2.6.9-99.noarch.rpm').touch()

            # create an additional media type 
            # (as in the layout for disc media 2, 3, ..)
            self.additionalRHELMedia = path(tempfile.mkdtemp(dir='/tmp'))
            path(self.additionalRHELMedia / 'Server').mkdir()
            path(self.additionalRHELMedia / 'Cluster').mkdir()
            path(self.additionalRHELMedia / 'ClusterStorage').mkdir()
            path(self.additionalRHELMedia / 'VT').mkdir()
 
            f = open(path(self.additionalRHELMedia / '.discinfo'), 'w')
            f.write('1170972069.396645\n')
            f.write('Red Hat Enterprise Linux Server 5\n')
            f.write('i386\n')
            f.write('2\n')
            f.write('Server/base\n')
            f.write('Server/RPMS\n')
            f.write('Server/pixmaps\n')
            f.close()

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
            path(self.rhelLocalPath / 'Server').rmtree()
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
        assert cdObj.getVersion() == "5"
        assert cdObj.getArch() == "i386"
        
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

    def test_RHELCDVersion(self):
        """Test if the version is correct for the RHEL media"""
        
        rhelObj = DistroFactory(self.rhelLocalPath)
        assert rhelObj.getVersion() == '5'

    def test_RHELCDMajorVersion (self):
        """Test if the version is correct for the RHEL media"""

        rhelObj = DistroFactory(self.rhelLocalPath)
        assert rhelObj.getMajorVersion() == '5'
       
    def test_RHELCDMinorVersion (self):
        """Test if the version is correct for the RHEL media"""

        global rhel_release

        for minor in ['0', '1', '2']:
            downloadFiles(self.rhelLocalPath / 'Server' / rhel_release[minor])

            rhelObj = DistroFactory(self.rhelLocalPath)
            assert rhelObj.getMinorVersion() == minor

            (self.rhelLocalPath / 'Server' / rhel_release[minor]).remove()

    def test_RHELCDVersionString (self):
        """Test if the version is correct for the RHEL media"""

        global rhel_release

        for minor in ['0', '1', '2']:
            downloadFiles(self.rhelLocalPath / 'Server' / rhel_release[minor])

            rhelObj = DistroFactory(self.rhelLocalPath)
            assert rhelObj.getVersionString() == '5.' + minor

            (self.rhelLocalPath / 'Server' / rhel_release[minor]).remove()

    def test_RHELGetKernelPackages(self):
        """ Test to get the kernel packages. """

        rhelObj = DistroFactory(self.rhelLocalPath)
        li = [path(self.rhelLocalPath / 'Server/kernel-2.6.9-99.i586.rpm')]

        assert rhelObj.getKernelPackages() == li
        assert rhelObj.getKernelRpms() == li

class TestCentOS5Detection:
    """Test suite for detecting CentOS 5 installation sources"""

    def setUp(self):
        """Sets up mock paths"""

        self.setupCentOS(5)

    def tearDown(self):
        """Clean up after done"""

        self.teardownCentOS(5)

    def setupCentOS(self, version):
        """CentOS-centric housekeeping"""

        # Can be moved to allow all RHEL test to use the same setup
        if version == 5:
            self.centosLocalPath = path(tempfile.mkdtemp(dir='/tmp'))

            # create a directory and delete it immediately after. 
            self.invalidCentOSLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
            self.invalidCentOSLocalPath.rmdir()

            path(self.centosLocalPath / 'isolinux').mkdir()
            path(self.centosLocalPath / 'isolinux/vmlinuz').touch()
            path(self.centosLocalPath / 'isolinux/initrd.img').touch()
            path(self.centosLocalPath / 'isolinux/isolinux.bin').touch()
            path(self.centosLocalPath / 'images').mkdir()
            path(self.centosLocalPath / 'images/stage2.img').touch()
            path(self.centosLocalPath / 'CentOS').mkdir()
            path(self.centosLocalPath / 'repodata').mkdir()


            f = open(path(self.centosLocalPath / '.discinfo'), 'w')
            f.write('1170972069.396645\n')
            f.write('Final\n')
            f.write('i386\n')
            f.write('1\n')
            f.write('CentOS/base\n')
            f.write('/home/buildcentos/CENTOS/5.0/en/i386/CentOS\n')
            f.write('CentOS/pixmaps\n')
            f.close()
            
            # set up some kernel packages
            path(self.centosLocalPath / 'CentOS/kernel-2.6.9-99.i586.rpm').touch()
            path(self.centosLocalPath / 'CentOS/kernel-devel-2.6.9-99.noarch.rpm').touch()
            path(self.centosLocalPath / 'CentOS/kernel-docs-2.6.9-99.noarch.rpm').touch()

            # create an additional media type 
            # (as in the layout for disc media 2, 3, ..)
            self.additionalCentOSMedia = path(tempfile.mkdtemp(dir='/tmp'))
            path(self.additionalCentOSMedia / 'CentOS').mkdir()
 
            f = open(path(self.additionalCentOSMedia / '.discinfo'), 'w')
            f.write('1170972069.396645\n')
            f.write('Final\n')
            f.write('i386\n')
            f.write('2\n')
            f.write('CentOS/base\n')
            f.write('/home/buildcentos/CENTOS/5.0/en/i386/CentOS\n')
            f.write('CentOS/pixmaps\n')
            f.close()

        elif version == '4':
            pass

    def teardownCentOS(self, version):
        """RHEL-centric housekeeping in reverse"""

        if version == 5:
            path(self.centosLocalPath / 'isolinux/vmlinuz').remove()
            path(self.centosLocalPath / 'isolinux/initrd.img').remove()
            path(self.centosLocalPath / 'isolinux/isolinux.bin').remove()
            path(self.centosLocalPath / 'isolinux').rmdir()
            path(self.centosLocalPath / 'images/stage2.img').remove()
            path(self.centosLocalPath / 'images').rmdir()
            path(self.centosLocalPath / 'CentOS').rmtree()
            path(self.centosLocalPath / 'repodata').rmdir()
            path(self.centosLocalPath / '.discinfo').remove()
            self.centosLocalPath.rmdir()
            self.additionalCentOSMedia.rmtree()
        elif version == '4':
            pass

    def test_IsCentOSCD(self):
        """Test if the CD is a CentOS CD"""

        cdObj = DistroFactory(self.centosLocalPath)
        assert cdObj.ostype == "centos"

    def test_IsAdditionalCentOSCD(self):
        """Test if the CD is an additional CentOS CD"""
        
        cdObj = DistroFactory(self.additionalCentOSMedia)
        assert cdObj.ostype == "centos"
        assert cdObj.getVersion() == "5"
        assert cdObj.getArch() == "i386"
        
    def test_IsNotCentOSCD(self):
        """Test if the CD is not a CentOS CD"""

        cdObj = DistroFactory(self.invalidCentOSLocalPath)
        assert cdObj.ostype != "centos"

    def test_CentOSCDPathExists(self):
        """Test if the path does indeed contain CentOS media"""

        centosObj = DistroFactory(self.centosLocalPath)
        assert centosObj.verifyLocalSrcPath() is True

    def test_CentOSCDPathNotExists(self):
        """Test if the path does indeed contain CentOS media"""

        centosObj = DistroFactory(self.invalidCentOSLocalPath)
        assert centosObj.verifyLocalSrcPath() is False

    def test_CentOSCDArch(self):
        """Test if the arch is correct for the CentOS media"""
        
        centosObj = DistroFactory(self.centosLocalPath)
        assert centosObj.getArch() == 'i386'
   
    def test_CentOSCDVersion(self):
        """Test if the version is correct for the CentOS media"""
        
        centosObj = DistroFactory(self.centosLocalPath)
        assert centosObj.getVersion() == '5'
       
    def test_test_CentOSCDMajorVersion (self):
        """Test if the version is correct for the CentOS media"""

        centosObj = DistroFactory(self.centosLocalPath)
        assert centosObj.getMajorVersion() == '5'
       
    def test_CentOSCDMinorVersion (self):
        """Test if the version is correct for the CentOS media"""

        global centos_release

        for minor in ['0', '1', '2']:
            downloadFiles(self.centosLocalPath / 'CentOS' / centos_release[minor])

            centosObj = DistroFactory(self.centosLocalPath)
            assert centosObj.getMinorVersion() == minor

            (self.centosLocalPath / 'CentOS' / centos_release[minor]).remove()

    def test_CentOSCDVersionString (self):
        """Test if the version is correct for the CentOS media"""

        global centos_release

        for minor in ['0', '1', '2']:
            downloadFiles(self.centosLocalPath / 'CentOS' / centos_release[minor])

            centosObj = DistroFactory(self.centosLocalPath)
            assert centosObj.getVersionString() == '5.' + minor

            (self.centosLocalPath / 'CentOS' / centos_release[minor]).remove()

    def test_CentOSGetKernelPackages(self):
        """ Test to get the kernel packages. """

        centosObj = DistroFactory(self.centosLocalPath)
        li = [path(self.centosLocalPath / 'CentOS/kernel-2.6.9-99.i586.rpm')]

        assert centosObj.getKernelPackages() == li
        assert centosObj.getKernelRpms() == li

class TestFedora8Detection:
    """Test suite for detecting Fedora 8 installation sources"""

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
        path(self.fedoraLocalPath / 'isolinux/isolinux.bin').touch()
        path(self.fedoraLocalPath / 'images').mkdir()
        path(self.fedoraLocalPath / 'images/stage2.img').touch()
        path(self.fedoraLocalPath / 'Packages').mkdir()
        path(self.fedoraLocalPath / 'repodata').mkdir()

        f = open(path(self.fedoraLocalPath / '.treeinfo'), 'w')
        data = """
[general]
family = Fedora
timestamp = 1194015227.78
variant = Fedora
totaldiscs = 1
version = 8
discnum = 1
packagedir = Packages
arch = i386

[images-i386]
kernel = images/pxeboot/vmlinuz
initrd = images/pxeboot/initrd.img
boot.iso = images/boot.iso
diskboot.img = images/diskboot.img

[images-xen]
kernel = images/xen/vmlinuz
initrd = images/xen/initrd.img

[stage2]
instimage = images/minstg2.img
mainimage = images/stage2.img
"""
        f.write(data)

        f.close()

        # set up some kernel packages
        path(self.fedoraLocalPath / 'Packages/kernel-2.6.23.1-42.fc8.i586.rpm').touch()
        path(self.fedoraLocalPath / 'Packages/kernel-devel-2.6.23.1-42.fc8.i586.rpm').touch()
        path(self.fedoraLocalPath / 'Packages/kernel-doc-2.6.23.1-42.fc8.noarch.rpm').touch()


    def teardownFedora(self):
        """Fedora-centric housekeeping in reverse"""

        path(self.fedoraLocalPath / 'isolinux').rmtree()
        path(self.fedoraLocalPath / 'images').rmtree()
        path(self.fedoraLocalPath / 'Packages').rmtree()
        path(self.fedoraLocalPath / '.treeinfo').remove()
        self.fedoraLocalPath.rmtree()

    def test_IsFedora8DVD(self):
        """Test if the DVD is a Fedora 8 DVD"""

        dvdObj = DistroFactory(self.fedoraLocalPath)
        assert dvdObj.ostype == "fedora"

    def test_IsNotFedora8DVD(self):
        """Test if the DVD is not a Fedora DVD"""

        dvdObj = DistroFactory(self.invalidFedoraLocalPath)
        assert dvdObj.ostype != "fedora"

    def test_FedoraDVDPathExists(self):
        """Test if the path does indeed contain Fedora 8 media"""

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        assert fedoraObj.verifyLocalSrcPath() is True

    def test_FedoraCDPathNotExists(self):
        """Test if the path does indeed contain Fedora 8 media"""

        fedoraObj = DistroFactory(self.invalidFedoraLocalPath)
        assert fedoraObj.verifyLocalSrcPath() is False

    def test_FedoraDVDArch(self):
        """Test if the arch is correct for the Fedora 8 media"""

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        assert fedoraObj.getArch() == 'i386'

    def test_FedoraDVDVersion(self):
        """Test if the version is correct for the Fedora 8 media"""

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        assert fedoraObj.getVersion() == '8'

    def test_RHELGetKernelPackages(self):
        """ Test to get the kernel packages. """

        fedoraObj = DistroFactory(self.fedoraLocalPath)
        li = [path(self.fedoraLocalPath / 'Packages/kernel-2.6.23.1-42.fc8.i586.rpm')]

        assert fedoraObj.getKernelPackages() == li
        assert fedoraObj.getKernelRpms() == li



class TestSLES10Detection:
    """Test suite for detecting SLES 10 installation sources"""

    def setUp(self):
        """Sets up mock paths"""

        self.setupSLES(10)

    def tearDown(self):
        """Clean up after done"""

        self.teardownSLES(10)

    def setupSLES(self, version):
        """SLES-centric housekeeping"""

        self.slesLocalPath = path(tempfile.mkdtemp(dir='/tmp'))

        # create a directory and delete it immediately after. 
        self.invalidSLESLocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        self.invalidSLESLocalPath.rmdir()

        path(self.slesLocalPath / 'boot').mkdir()
        path(self.slesLocalPath / 'boot/i386').mkdir()
        path(self.slesLocalPath / 'boot/i386/loader').mkdir()
        path(self.slesLocalPath / 'boot/i386/loader/isolinux.bin').touch()
        path(self.slesLocalPath / 'boot/i386/loader/initrd').touch()
        path(self.slesLocalPath / 'boot/i386/loader/linux').touch()
        path(self.slesLocalPath / 'suse').mkdir()
        path(self.slesLocalPath / 'suse/i586').mkdir()
        path(self.slesLocalPath / 'suse/i686').mkdir()
        path(self.slesLocalPath / 'suse/noarch').mkdir()

        # set up some kernel packages
        path(self.slesLocalPath / 'suse/i586/kernel-smp-2.6.16.60-0.21.i586.rpm').touch()
        path(self.slesLocalPath / 'suse/i586/kernel-source-2.6.16.60-0.21.i586.rpm').touch()
        path(self.slesLocalPath / 'suse/i586/kernel-xen-2.6.16.60-0.21.i586.rpm').touch()
        path(self.slesLocalPath / 'suse/i586/kernel-default-2.6.16.60-0.21.i586.rpm').touch()

    def setupContent(self, minorVersion):

        global sles_content

        content = self.slesLocalPath / 'content'
            
        f = open(content, 'w')
        f.write(sles_content[minorVersion])
        f.close()

        return content

    def teardownSLES(self, version):
        """RHEL-centric housekeeping in reverse"""

        path(self.slesLocalPath).rmtree()
        #self.rhelLocalPath.rmdir()

    def test_IsSLESCD(self):
        """Test if the CD is a SLES CD"""

        cdObj = DistroFactory(self.slesLocalPath)
        assert cdObj.ostype == "sles"

            
    def test_IsAdditionalSLESCD(self):
        """Test if the CD is an additional SLES CD"""
        
        #cdObj = DistroFactory(self.additionalRHELMedia)
        #assert cdObj.ostype == "rhel"
        #assert cdObj.getVersion() == "5"
        #assert cdObj.getArch() == "i386"
        return

        
    def test_IsNotSLESCD(self):
        """Test if the CD is not a SLES CD"""

        cdObj = DistroFactory(self.invalidSLESLocalPath)
        assert cdObj.ostype != "sles"

    def test_SLESCDPathExists(self):
        """Test if the path does indeed contain SLES media"""

        slesObj = DistroFactory(self.slesLocalPath)
        assert slesObj.verifyLocalSrcPath() is True

    def test_SLESCDPathNotExists(self):
        """Test if the path does indeed contain SLES media"""

        slesObj = DistroFactory(self.invalidSLESLocalPath)
        assert slesObj.verifyLocalSrcPath() is False

    def test_SLESCDArch(self):
        """Test if the arch is correct for the SLES media"""
        
        slesObj = DistroFactory(self.slesLocalPath)

        assert slesObj.getArch() == 'i386'

    def test_SLESCDVersion(self):
        """Test if the version is correct for the SLES media"""
        
        for minor in ['0', '1', '2']:
            content = self.setupContent(minor)

            slesObj = DistroFactory(self.slesLocalPath)
            assert slesObj.getVersion() == '10'
            
            content.remove()

    def test_SLESCDMajorVersion (self):
        """Test if the version is correct for the SLES media"""

        
        for minor in ['0', '1', '2']:
            content = self.setupContent(minor)
            slesObj = DistroFactory(self.slesLocalPath)
            assert slesObj.getMajorVersion() == '10'
            content.remove()
       
    def test_SLESCDMinorVersion (self):
        """Test if the version is correct for the SLES media"""

        for minor in ['0', '1', '2']:
            content = self.setupContent(minor)

            slesObj = DistroFactory(self.slesLocalPath)

            assert slesObj.getMinorVersion() == minor

            content.remove()

    def test_SLESCDVersionString (self):
        """Test if the version is correct for the SLES media"""

        for minor in ['0', '1', '2']:
        
            content = self.setupContent(minor)
            slesObj = DistroFactory(self.slesLocalPath)
            assert slesObj.getVersionString() == '10.' + minor
            content.remove()

    def test_SLESGetKernelPackages(self):
        """ Test to get the kernel packages. """
       
        slesObj = DistroFactory(self.slesLocalPath)

        li = [path(self.slesLocalPath / 'suse/i586/kernel-default-2.6.16.60-0.21.i586.rpm')]

        assert slesObj.getKernelPackages() == li
        assert slesObj.getKernelRpms() == li

class TestOpenSUSE103Detection:
    """Test suite for detecting openSUSE 10.3 installation sources"""

    def setUp(self):
        """Sets up mock paths"""

        self.setupOpenSUSE103('10.3')

    def tearDown(self):
        """Clean up after done"""
        
        self.teardownOpenSUSE103('10.3')

    def setupOpenSUSE103(self, version):
        """openSUSE-centric housekeeping"""

        self.suseLocalPath = path(tempfile.mkdtemp(dir='/tmp'))

        # create a directory and delete it immediately after. 
        self.invalidSUSELocalPath = path(tempfile.mkdtemp(dir='/tmp'))
        self.invalidSUSELocalPath.rmdir()

        path(self.suseLocalPath / 'boot').mkdir()
        path(self.suseLocalPath / 'boot/i386').mkdir()
        path(self.suseLocalPath / 'boot/i386/loader').mkdir()
        path(self.suseLocalPath / 'boot/i386/loader/isolinux.bin').touch()
        path(self.suseLocalPath / 'boot/i386/loader/initrd').touch()
        path(self.suseLocalPath / 'boot/i386/loader/linux').touch()
        path(self.suseLocalPath / 'suse').mkdir()
        path(self.suseLocalPath / 'suse/i586').mkdir()
        path(self.suseLocalPath / 'suse/i686').mkdir()
        path(self.suseLocalPath / 'suse/noarch').mkdir()
        path(self.suseLocalPath / 'openSUSE10_3_LOCAL.exe').touch()

        # set up some kernel packages
        path(self.suseLocalPath / 'suse/i586/kernel-bigsmp-2.6.22.5-31.i586.rpm').touch()
        path(self.suseLocalPath / 'suse/i586/kernel-source-2.6.22.5-31.i586.rpm').touch()
        path(self.suseLocalPath / 'suse/i586/kernel-xen-2.6.22.5-31.i586.rpm').touch()
        path(self.suseLocalPath / 'suse/i586/kernel-default-2.6.22.5-31.i586.rpm').touch()

    def setupContent(self, minorVersion):

        global opensuse_content

        content = self.suseLocalPath / 'content'
            
        f = open(content, 'w')
        f.write(opensuse_content[minorVersion])
        f.close()

        return content

    def teardownOpenSUSE103(self, version):
        """openSUSE-centric housekeeping in reverse"""

        path(self.suseLocalPath).rmtree()

    def test_IsOpenSUSE103CD(self):
        """Test if the CD is a SLES CD"""

        cdObj = DistroFactory(self.suseLocalPath)
        assert cdObj.ostype == "opensuse"

            
    def test_IsAdditionalOpenSUSE103CD(self):
        """Test if the CD is an additional open SUSE CD"""
        
        #cdObj = DistroFactory(self.additionalRHELMedia)
        #assert cdObj.ostype == "rhel"
        #assert cdObj.getVersion() == "5"
        #assert cdObj.getArch() == "i386"
        return

        
    def test_IsNotOpenSUSE103CD(self):
        """Test if the CD is not a open SUSE CD"""

        cdObj = DistroFactory(self.invalidSUSELocalPath)
        assert cdObj.ostype != "opensuse"

    def test_OpenSUSE103CDPathExists(self):
        """Test if the path does indeed contain openSUSE media"""

        obj = DistroFactory(self.suseLocalPath)
        assert obj.verifyLocalSrcPath() is True

    def test_OpenSUSE103CDPathNotExists(self):
        """Test if the path does indeed contain openSUSE media"""

        obj = DistroFactory(self.invalidSUSELocalPath)
        assert obj.verifyLocalSrcPath() is False

    def test_OpenSUSE103CDArch(self):
        """Test if the arch is correct for the openSUSE media"""
        
        obj = DistroFactory(self.suseLocalPath)

        assert obj.getArch() == 'i386'

    def test_OpenSUSE103CDVersion(self):
        """Test if the version is correct for the openSUSE media"""
        
        content = self.setupContent('3')

        obj = DistroFactory(self.suseLocalPath)
        assert obj.getVersion() == '10.3'
        
        content.remove()

    def test_OpenSUSE103CDMajorVersion (self):
        """Test if the version is correct for the openSUSE media"""

        content = self.setupContent('3')
        obj = DistroFactory(self.suseLocalPath)
        assert obj.getMajorVersion() == '10'
        content.remove()
       
    def test_OpenSUSE103CDMinorVersion (self):
        """Test if the version is correct for the openSUSE media"""

        content = self.setupContent('3')
        obj = DistroFactory(self.suseLocalPath)
        assert obj.getMinorVersion() == '3'
        content.remove()

    def test_OpenSUSECDVersionString (self):
        """Test if the version is correct for the openSUSE media"""

        content = self.setupContent('3')
        obj = DistroFactory(self.suseLocalPath)
        assert obj.getVersionString() == '10.3'
        content.remove()

    def test_OpenSUSE103GetKernelPackages(self):
        """ Test to get the kernel packages. """
       
        obj = DistroFactory(self.suseLocalPath)

        li = [path(self.suseLocalPath / 'suse/i586/kernel-default-2.6.22.5-31.i586.rpm')]

        assert obj.getKernelPackages() == li
        assert obj.getKernelRpms() == li

