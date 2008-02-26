#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module handles driverpatch operations dealing with kernel packages
"""


from path import path
from kusu.util.errors import FileDoesNotExistError, DirDoesNotExistError
from kusu.util import rpmtool, tools


class RPMPackage(object):

        def __init__(self, filepath):
            """ Initializes this class with the filepath of the kernel rpm package.
            """
            if not path(filepath).exists: raise FileDoesNotExistError
            self.filepath = path(filepath).abspath()
            self.rpmfile = rpmtool.RPM(str(self.filepath))
            
        def getKernelModuleName(self):
            """ Returns the module name contained in this package. 
            """
            # FIXME: this is totally relying on the name of the rpm
            # package is really the name of the module too. Which is
            # dangerous and silly

            return self.rpmfile.name
            
        def getKernelModuleVersion(self):
            """ Returns the module version string.
            """
            # FIXME: this is totally relying on the version of the rpm
            # package is really the version of the module too. Which is
            # dangerous and silly
            
            return self.rpmfile.version
            
        def isKernel(self):
            """ Check if the package is a kernel package or not. Basically the existence of the vmlinuz file determines this check.
            """
            
            tmpdir = path(tools.mkdtemp())
            self.unpack(tmpdir)
            
            li = [ f for f in tmpdir.walkfiles('vmlinuz*')]
            
            if tmpdir.exists(): tmpdir.rmtree()
            
            if li: return True
            
            return False

        def isKernelModule(self):
            """ Check if the package is a kernel module package or not. Basically the existence of any ko files determines this check.
            """

            tmpdir = path(tools.mkdtemp())
            self.unpack(tmpdir)

            li = [ f for f in tmpdir.walkfiles('*.ko*')]

            if tmpdir.exists(): tmpdir.rmtree()

            if li: return True

            return False

        def hasPciUpdates(self):
            """ Check if the package has a pci.updates file or not.
            """

            tmpdir = path(tools.mkdtemp())
            self.unpack(tmpdir)

            li = [ f for f in tmpdir.walkfiles('pci.updates')]

            if tmpdir.exists(): tmpdir.rmtree()

            if li: return True

            return False
            
        def hasPcitable(self):
            """ Check if the package has a pcitable file or not.
            """

            tmpdir = path(tools.mkdtemp())
            self.unpack(tmpdir)

            li = [ f for f in tmpdir.walkfiles('pcitable')]

            if tmpdir.exists(): tmpdir.rmtree()

            if li: return True

            return False

        def unpack(self, destdir):
            """ Unpacks the package into destdir. 
            """
            self.rpmfile.extract(destdir)

            
        def getKernelModuleFiles(self):
            """ Returns a list of containing tuples of the kofile, kernel version and arch.
            """
            pass
            
        def extractPciUpdates(self, destdir):
            """ Extracts the pci.updates file from the package into the destdir.
            """
            destdir = path(destdir)
            if not destdir.exists(): raise DirDoesNotExistError, destdir

            tmpdir = path(tools.mkdtemp())

            self.unpack(tmpdir)

            li = [f for f in tmpdir.walkfiles('pci.updates')]
            
            pciupdates = ''
            if li: pciupdates = li[0] # hopefully only it contains only one instance of pci.updates
            
            pciupdates.copy(destdir)
                                
            if tmpdir.exists(): tmpdir.rmtree()            
            
        # syntantic sugar
        extractPCIUpdates = extractPciUpdates

        def extractPcitable(self, destdir):
            """ Extracts the pcitable file from the package into the destdir.
            """
            destdir = path(destdir)
            if not destdir.exist(): raise DirDoesNotExistError, destdir

            pass

            
        def extractKernelModulesDir(self, destdir, kofile=''):
            """ Extracts the kernel modules directory or just one kofile to destdir. 
            """

            tmpdir = path(tools.mkdtemp())
            kmoddestdir = path(destdir / 'lib/modules')
            
            if not kmoddestdir.exists():
                kmoddestdir.makedirs()
            
            self.unpack(tmpdir)
            kmoddir = tmpdir / 'lib/modules'

            if not kofile:
                tools.cpio_copytree(kmoddir,kmoddestdir)
            else:
                li = [ko for ko in kmoddir.walkfiles(kofile)]
                for l in li:
                    l.copy(kmoddestdir)
                    
            if tmpdir.exists(): tmpdir.rmtree()
            
            
        def extractKernel(self,destdir, kernelname=''):
            """ Extracts the kernel to destdir.
                Returns the name of the copied kernel image.
            """
            tmpdir = path(tools.mkdtemp())
            destdir = path(destdir).abspath()
            self.unpack(tmpdir)
            # get the kernel
            bootdir = tmpdir / 'boot'
            if not bootdir.exists(): 
                if tmpdir.exists(): tmpdir.rmtree()
                raise FileDoesNotExistError,'vmlinuz'

            li = [f for f in bootdir.walkfiles('vmlinuz*')]
            destdir = path(destdir)
            if not destdir.exists(): 
                if tmpdir.exists(): tmpdir.rmtree()
                raise DirDoesNotExistError
                
            if not li:
                if tmpdir.exists(): tmpdir.rmtree()
                raise FileDoesNotExistError,'vmlinuz'
                
            kernelimage = li[0]
            kname = kernelname or kernelimage.basename()
                
            dest = destdir / kname
            if dest.exists(): dest.remove()
            kernelimage.copy(dest)
                
            if tmpdir.exists(): tmpdir.rmtree()
            return kname

            
        


