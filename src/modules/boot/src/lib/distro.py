#!/usr/bin/env python
# $Id$
# 
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

"""This module handles operations that work with the meta-information of the supported native distros."""

from path import path
import os
import re
from kusu.util.errors import FileAlreadyExists, CopyError


SUPPORTED_DISTROS = ['centos', 'fedora', 'rhel']
USES_ANACONDA = ['centos', 'fedora', 'rhel']
SUPPORTED_ARCH = ['i386', 'x86_64']

class DistroInstallSrcBase(object):
    """Base class for a distro installation source and the operations that can work on it"""
    
    def __init__(self):
        """The following attributes should be defined by the subclasses.
        
        self.srcPath - refers to the path of the installation source. Note that it can be a remote or local path.
        self.isRemote - booleanType and should reflect that self.srcPath is a remote or not.
        self.isAdditionalType - booleanType and should reflect that this media is a additional installation media type.
        self.ostype - Name of the OS/Distro. It should be in lowercase for consistency. May be used for comparison cases.
        self.version - Major version number of the OS/Distro.
        self.pathLayoutAttributes - a dict describing the layout of key directories/files for the installation source. 
        self.patchLayoutAttributes - a dict describing the layout of key directories/files for installation patches.
        
        The keys should the logical names of each layout attribute and the value should be the relative paths of the 
        directories/files."""
        
        self.srcPath = None
        self.isRemote = False
        self.isAdditionalType = False
        self.ostype = None
        self.version = None
        self.arch = None
        self.pathLayoutAttributes = {}
        self.patchLayoutAttributes = {}
    
    def verifySrcPath(self):
        """Call the correct verify*SrcPath method."""
        
        if self.isRemote:
            return self.verifyRemoteSrcPath()
        else:
            return self.verifyLocalSrcPath()
    
    def verifyLocalSrcPath(self):
        """Verify the path for attributes that describes a valid local installation source"""
        
        try:
            if not self.srcPath.exists(): 
                return False
        except AttributeError:
            # we could be testing on a NoneType object instead of a Path object
            return False
        
        # Check the path for each attribute listed
        for k,v in self.pathLayoutAttributes.items():
            p = self.srcPath / v
            if not p.exists(): 
                return False
        
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
        
        if path(dest).isdir():
            if path(dest).access(os.W_OK):
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
            if path(dest).parent.access(os.W_OK):
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

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
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
            if path(dest).parent.access(os.W_OK):
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

    def getVersion(self):
        '''virtual function to be implemented by specific distro children'''
        return self.version

    def getArch(self):
        return self.arch
        
    def getKernelPackages(self):
        """ Returns any distribution-specific kernel packages. """
        raise NotImplemented


def DistroFactory(srcPath):
    """ Factory function that returns a DistroInstallSrcBase instance. """
    distros = [CentOS5InstallSrc(srcPath), 
               CentOS5AdditionalInstallSrc(srcPath),
               CentOS4InstallSrc(srcPath),
               CentOS4AdditionalInstallSrc(srcPath),
               FedoraInstallSrc(srcPath),
               FedoraAdditionalInstallSrc(srcPath),
               RHELInstallSrc(srcPath),
               RHEL5InstallSrc(srcPath),
               RHEL5AdditionalInstallSrc(srcPath)]
    for d in distros:
        if d.verifySrcPath():
            return d
    return DistroInstallSrcBase()


class CentOS4InstallSrc(DistroInstallSrcBase):
    """This class describes how a CentOS installation source should be and the operations that can work on it."""
    
    def __init__(self, srcPath):
        super(CentOS4InstallSrc,self).__init__()
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
        self.version = '4'

        # These should describe the key directories that identify a CentOS installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'isolinuxbin' : 'isolinux/isolinux.bin',
            'imagesdir' : 'images',
            'stage2' : 'images/stage2.img',
            'baseosdir' : 'CentOS',
            'packagesdir' : 'CentOS/RPMS',
            'metainfodir' : 'CentOS/base'
        }

        # The following determines the patchfile layout for CentOS
        self.patchLayoutAttributes = {
            'patchdir' : 'images',
            'patchimage' : 'images/updates.img'
        }


    def getVersion(self):
        '''CentOS specific way of getting the distro version'''
        return self.version
        
    def getIsolinuxbinPath(self):
        """Get the isolinux.bin path object"""

        if self.pathLayoutAttributes.has_key('isolinuxbin'):
            return path(self.srcPath / self.pathLayoutAttributes['isolinuxbin'])
        else:
            return None 

    def copyIsolinuxbin(self, dest, overwrite=False):
        """Copy the isolinuxbin file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the isolinuxbinPath
                filepath = path(dest) / self.getIsolinuxbinPath().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getIsolinuxbinPath().copy(filepath)
                elif not filepath.exists():
                    self.getIsolinuxbinPath().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getIsolinuxbinPath().copy(dest)
                if not path(dest).exists():
                    self.getIsolinuxbinPath().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

    def getStage2Path(self):
        """Get the stage2 path object"""

        if self.pathLayoutAttributes.has_key('stage2'):
            return path(self.srcPath / self.pathLayoutAttributes['stage2'])
        else:
            return None
            
    def copyStage2(self, dest, overwrite=False):
        """Copy the stage2 file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the stage2Path
                filepath = path(dest) / self.getStage2Path().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getStage2Path().copy(filepath)
                elif not filepath.exists():
                    self.getStage2Path().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getStage2Path().copy(dest)
                if not path(dest).exists():
                    self.getStage2Path().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError
                
    def getKernelPackages(self):
        # set up pattern to match centos kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        keys = [k for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        kpkgs = []

        try:
            for k in keys:
                root = path(self.srcPath) / self.pathLayoutAttributes[k]
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages

class CentOS4AdditionalInstallSrc(DistroInstallSrcBase):
    """This class describes how a CentOS installation source should be and the operations that can work on it."""
    
    def __init__(self, srcPath):
        super(CentOS4AdditionalInstallSrc,self).__init__()
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
        self.version = '4'
        self.isAdditionalType = True

        # These should describe the key directories that identify a CentOS installation source layout.
        self.pathLayoutAttributes = {
            'baseosdir' : 'CentOS',
            'packagesdir' : 'CentOS/RPMS'
        }

    def getKernelPath(self):
        return None
            
    def getInitrdPath(self):
        return None
            
    def copyKernel(self, dest, overwrite=False):
        raise CopyError
        
    def copyInitrd(self, dest, overwrite=False):
        raise CopyError
        
    def getKernelPackages(self):
        # set up pattern to match centos kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        keys = [k for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        kpkgs = []

        try:
            for k in keys:
                root = path(self.srcPath) / self.pathLayoutAttributes[k]
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages

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
        self.version = '0'
        self.arch = 'noarch'

        # These should describe the key directories that identify a Fedora Core installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'isolinuxbin' : 'isolinux/isolinux.bin',
            'imagesdir' : 'images',
            'stage2' : 'images/stage2.img',
            'baseosdir' : 'Fedora',
            'packagesdir' : 'Fedora/RPMS',
            'metainfodir' : 'Fedora/base'
        }

        # The following determines the patchfile layout for Fedora
        self.patchLayoutAttributes = {
            'patchdir' : 'images',
            'patchimage' : 'images/updates.img'
        }


    def getIsolinuxbinPath(self):
        """Get the isolinux.bin path object"""

        if self.pathLayoutAttributes.has_key('isolinuxbin'):
            return path(self.srcPath / self.pathLayoutAttributes['isolinuxbin'])
        else:
            return None 

    def copyIsolinuxbin(self, dest, overwrite=False):
        """Copy the isolinuxbin file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the isolinuxbinPath
                filepath = path(dest) / self.getIsolinuxbinPath().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getIsolinuxbinPath().copy(filepath)
                elif not filepath.exists():
                    self.getIsolinuxbinPath().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getIsolinuxbinPath().copy(dest)
                if not path(dest).exists():
                    self.getIsolinuxbinPath().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

    def getStage2Path(self):
        """Get the stage2 path object"""

        if self.pathLayoutAttributes.has_key('stage2'):
            return path(self.srcPath / self.pathLayoutAttributes['stage2'])
        else:
            return None


    def copyStage2(self, dest, overwrite=False):
        """Copy the stage2 file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the stage2Path
                filepath = path(dest) / self.getStage2Path().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)
                    self.getStage2Path().copy(filepath)
                elif not filepath.exists():
                    self.getStage2Path().copy(filepath)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite:
                    path(dest).chmod(0644)
                    self.getStage2Path().copy(dest)
                if not path(dest).exists():
                    self.getStage2Path().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

    def getVersion(self):
        '''Fedora specific way of getting the distro version'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[1] #second line is usually the name/version
            words = line.split()
            for i in range(0,len(words)):
                if words[i].isdigit():
                    break
            self.version = words[i]
        else:
            #try the fedora-release RPM under self.pathLayoutAttributes[packagesdir]
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{version}' 2> /dev/null
            pass
        return self.version

    def getArch(self):
        '''Fedora specific way of getting the distro architecture'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[2] #third line is usually the arch
            self.arch = line.strip().split()[0].lower()
        else:
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{arch}' 2> /dev/null
            pass
        return self.arch
        
    def getKernelPackages(self):
        # set up pattern to match fedora kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        keys = [k for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        kpkgs = []

        try:
            for k in keys:
                root = path(self.srcPath) / self.pathLayoutAttributes[k]
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages

class FedoraAdditionalInstallSrc(DistroInstallSrcBase):
    """This class describes how a Fedora installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(FedoraAdditionalInstallSrc,self).__init__()
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
        self.version = '0'
        self.arch = 'noarch'
        self.isAdditionalType = True

        # These should describe the key directories that identify a Fedora Core installation source layout.
        self.pathLayoutAttributes = {
            'baseosdir' : 'Fedora',
            'packagesdir' : 'Fedora/RPMS'
        }

    def getKernelPath(self):
        return None
            
    def getInitrdPath(self):
        return None
            
    def copyKernel(self, dest, overwrite=False):
        raise CopyError
        
    def copyInitrd(self, dest, overwrite=False):
        raise CopyError

    def getVersion(self):
        '''Fedora specific way of getting the distro version'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[1] #second line is usually the name/version
            words = line.split()
            for i in range(0,len(words)):
                if words[i].isdigit():
                    break
            self.version = words[i]
        else:
            #try the fedora-release RPM under self.pathLayoutAttributes[packagesdir]
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{version}' 2> /dev/null
            pass
        return self.version

    def getArch(self):
        '''Fedora specific way of getting the distro architecture'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[2] #third line is usually the arch
            self.arch = line.strip().split()[0].lower()
        else:
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{arch}' 2> /dev/null
            pass
        return self.arch
        

    def getKernelPackages(self):
        # set up pattern to match fedora kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        keys = [k for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        kpkgs = []

        try:
            for k in keys:
                root = path(self.srcPath) / self.pathLayoutAttributes[k]
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages


class RHELInstallSrc(DistroInstallSrcBase):
    """This class describes how a RHEL installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(RHELInstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'rhel'
        self.version = '4'

        # These should describe the key directories that identify a CentOS installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'isolinuxbin' : 'isolinux/isolinux.bin',
            'imagesdir' : 'images',
            'baseosdir' : 'RedHat',
            'packagesdir' : 'RedHat/RPMS',
            'metainfodir' : 'RedHat/base'
        }

    def getIsolinuxbinPath(self):
        """Get the isolinux.bin path object"""

        if self.pathLayoutAttributes.has_key('isolinuxbin'):
            return path(self.srcPath / self.pathLayoutAttributes['isolinuxbin'])
        else:
            return None 

    def copyIsolinuxbin(self, dest, overwrite=False):
        """Copy the isolinuxbin file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the isolinuxbinPath
                filepath = path(dest) / self.getIsolinuxbinPath().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getIsolinuxbinPath().copy(filepath)
                elif not filepath.exists():
                    self.getIsolinuxbinPath().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getIsolinuxbinPath().copy(dest)
                if not path(dest).exists():
                    self.getIsolinuxbinPath().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

    def getVersion(self):
        '''RHEL specific way of getting the distro version'''
        return self.version     #for now
        
    def getKernelPackages(self):
        # set up pattern to match rhel kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        keys = [k for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        kpkgs = []

        try:
            for k in keys:
                root = path(self.srcPath) / self.pathLayoutAttributes[k]
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages

class CentOS5InstallSrc(DistroInstallSrcBase):
    """This class describes how a CentOS installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(CentOS5InstallSrc,self).__init__()
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
        self.version = '5'

        # These should describe the key directories that identify a CentOS installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'isolinuxbin' : 'isolinux/isolinux.bin',
            'imagesdir' : 'images',
            'stage2' : 'images/stage2.img',
            'baseosdir' : 'CentOS',
            'packagesdir' : 'CentOS',
            'repodatadir' : 'repodata'
        }

        # The following determines the patchfile layout for CentOS
        self.patchLayoutAttributes = {
            'patchdir' : 'images',
            'patchimage' : 'images/updates.img'
        }


    def getVersion(self):
        '''CentOS specific way of getting the distro version'''
        return self.version

    def getIsolinuxbinPath(self):
        """Get the isolinux.bin path object"""

        if self.pathLayoutAttributes.has_key('isolinuxbin'):
            return path(self.srcPath / self.pathLayoutAttributes['isolinuxbin'])
        else:
            return None 

    def copyIsolinuxbin(self, dest, overwrite=False):
        """Copy the isolinuxbin file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the isolinuxbinPath
                filepath = path(dest) / self.getIsolinuxbinPath().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getIsolinuxbinPath().copy(filepath)
                elif not filepath.exists():
                    self.getIsolinuxbinPath().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getIsolinuxbinPath().copy(dest)
                if not path(dest).exists():
                    self.getIsolinuxbinPath().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

    def getStage2Path(self):
        """Get the stage2 path object"""

        if self.pathLayoutAttributes.has_key('stage2'):
            return path(self.srcPath / self.pathLayoutAttributes['stage2'])
        else:
            return None

    def copyStage2(self, dest, overwrite=False):
        """Copy the stage2 file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the stage2Path
                filepath = path(dest) / self.getStage2Path().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getStage2Path().copy(filepath)
                elif not filepath.exists():
                    self.getStage2Path().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getStage2Path().copy(dest)
                if not path(dest).exists():
                    self.getStage2Path().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

    def getArch(self):
        '''Centos specific way of getting the distro architecture'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[2] #third line is usually the arch
            self.arch = line.strip().split()[0].lower()
        else:
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{arch}' 2> /dev/null
            pass
        return self.arch
        
    def getKernelPackages(self):
        # set up pattern to match rhel kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        _pkgsdir = [self.pathLayoutAttributes[k] for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        # remove duplicates
        _d = {}
        try:
            for k in _pkgsdir:
                _d[k] = 1
        except TypeError:
                del _d
        pkgsdir = _d.keys()
        kpkgs = []

        try:
            for pkgdir in pkgsdir:
                root = path(self.srcPath) / pkgdir
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages

class CentOS5AdditionalInstallSrc(DistroInstallSrcBase):
    """This class describes how a centos 5 installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(CentOS5AdditionalInstallSrc,self).__init__()
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
        self.version = '5'
        self.arch = 'noarch'
        self.isAdditionalType = True

        # These should describe the key directories that identify a CentOS 5 installation source layout.
        self.pathLayoutAttributes = {
            'baseosdir' : 'CentOS',
            'packagesdir' : 'CentOS'
        }


    def getKernelPath(self):
        return None
            
    def getInitrdPath(self):
        return None
            
    def copyKernel(self, dest, overwrite=False):
        raise CopyError
        
    def copyInitrd(self, dest, overwrite=False):
        raise CopyError

    def getArch(self):
        '''Redhat specific way of getting the distro architecture'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[2] #third line is usually the arch
            self.arch = line.strip().split()[0].lower()
        else:
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{arch}' 2> /dev/null
            pass
        return self.arch

    def getKernelPackages(self):
        # set up pattern to match rhel kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        _pkgsdir = [self.pathLayoutAttributes[k] for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        # remove duplicates
        _d = {}
        try:
            for k in _pkgsdir:
                _d[k] = 1
        except TypeError:
                del _d
        pkgsdir = _d.keys()
        kpkgs = []

        try:
            for pkgdir in pkgsdir:
                root = path(self.srcPath) / pkgdir
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages


class RHEL5InstallSrc(DistroInstallSrcBase):
    """This class describes how a RHEL 5 installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(RHEL5InstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'rhel'
        self.version = '5'

        # These should describe the key directories that identify a CentOS installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'isolinuxbin' : 'isolinux/isolinux.bin',
            'imagesdir' : 'images',
            'stage2' : 'images/stage2.img',
            'server.packagesdir' : 'Server',
            'server.repodatadir' : 'Server/repodata',
            'cluster.packagesdir' : 'Cluster',
            'cluster.repodatadir' : 'Cluster/repodata',
            'clusterstorage.packagesdir' : 'ClusterStorage',
            'clusterstorage.repodatadir' : 'ClusterStorage/repodata',
            'vt.packagesdir' : 'Server',
            'vt.repodatadir' : 'Server/repodata',
        }

        # The following determines the patchfile layout for RHEL5
        self.patchLayoutAttributes = {
            'patchdir' : 'images',
            'patchimage' : 'images/updates.img'
        }

    def getIsolinuxbinPath(self):
        """Get the isolinux.bin path object"""

        if self.pathLayoutAttributes.has_key('isolinuxbin'):
            return path(self.srcPath / self.pathLayoutAttributes['isolinuxbin'])
        else:
            return None 

    def copyIsolinuxbin(self, dest, overwrite=False):
        """Copy the isolinuxbin file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the isolinuxbinPath
                filepath = path(dest) / self.getIsolinuxbinPath().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getIsolinuxbinPath().copy(filepath)
                elif not filepath.exists():
                    self.getIsolinuxbinPath().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getIsolinuxbinPath().copy(dest)
                if not path(dest).exists():
                    self.getIsolinuxbinPath().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

    def getStage2Path(self):
        """Get the stage2 path object"""

        if self.pathLayoutAttributes.has_key('stage2'):
            return path(self.srcPath / self.pathLayoutAttributes['stage2'])
        else:
            return None

    def copyStage2(self, dest, overwrite=False):
        """Copy the stage2 file to a destination"""

        if path(dest).isdir():
            if path(dest).access(os.W_OK):
                # check if the destpath already contains the same name as the stage2Path
                filepath = path(dest) / self.getStage2Path().basename()
                if filepath.exists() and overwrite:
                    filepath.chmod(0644)            
                    self.getStage2Path().copy(filepath)
                elif not filepath.exists():
                    self.getStage2Path().copy(filepath)
                else:
                    raise FileAlreadyExists                
            else:
                raise CopyError
        else:
            if path(dest).parent.access(os.W_OK):
                # make sure that the existing destpath is accessible and writable
                if path(dest).exists() and overwrite: 
                    path(dest).chmod(0644)
                    self.getStage2Path().copy(dest)
                if not path(dest).exists():
                    self.getStage2Path().copy(dest)
                else:
                    raise FileAlreadyExists
            else:
                raise CopyError

    def getVersion(self):
        '''Redhat specific way of getting the distro version'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[1] #second line is usually the name/version
            words = line.split()
            for i in range(0,len(words)):
                if words[i].isdigit():
                    break
            self.version = words[i]
        else:
            #try the fedora-release RPM under self.pathLayoutAttributes[packagesdir]
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{version}' 2> /dev/null
            pass
        return self.version

    def getArch(self):
        '''Redhat specific way of getting the distro architecture'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[2] #third line is usually the arch
            self.arch = line.strip().split()[0].lower()
        else:
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{arch}' 2> /dev/null
            pass
        return self.arch
        
    def getKernelPackages(self):
        # set up pattern to match rhel kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        _pkgsdir = [self.pathLayoutAttributes[k] for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        # remove duplicates
        _d = {}
        try:
            for k in _pkgsdir:
                _d[k] = 1
        except TypeError:
                del _d
        pkgsdir = _d.keys()
        kpkgs = []

        try:
            for pkgdir in pkgsdir:
                root = path(self.srcPath) / pkgdir
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages

class RHEL5AdditionalInstallSrc(DistroInstallSrcBase):
    """This class describes how a RHEL 5 installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(RHEL5AdditionalInstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'rhel'
        self.version = '0'
        self.arch = 'noarch'
        self.isAdditionalType = True

        # These should describe the key directories that identify a RHEL 5 installation source layout.
        self.pathLayoutAttributes = {
            'server.packagesdir' : 'Server',
            'cluster.packagesdir' : 'Cluster',
            'clusterstorage.packagesdir' : 'ClusterStorage',
            'vt.packagesdir' : 'Server',
        }

    def getKernelPath(self):
        return None
            
    def getInitrdPath(self):
        return None
            
    def copyKernel(self, dest, overwrite=False):
        raise CopyError
        
    def copyInitrd(self, dest, overwrite=False):
        raise CopyError

    def getVersion(self):
        '''Redhat specific way of getting the distro version'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[1] #second line is usually the name/version
            words = line.split()
            for i in range(0,len(words)):
                if words[i].isdigit():
                    break
            self.version = words[i]
        else:
            #try the fedora-release RPM under self.pathLayoutAttributes[packagesdir]
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{version}' 2> /dev/null
            pass
        return self.version

    def getArch(self):
        '''Redhat specific way of getting the distro architecture'''
        discinfo = self.srcPath + '/.discinfo'
        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[2] #third line is usually the arch
            self.arch = line.strip().split()[0].lower()
        else:
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{arch}' 2> /dev/null
            pass
        return self.arch

    def getKernelPackages(self):
        # set up pattern to match rhel kernel packages
        pat = re.compile(r'kernel-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        _pkgsdir = [self.pathLayoutAttributes[k] for k in self.pathLayoutAttributes.keys() if k.endswith('packagesdir')]
        # remove duplicates
        _d = {}
        try:
            for k in _pkgsdir:
                _d[k] = 1
        except TypeError:
                del _d
        pkgsdir = _d.keys()
        kpkgs = []

        try:
            for pkgdir in pkgsdir:
                root = path(self.srcPath) / pkgdir
                li = [f for f in root.walkfiles('kernel*rpm')]
                kpkgs.extend([l for l in li if re.findall(pat,l)])
        except OSError:
            pass

        return kpkgs

    # syntatic sugar
    getKernelRpms = getKernelPackages

