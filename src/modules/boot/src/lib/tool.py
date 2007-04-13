#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.util.path import path
from kusu.boot.distro import GeneralInstallSrc
from kusu.boot.distro import CopyError
from kusu.boot.distro import FileAlreadyExists
from kusu.boot.image import *


class BootMediaTool:
    """ The management class for boot-media-tool operations. This convenience class combines 
        the functions and methods from the kusu.boot.image and kusu.boot.distro modules. 
    """
        
    def _initSrc(self,srcpath):
        """ Initializes the installsrc instance with GeneralInstallSrc. 
        """
        self.installsrc = GeneralInstallSrc(srcpath)
        
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
            
    def mkBootISO(self, isolinuxdir, isoname, volname="BootKit"):
        """ Creates ISO based on the isolinux directory. A FilePathError 
            exception will be raised if the paths are invalid or unaccesible.
        """
        try:
            makeBootISO(isolinuxdir, isoname, volname="BootKit")
            return True
        except FilePathError, e:
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
