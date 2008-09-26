#!/usr/bin/env python
# $Id: kernel.py 1605 2008-08-21 10:15:36Z nninaba $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module handles driverpatch operations dealing with kernel packages
"""


from path import path
from kusu.util.errors import FileDoesNotExistError, DirDoesNotExistError, ToolNotFound
from kusu.util import rpmtool, tools
import subprocess


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
            
        def getKernelVersion(self):
            """ Returns the kernel version string based on the rpm version + release.
            """
            version = self.rpmfile.version
            release = self.rpmfile.release
            return '-'.join([version,release])
            
        def isKernel(self):
            """ Check if the package is a kernel package or not. Basically the existence of the vmlinuz file determines this check.
            """
            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
            self.unpack(tmpdir)
            
            li = [ f for f in tmpdir.walkfiles('vmlinuz*')]
            
            if tmpdir.exists(): tmpdir.rmtree()
            
            if li: return True
            
            return False

        def isKernelModule(self):
            """ Check if the package is a kernel module package or not. Basically the existence of any ko files determines this check.
            """
            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
            self.unpack(tmpdir)

            li = [ f for f in tmpdir.walkfiles('*.ko*')]

            if tmpdir.exists(): tmpdir.rmtree()

            if li: return True

            return False

        def hasModulesRemove(self):
            """ Check if the package has a modules.remove file or not.
            """
            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
            self.unpack(tmpdir)

            li = [ f for f in tmpdir.walkfiles('modules.remove')]

            if tmpdir.exists(): tmpdir.rmtree()

            if li: return True

            return False

        def hasPciUpdates(self):
            """ Check if the package has a pci.updates file or not.
            """
            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
            self.unpack(tmpdir)

            li = [ f for f in tmpdir.walkfiles('pci.updates')]

            if tmpdir.exists(): tmpdir.rmtree()

            if li: return True

            return False
            
        def hasPcitable(self):
            """ Check if the package has a pcitable file or not.
            """
            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
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

            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))

            self.unpack(tmpdir)

            li = [f for f in tmpdir.walkfiles('pci.updates')]
            
            pciupdates = ''
            if li: pciupdates = li[0] # hopefully only it contains only one instance of pci.updates
            
            pciupdates.copy(destdir)
                                
            if tmpdir.exists(): tmpdir.rmtree()            
            
        # syntantic sugar
        extractPCIUpdates = extractPciUpdates
        
        def extractModulesRemoveFile(self, destdir):
            """ Extracts the modules.remove file from the package into the destdir.
            """
            destdir = path(destdir)
            if not destdir.exists(): raise DirDoesNotExistError, destdir

            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))

            self.unpack(tmpdir)

            li = [f for f in tmpdir.walkfiles('modules.remove')]
            
            modremove = ''
            if li: modremove = li[0] # hopefully only it contains only one instance of modules.remove
            
            modremove.copy(destdir)
                                
            if tmpdir.exists(): tmpdir.rmtree()

        def extractPcitable(self, destdir):
            """ Extracts the pcitable file from the package into the destdir.
            """
            destdir = path(destdir)
            if not destdir.exist(): raise DirDoesNotExistError, destdir

            pass

        
        def patchPciIds(self, original, pciupdates):
            """ Patches the original with new pci.updates.
            """
            # check if patchpcitable-script is available
            tool = 'patchpcitable-script'
            cmd = 'which %s > /dev/null 2>&1' % tool
            whichP = subprocess.Popen(cmd,shell=True)
            whichP.communicate()
            if whichP.returncode <> 0:
                raise ToolNotFound, tool
            
            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()

            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
            
            origfile = path(original)
            if not origfile.exists(): 
                if tmpdir.exists(): tmpdir.rmtree()
                raise FileDoesNotExistError, origfile

            origfile.copy(tmpdir)
            syspci = tmpdir / origfile.basename()
            origfile.remove()
            
            updatesfile = path(pciupdates)
            if not updatesfile.exists(): 
                if tmpdir.exists(): tmpdir.rmtree()
                raise FileDoesNotExistError, updatesfile
            
            cmd = '%s %s /dev/null %s %s /dev/null' % (tool, syspci, updatesfile, origfile)
            patchP = subprocess.Popen(cmd,shell=True)
            patchP.wait()
            
            if tmpdir.exists(): tmpdir.rmtree()
            
            
        def extractKernelModulesDir(self, destdir, kofile=''):
            """ Extracts the kernel modules directory or just one kofile to destdir. 
            """
            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
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
            # using a toplevel scratch directory
            # FIXME: Hardcoding for now
            if not path('/var/cache/kusu-driverpatch').exists(): path('/var/cache/kusu-driverpatch').mkdir()
            
            tmpdir = path(tools.mkdtemp(dir='/var/cache/kusu-driverpatch'))
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

            
        


