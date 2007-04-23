#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module contains several classes and functions for dealing with boot media and boot environments. """

from path import path
import subprocess
import os
from kusu.boot.distro import DistroFactory, InvalidInstallSource
from kusu.boot.distro import CopyError
from kusu.boot.distro import FileAlreadyExists
from kusu.boot.image import *
import tempfile

def getPartitionMap(src='/proc/partitions'):
    """ This function returns a list of dicts containing the entries of /proc/partitions. """
    partition_map = {}
    lines = open(src).readlines()
    for line in lines[2:]:
        tokens = line.split()
        details = {}
        details['major'] = tokens[0]
        details['minor'] = tokens[1]
        details['blocks'] = tokens[2]
        partition_map[tokens[3]] = details
    return partition_map
    
def makeDev(devtype,major,minor,devpath):
    """ This function creates /dev/* entries. Mainly used for creating block devices. """
    
    # do not create if devpath already exists
    if path(devpath).exists(): return
    
    os.system('mknod /dev/%s %s %s %s' % (devpath,devtype,major,minor))

class KusuSVNSource:
    """ This class contains data and operations that work with the Kusu SVN source. """
    
    def __init__(self, source):
        self.srcpath = path(source)
        self.isRemote = False
        self.develroot = None
        self.kusuroot = None
        self.scratchdir = None

        # These should describe the key directories/files that identify a Kusu SVN source layout.
        self.srcpathLayoutAttributes = {
            'bin' : 'bin',
            'build' : 'build',
            'CMakeLists' : 'CMakeLists.txt',
            'docs' : 'docs',
            'etc' : 'etc',
            'src' : 'src',
            'dists' : 'src/dists'
        }

    def verifySrcPath(self):
        """Call the correct verify*SrcPath method."""

        if self.isRemote:
            return self.verifyRemoteSrcPath()
        else:
            return self.verifyLocalSrcPath()

    def verifyLocalSrcPath(self):
        """Verify the path for attributes that describes a valid Kusu SVN source"""

        try:
            if not self.srcpath.exists(): return False
        except AttributeError:
            # we could be testing on a NoneType object instead of a Path object
            return False

        # Check the path for each attribute listed, return if invalid path
        for k,v in self.srcpathLayoutAttributes.items():
            p = self.srcpath / v
            if not p.exists(): return False

        return True
        
    def setup(self,develroot=None,kusuroot=None):
        """ General setup for Kusu develroot"""
        
        if not develroot:
            self.scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
            self.develroot = path(tempfile.mkdtemp(dir=self.scratchdir))
        else:
            if path(develroot).exists():
                self.develroot = path(develroot)
            else:
                raise FilePathError, "Please ensure that the develroot %s exists!" \
                    % develroot
            
        if not kusuroot:
            self.kusuroot = self.develroot / 'kusuroot'
        else:
            if path(kusuroot).exists():
                self.kusuroot = path(kusuroot)
            else:
                raise FilePathError, "Please ensure that the kusuroot %s exists!" \
                    % kusuroot
            
                
    def runCMake(self):
        """ Run CMake within the Kusu develroot. This is a blocking call. """
        env = os.environ
        env['KUSU_ROOT'] = self.kusuroot
        cmakeP = subprocess.Popen('cmake %s > /dev/null 2>&1' % self.srcpath.abspath(),shell=True,
                    cwd=self.develroot,env=env)
        result = cmakeP.communicate()
        
        return cmakeP.returncode

        
    def runMake(self):
        """ Run make within the Kusu develroot. This is a blocking call. """

        makeP = subprocess.Popen('make > /dev/null 2>&1',shell=True,
                    cwd=self.develroot)
        result = makeP.communicate()

        return makeP.returncode
        
    def cleanup(self):
        """ Housecleaning for Kusu develroot. """
        
        # remove the scratchtree when done
        if self.kusuroot.exists(): self.kusuroot.rmtree()
        if self.develroot.exists(): self.develroot.rmtree()
        if self.scratchdir.exists(): self.scratchdir.rmtree()
        
    def run(self):
        """ Main launcher. """
        
        self.runCMake()
        self.runMake()
        
    def copyKusuroot(self, dest, overwrite=False):
        """Copy the kusuroot file to a destination"""

        if path(dest).parent.access(os.W_OK):
            # make sure that the existing destpath is accessible and writable
            if path(dest).exists() and overwrite:
                path(dest).rmtree()
                cpio_copytree(self.kusuroot,dest)
            elif not path(dest).exists():
                cpio_copytree(self.kusuroot,dest)
            else:
                raise FileAlreadyExists
        else:
            raise CopyError        

class BootMediaTool:
    """ The management class for boot-media-tool operations. This convenience class combines 
        the functions and methods from the kusu.boot.image and kusu.boot.distro modules. 
    """
        
    def _initSrc(self,srcpath):
        """ Initializes the installsrc instance with DistroFactory. 
        """
        self.installsrc = DistroFactory(srcpath)
        
    def validSrcPath(self, srcpath):
        """ Verify if the srcpath is valid. """
        self._initSrc(srcpath)
        return self.installsrc.verifySrcPath()
        
    def getDistro(self, srcpath):
        """ Returns the OS type. """
        self._initSrc(srcpath)
        return self.installsrc.ostype
        
    def getKernelPath(self, srcpath):
        """ Query the srcpath and returns the path of the kernel. """
        self._initSrc(srcpath)
        return self.installsrc.getKernelPath()
        
    def getInitrdPath(self, srcpath):
        """ Query the srcpath and returns the path of the initrd. """
        self._initSrc(srcpath)
        return self.installsrc.getInitrdPath()
        
    def copyKernel(self, srcpath, dest, overwrite=False):
        """ Extract the kernel from the srcpath to the dest. A CopyError
            exception will be raised if there are errors when extraction.
        """
        try:
            self._initSrc(srcpath)
            self.installsrc.copyKernel(dest,overwrite)
            return True
        except (CopyError,FileAlreadyExists), e:
            raise e
            
    def copyInitrd(self, srcpath, dest, overwrite=False):
        """ Extract the initrd from the srcpath to the dest. A CopyError
            exception will be raised if there are errors when extraction. 
        """
        try:
            self._initSrc(srcpath)
            self.installsrc.copyInitrd(dest,overwrite)
            return True
        except (CopyError,FileAlreadyExists), e:
            raise e
            
    def packRootImg(self, dirname, rootimgpath, initscript=None):
        """ Converts the rootfs directory into a initramfs image. A
            FilePathError exception will be raised if the paths are
            invalid or unaccesible. This is also a root only operation.
        """
        try:
            packInitramFS(dirname, rootimgpath, initscript)
            return True
        except FilePathError, e:
            raise e
            
    def unpackRootImg(self, rootimgpath, dirname):
        """ Unpack a root image into a rootfs directory. A
            FilePathError exception will be raised if the paths are
            invalid or unaccesible. This is also a root only operation
            and a NotPriviledgedUser exception will be raised if non-root
            process or user is calling this method.
        """
        try:
            unpack(rootimgpath, dirname)
            return True
        except (FilePathError,NotPriviledgedUser), e:
            raise e
            
    def mkISOLinuxDir(self, isolinuxdir, kernelpath, initrdpath, ostype, isolinuxbin):
        """ Creates isolinux directory. A FilePathError exception will be 
            raised if the paths are invalid or unaccesible.
        """
        try:
            obj = OperatingEnvironment(kernelpath,initrdpath,ostype)
            makeISOLinuxDir(isolinuxdir, obj, isolinuxbin)
            return True
        except FilePathError, e:
            raise e
            
    def mkImagesDir(self, srcpath, destdir, patchfile=None,overwrite=False):
        """ Creates images directory based on installsrc. A FilePathError
            exception will be raised if the paths are invalid or unaccesible.
        """
        try:
            makeImagesDir(srcpath,destdir,patchfile,overwrite)
        except (FilePathError,InvalidInstallSource), e:
            raise e
            
    def mkBootISO(self, isolinuxdir, isoname, volname="BootKit"):
        """ Creates ISO based on the isolinux directory. A FilePathError 
            exception will be raised if the paths are invalid or unaccesible.
        """
        try:
            makeBootISO(isolinuxdir, isoname, volname="BootKit")
            return True
        except FilePathError, e:
            raise e
            
    def mkPatch(self,kususrc,osname,osver,osarch,patchfile):
        """ Creates a distro-specific Kusu Installer patchfile. """
        try:
            svnsrc = KusuSVNSource(kususrc)
            
            # create a scratchdir to hold the patchfile contents
            parentdir = path(patchfile).parent
            tmpdir = path(tempfile.mkdtemp(dir=parentdir))
            kusuroot = tmpdir / 'opt/kusu'
            kusuroot.makedirs()
            
            if not svnsrc.verifySrcPath(): raise FilePathError, "Invalid Kusu SVN Source!"
            
            if svnsrc.verifySrcPath():
                svnsrc.setup()
                svnsrc.run()
                svnsrc.copyKusuroot(kusuroot,overwrite=True)
                svnsrc.cleanup()
                # get the correct kusuenv.sh
                if osname == 'fedora':
                    # put in the kusuenv.sh
                    p = svnsrc.srcpath / 'src/dists/fedora/%s/%s/kusuenv.sh' % (osver,osarch)
                    kusuenv = path(p)
                        
                    if kusuenv.exists(): kusuenv.copy(kusuroot / 'bin')
                    
                    # remove the kusudevenv.sh
                    if path(kusuroot / 'bin' / 'kusudevenv.sh').exists():
                        path(kusuroot / 'bin' / 'kusudevenv.sh').remove()
                        
                    # put in the the faux anaconda launcher
                    p = svnsrc.srcpath / 'src/dists/fedora/%s/%s/updates.img/anaconda' % (osver,osarch)
                    fakeanaconda = path(p)
                    if fakeanaconda.exists(): fakeanaconda.copy(tmpdir)
                        
                
                packExt2FS(tmpdir,patchfile)
                
            path(tmpdir).rmtree()
        except (FilePathError,NotPriviledgedUser), e:
            # do some housecleaning if possible
            if svnsrc.verifySrcPath(): svnsrc.cleanup()
            if path(tmpdir).exists(): path(tmpdir).rmtree()
            raise e
        
    def mkBootArchive(self, isolinuxdir, archive):
        """ Creates a BootArchive based on the isolinux directory. A 
            FilePathError exception will be raised if the paths are 
            invalid or unaccesible.
        """
        try:
            makeBootArchive(isolinuxdir, archive)
            return True
        except FilePathError, e:
            raise e
