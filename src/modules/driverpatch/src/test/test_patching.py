#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.util import tools as utiltools
from kusu.core import database as db
from kusu.driverpatch import DriverPatchController
import urllib
from path import path

RPMDIR = path('/tmp/kusu/driverpatch-test-assets')
if not RPMDIR.exists(): RPMDIR.makedirs()
BASEURL = 'http://www.osgdc.org/pub/build/tests/modules/driverpatch'
KRPM1_URL = BASEURL + '/' + 'kernel-2.6.18-1.2798.fc6.i586.rpm'
KRPM1 = 'kernel-2.6.18-1.2798.fc6.i586.rpm'

def download(url,dest):
    urllib.urlretrieve(url,dest)

def setUp():
    global RPMDIR
    global KRPM1_URL
    global KRPM1
    dest = RPMDIR / KRPM1
    if not dest.exists(): download(KRPM1_URL,dest)

    
def tearDown():
    pass
    #if RPMDIR.exists(): RPMDIR.rmtree()

class TestPatchingKernel(object):
    """ Test suite for driverpatch kernel patching.
    """

    def setUp(self):
        
        self.scratchdir = path(utiltools.mkdtemp())
        self.kusudb = self.scratchdir / 'kusu.db'
        self.dbinst = db.DB('sqlite', self.kusudb)
        self.dbinst.createTables()
        
        self.controller = DriverPatchController(self.dbinst)
        
    def tearDown(self):
        if self.scratchdir.exists(): self.scratchdir.rmtree()
        
    def testExtractKernelFori586DefaultName(self):
        """ Testing i586 kernel extraction with default name.
        """
        krpm = path(RPMDIR) / KRPM1
        if not krpm.exists():
            assert False, 'Kernel rpm not found!'
            
        tftpbootdir = self.scratchdir / 'tftpboot'
        if not tftpbootdir.exists(): tftpbootdir.mkdir()
        self.controller.copyKernel(krpm,tftpbootdir)
        newkernel = tftpbootdir / 'vmlinuz-2.6.18-1.2798.fc6'
        assert newkernel.exists()


    def testExtractKernelFori586CustomName(self):
        """ Testing i586 kernel extraction with custom name.
        """
        krpm = path(RPMDIR) / KRPM1
        newkernelname = 'mykernel'
        if not krpm.exists():
            assert False, 'Kernel rpm not found!'

        tftpbootdir = self.scratchdir / 'tftpboot'
        if not tftpbootdir.exists(): tftpbootdir.mkdir()
        self.controller.copyKernel(krpm,tftpbootdir,newkernelname)
        newkernel = tftpbootdir / newkernelname
        assert newkernel.exists()
        
    def testExtractKernelModulesDirFori586(self):
        """ Testing i586 kernel modules dir extraction.
        """
        krpm = path(RPMDIR) / KRPM1
        if not krpm.exists():
            assert False, 'Kernel rpm not found!'

        modulesdir = self.scratchdir / 'modules'
        if not modulesdir.exists(): modulesdir.mkdir()
        self.controller.extractKernelModulesDir(krpm,modulesdir)
        # find one well known asset
        miiko = modulesdir / 'kernel/drivers/net/mii.ko'
        assert miiko.exists()
        
    def testPackModulesCgzFori586(self):
        """ Test packaging of modules.cgz archive.
        """
        krpm = path(RPMDIR) / KRPM1
        if not krpm.exists():
            assert False, 'Kernel rpm not found!'

        modulesdir = self.scratchdir / 'modules'
        modulescgz = self.scratchdir / 'modules.cgz'
        if not modulesdir.exists(): modulesdir.mkdir()
        self.controller.extractKernelModulesDir(krpm,modulesdir)
        self.controller.convertKmodDirToModulesArchive(modulesdir,modulescgz)
        assert modulescgz.exists()
        
    def testKernelVersionArch(self):
        """ Validate the kernel version and arch for the modules.
        """
        krpm = path(RPMDIR) / KRPM1
        if not krpm.exists():
            assert False, 'Kernel rpm not found!'

        modulesdir = self.scratchdir / 'modules'
        if not modulesdir.exists(): modulesdir.mkdir()
        self.controller.extractKernelModulesDir(krpm,modulesdir)
        kver = self.controller.getKernelVersion(modulesdir)
        karch = self.controller.getKernelArch(modulesdir)
        
        assert kver == '2.6.18-1.2798.fc6'
        assert karch == 'i586'


        


        
    