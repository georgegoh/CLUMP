#!/usr/bin/env python
# $Id: distro.py 194 2007-03-29 07:36:10Z najib $
# 
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

"""This module handles operations that work with the meta-information of the supported native distros."""

from path import path

SUPPORTED_DISTROS = { 'CentOS': '4.4', 'Fedora Core': '6', 'OpenSuSE': '10.2', 'Ubuntu': '6.10' }

# Taken from <unistd.h>, for file/dirs access modes
# These can be OR'd together
R_OK = 4   # Test for read permission.
W_OK = 2   # Test for write permission.
X_OK = 1   # Test for execute permission.


class CopyError(Exception): pass
class FileAlreadyExists(Exception): pass

class DistroInstallSrcBase(object):
    """Base class for a distro installation source and the operations that can work on it"""
    
    def __init__(self):
        """The following attributes should be defined by the subclasses.
        
        self.srcPath - refers to the path of the installation source. Note that it can be a remote or local path.
        self.isRemote - booleanType and should reflect that self.srcPath is a remote or not.
        self.ostype - Name of the OS/Distro. It should be in lowercase for consistency. May be used for comparison cases.
        self.version - Version of the OS/Distro.
        self.pathLayoutAttributes - a dict describing the layout of key directories/files for the installation source. 
        
        The keys should the logical names of each layout attribute and the value should be the relative paths of the 
        directories/files."""
        
        self.srcPath = None
        self.isRemote = False
        self.ostype = None
        self.version = None
        self.pathLayoutAttributes = {}
    
    def verifySrcPath(self):
        """Call the correct verify*SrcPath method."""
        
        if self.isRemote:
            return self.verifyRemoteSrcPath()
        else:
            return self.verifyLocalSrcPath()
    
    def verifyLocalSrcPath(self):
        """Verify the path for attributes that describes a valid local installation source"""
        
        try:
            if not self.srcPath.exists(): return False
        except AttributeError:
            # we could be testing on a NoneType object instead of a Path object
            return False
        
        # Check the path for each attribute listed, return if invalid path
        for k,v in self.pathLayoutAttributes.items():
            p = self.srcPath / v
            if not p.exists(): return False
            
        return True  

    def verifyRemoteSrcPath(self):
        """Verify the path for attributes that describes a valid remote installation source"""

        pass
        
    def getKernelPath(self):
        """Get the kernel path object"""
        
        if self.pathLayoutAttributes.has_key('kernel'):
            return path(self.srcPath / self.pathLayoutAttributes['kernel'])
        else:
            return None
            
    def getInitrdPath(self):
        """Get the initrd path object"""

        if self.pathLayoutAttributes.has_key('initrd'):
            return path(self.srcPath / self.pathLayoutAttributes['initrd'])
        else:
            return None
            
    def copyKernel(self, dest, overwrite=False):
        """Copy the kernel file to a destination"""

        global W_OK
        
        if path(dest).isdir():
            if path(dest).access(W_OK):
                filepath = path(dest) / self.getKernelPath().basename()
                # check if the destpath already contains the same name as the kernelPath
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getKernelPath().copy(filepath)
                elif not filepath.exists():
                    self.getKernelPath().copy(filepath)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError
        else:
            if path(dest).parent.access(W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite:
                    path(dest).chmod(0644)
                    self.getKernelPath().copy(dest)
                elif not path(dest).exists():
                    self.getKernelPath().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError
        
    def copyInitrd(self, dest, overwrite=False):
        """Copy the initrd file to a destination"""
        
        global W_OK

        if path(dest).isdir():
            if path(dest).access(W_OK):
                # check if the destpath already contains the same name as the initrdPath
                filepath = path(dest) / self.getInitrdPath().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getInitrdPath().copy(filepath)
                elif not filepath.exists():
                    self.getInitrdPath().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getInitrdPath().copy(dest)
                if not path(dest).exists():
                    self.getInitrdPath().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

class GeneralInstallSrc(DistroInstallSrcBase):
    """General wrapper class to deal with the different distro installation sources."""
    
    def __init__(self, srcPath):
        super(GeneralInstallSrc,self).__init__()
        # set the list of possible distros
        self.distros = [CentOSInstallSrc(srcPath), FedoraInstallSrc(srcPath)]
        
        for d in self.distros:
            if d.verifySrcPath():
                self.srcPath = d.srcPath
                self.isRemote = d.isRemote
                self.ostype = d.ostype
                self.version = d.version
                self.pathLayoutAttributes = d.pathLayoutAttributes
                break
            else:
                self.srcPath = None
                self.isRemote = False
                self.ostype = None
                self.version = None
                self.pathLayoutAttributes = {}
    
class CentOSInstallSrc(DistroInstallSrcBase):
    """This class describes how a CentOS installation source should be and the operations that can work on it."""
    
    def __init__(self, srcPath):
        super(CentOSInstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False
            
        self.ostype = 'centos'
        self.version = '4.4'

        # These should describe the key directories that identify a CentOS installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'imagesdir' : 'images',
            'baseosdir' : 'CentOS',
            'packagesdir' : 'CentOS/RPMS',
            'metainfodir' : 'CentOS/base'
        }
        

class FedoraInstallSrc(DistroInstallSrcBase):
    """This class describes how a Fedora installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(FedoraInstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'fedora'
        self.version = '6'

        # These should describe the key directories that identify a Fedora Core installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'imagesdir' : 'images',
            'baseosdir' : 'Fedora',
            'packagesdir' : 'Fedora/RPMS',
            'metainfodir' : 'Fedora/base'
        }
