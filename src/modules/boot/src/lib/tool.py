#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module contains several convenience classes and functions for dealing with boot media and boot environments. """

from path import path
import subprocess
from kusu.boot.distro import GeneralInstallSrc, InvalidInstallSource
from kusu.boot.distro import CopyError
from kusu.boot.distro import FileAlreadyExists
from kusu.boot.image import *

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
    
    if devtype != 'b' or devtype != 'c': raise Exception, "devtype must be 'b' or 'c'!"
    
    args = ' '.join([devpath,devtype,major,minor])
    mknodP = subprocess.Popen("mknod %s" % args,cwd=cwd,shell=True)
    mknodP.communicate()
    
    return mknodP.retcode

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
