#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#

"""This module handles operations that work with the meta-information of the supported native distros."""

from path import path
import os
import re
from kusu.util.errors import FileAlreadyExists, CopyError
from primitive.support.rpmtool import RPM
from ConfigParser import ConfigParser
from primitive.support import osfamily

SUPPORTED_DISTROS = osfamily.getOSNames('rhelfamily') + ['fedora', 'sles', 'opensuse']
USES_ANACONDA = osfamily.getOSNames('rhelfamily') + ['fedora']
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
        self.versionString = None
        self.majorVersion = None
        self.minorVersion = None
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

        try:
            if path(dest).isdir():
                if path(dest).access(os.W_OK):
                    filepath = path(dest) / self.getKernelPath().basename()
                    # check if the destpath already contains the same name as the kernelPath
                    if filepath.exists() and overwrite:
                        filepath.chmod(0644)
                        self.getKernelPath().copy(filepath)
                        return
                    elif not filepath.exists():
                        self.getKernelPath().copy(filepath)
                        return
                    else:
                        raise FileAlreadyExists
                else:
                    errmsg = 'Write permission denied: %s' % path(dest)
                    raise CopyError, errmsg
            else:
                if path(dest).parent.access(os.W_OK):
                    # make sure that the existing destpath is accessible and writable
                    if path(dest).exists() and overwrite:
                        # remove the existing file if overwrite is true
                        path(dest).remove()
                        self.getKernelPath().copy(dest)
                        return
                    elif not path(dest).exists():
                        self.getKernelPath().copy(dest)
                        return
                    else:
                        raise FileAlreadyExists
                else:
                    errmsg = 'Write permission denied: %s' % path(dest).parent
                    raise CopyError, errmsg
        except IOError, e:
            raise e

    def copyInitrd(self, dest, overwrite=False):
        """Copy the initrd file to a destination"""

        try:
            if path(dest).isdir():
                if path(dest).access(os.W_OK):
                    # check if the destpath already contains the same name as the initrdPath
                    filepath = path(dest) / self.getInitrdPath().basename()
                    if filepath.exists() and overwrite:
                        filepath.chmod(0644)
                        self.getInitrdPath().copy(filepath)
                        return
                    elif not filepath.exists():
                        self.getInitrdPath().copy(filepath)
                        return
                    else:
                        raise FileAlreadyExists
                else:
                    errmsg = "Write permission denied: %s" % path(dest)
                    raise CopyError, errmsg
            else:
                if path(dest).parent.access(os.W_OK):
                    # make sure that the existing destpath is accessible and writable
                    if path(dest).exists() and overwrite:
                        # remove the existing file if overwrite is true
                        path(dest).remove()
                        self.getInitrdPath().copy(dest)
                        return
                    if not path(dest).exists():
                        self.getInitrdPath().copy(dest)
                        return
                    else:
                        raise FileAlreadyExists
                else:
                    errmsg = "Write permission denied: %s" % path(dest).parent
                    raise CopyError, errmsg
        except IOError, e:
            raise e

    def getVersion(self):
        '''virtual function to be implemented by specific distro children'''
        return self.version

    def getMajorVersion(self):
        '''virtual function to be implemented by specific distro children'''
        return self.majorVersion

    def getMinorVersion(self):
        '''virtual function to be implemented by specific distro children'''
        return self.minorVersion

    def getVersionString(self):
        '''virtual function to be implemented by specific distro children'''
        return self.versionString

    def getArch(self):
        return self.arch

    def getKernelPackages(self):
        """ Returns any distribution-specific kernel packages. """
        raise NotImplementedError


def DistroFactory(srcPath):
    """ Factory function that returns a DistroInstallSrcBase instance. """
    distros = [CentOS5InstallSrc(srcPath),
               CentOS5AdditionalInstallSrc(srcPath),
               CentOS4InstallSrc(srcPath),
               CentOS4AdditionalInstallSrc(srcPath),
               #FedoraInstallSrc(srcPath),
               #FedoraAdditionalInstallSrc(srcPath),
               #Fedora7InstallSrc(srcPath),
               RHELInstallSrc(srcPath),
               RHEL5InstallSrc(srcPath),
               RHEL5AdditionalInstallSrc(srcPath),
               #Fedora8InstallSrc(srcPath),
               OPENSUSE103InstallSrc(srcPath),
               SLES10InstallSrc(srcPath),
               ScientificLinux5InstallSrc(srcPath),
               ScientificLinux5AdditionalInstallSrc(srcPath),
               ScientificLinuxCern5InstallSrc(srcPath)]

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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

    # syntactic sugar
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
        raise CopyError, dest

    def copyInitrd(self, dest, overwrite=False):
        raise CopyError, dest

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

    # syntactic sugar
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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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

    # syntactic sugar
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
        raise CopyError, dest

    def copyInitrd(self, dest, overwrite=False):
        raise CopyError, dest

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

    # syntactic sugar
    getKernelRpms = getKernelPackages

class Fedora7InstallSrc(DistroInstallSrcBase):
    """This class describes how a Fedora 7 installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(Fedora7InstallSrc,self).__init__()
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
            'packagesdir' : 'Fedora',
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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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
            self.version = words[i].strip('"')
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

    # syntactic sugar
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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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

    # syntactic sugar
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


    def getMajorVersion(self):
        '''CentOS specific way of getting the distro version'''

        self.majorVersion = self.getVersion()
        return self.majorVersion

    def getMinorVersion(self):
        '''CentOS specific way of getting the distro version'''

        r = RPM(str(self.getReleasePkg()))
        self.minorVersion = r.getVersion().split('.')[1]

        return self.minorVersion

    def getVersionString(self):
        '''CentOS specific way of getting the distro version'''

        r = RPM(str(self.getReleasePkg()))
        self.versionString = '.'.join(r.getVersion().split('.')[:2])

        return self.versionString

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
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

    def getReleasePkg(self):

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

                kpkgs =  [f for f in root.walkfiles('centos-release-notes*rpm')]
                if kpkgs: return kpkgs[0]
        except OSError:
            pass


    # syntactic sugar
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
        raise CopyError, dest

    def copyInitrd(self, dest, overwrite=False):
        raise CopyError, dest

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

    # syntactic sugar
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

        # These should describe the key directories that identify a RHEL 5 installation source layout.
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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

    def getMajorVersion(self):
        '''Redhat specific way of getting the distro version'''

        self.majorVersion = self.getVersion()
        return self.majorVersion

    def getMinorVersion(self):
        '''Redhat specific way of getting the distro version'''

        r = RPM(str(self.getReleasePkg()))
        self.minorVersion = r.getRelease().split('.')[1]

        return self.minorVersion

    def getVersionString(self):
        '''Redhat specific way of getting the distro version'''

        r = RPM(str(self.getReleasePkg()))
        self.versionString = '.'.join(r.getRelease().split('.')[:2])

        return self.versionString

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
            # sometimes, such as with rhel 5.3, the last value is 5.3 and not 5.
            # make it default to 5. Only if the last part is a digit, do we
            # use it.
            if words[i].isdigit():
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

    def getReleasePkg(self):

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
                li = [f for f in root.walkfiles('redhat-release-5Server*rpm')]
                kpkgs.extend(li)
        except OSError:
            pass

        return kpkgs[0]

    # syntactic sugar
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
        raise CopyError, dest

    def copyInitrd(self, dest, overwrite=False):
        raise CopyError, dest

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

    # syntactic sugar
    getKernelRpms = getKernelPackages

class Fedora8InstallSrc(DistroInstallSrcBase):
    """This class describes how a Fedora 8 installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(Fedora8InstallSrc,self).__init__()
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
        self.version = '8'

        # These should describe the key directories that identify a RHEL 5 installation source layout.
        self.pathLayoutAttributes = {
            '.treeinfo' : '.treeinfo',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'isolinuxbin' : 'isolinux/isolinux.bin',
            'imagesdir' : 'images',
            'stage2' : 'images/stage2.img',
            'packagesdir' : 'Packages',
            'repodatadir' : 'repodata',
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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

    def getVersion(self):
        '''Fedora 8 specific way of getting the distro version'''
        treeinfo = self.srcPath + '/.treeinfo'
        if os.path.exists(treeinfo):
            config = ConfigParser()
            config.read([str(treeinfo)])
            self.version = config.get('general','version')
        else:
            #try the fedora-release RPM under self.pathLayoutAttributes[packagesdir]
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{version}' 2> /dev/null
            pass
        return self.version

    def getArch(self):
        '''Fedora 8 specific way of getting the distro architecture'''
        treeinfo = self.srcPath + '/.treeinfo'
        if os.path.exists(treeinfo):
            config = ConfigParser()
            config.read([str(treeinfo)])
            self.arch = config.get('general','arch')
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

    # syntactic sugar
    getKernelRpms = getKernelPackages

class SLES10InstallSrc(DistroInstallSrcBase):
    """This class describes how a SLES 10 installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(SLES10InstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'sles'
        self.version = '10'

        self.getArch()

        # These should describe the key directories that identify a SLES 10 installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'boot/%s/loader' % self.arch,
            'kernel' : 'boot/%s/loader/linux' % self.arch,
            'initrd' : 'boot/%s/loader/initrd' % self.arch,
            'isolinuxbin' : 'boot/%s/loader/isolinux.bin' % self.arch,
            'packagesdir.noarch' : 'suse/noarch',
        }

        if self.arch == 'i386':
            self.pathLayoutAttributes['packagesdir.i586'] = 'suse/i586';
            self.pathLayoutAttributes['packagesdir.i686'] = 'suse/i686';
        elif self.arch == 'x86_64':
            self.pathLayoutAttributes['packagesdir.x86_64'] = 'suse/x86_64';

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

    def getMajorVersion(self):
        '''SLES specific way of getting the distro version'''

        f = open(self.srcPath / 'content', 'r')
        lines = f.readlines()
        f.close()

        # VERSION 10.2-0
        version = lines[1] # 2nd line
        self.majorVersion = re.compile('\d+').findall(version)[0]

        return self.majorVersion

    def getMinorVersion(self):
        '''SLES specific way of getting the distro version'''

        f = open(self.srcPath / 'content', 'r')
        lines = f.readlines()
        f.close()

        # VERSION 10.2-0 or VERSION 10
        version = lines[1] # 2nd line

        groups = re.compile('\d+').findall(version)
        if len(groups) >= 2:
            self.minorVersion = groups[1]
        else:
            self.minorVersion = '0' #10.0

        return self.minorVersion

    def getVersionString(self):
        '''SLES specific way of getting the distro version'''

        f = open(self.srcPath / 'content', 'r')
        lines = f.readlines()
        f.close()

        # VERSION 10.2-0 or VERSION 10
        version = lines[1] # 2nd line
        self.versionString = '.'.join(re.compile('\d+').findall(version)[:2])

        if self.versionString == '10':
            self.versionString = '10.0'

        return self.versionString

    def getVersion(self):
        '''SLES specific way of getting the distro version'''

        f = open(self.srcPath / 'content', 'r')
        lines = f.readlines()
        f.close()

        # VERSION 10.2-0
        version = lines[1] # 2nd line
        self.version = re.compile('\d+').findall(version)[0]

        return self.version

    def getArch(self):
        '''SLES specific way of getting the distro architecture'''
        if (self.srcPath / 'boot' / 'i386').exists():
            self.arch = 'i386'
        elif (self.srcPath / 'boot' / 'x86_64').exists():
            self.arch = 'x86_64'

        return self.arch

    def getKernelPackages(self):
        # set up pattern to match sles kernel packages
        pat = re.compile(r'kernel-default-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        _pkgsdir = [self.pathLayoutAttributes[k] for k in self.pathLayoutAttributes.keys() if k.startswith('packagesdir')]
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

    # syntactic sugar
    getKernelRpms = getKernelPackages


class OPENSUSE103InstallSrc(DistroInstallSrcBase):
    """This class describes how a openSUSE 10 installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(OPENSUSE103InstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'opensuse'
        self.version = '10.3'

        self.getArch()

        # These should describe the key directories that identify a SLES 10 installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'boot/%s/loader' % self.arch,
            'kernel' : 'boot/%s/loader/linux' % self.arch,
            'initrd' : 'boot/%s/loader/initrd' % self.arch,
            'isolinuxbin' : 'boot/%s/loader/isolinux.bin' % self.arch,
            'exe' : 'openSUSE10_3_LOCAL.exe',
            'packagesdir.noarch' : 'suse/noarch',
        }

        if self.arch == 'i386':
            self.pathLayoutAttributes['packagesdir.i586'] = 'suse/i586';
            self.pathLayoutAttributes['packagesdir.i686'] = 'suse/i686';
        elif self.arch == 'x86_64':
            self.pathLayoutAttributes['packagesdir.x86_64'] = 'suse/x86_64';

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
                errmsg = 'Write permission denied: %s' % path(dest)
                raise CopyError, errmsg
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
                errmsg = 'Write permission denied: %s' % path(dest).parent
                raise CopyError, errmsg

    def getMajorVersion(self):
        '''SLES specific way of getting the distro version'''

        f = open(self.srcPath / 'content', 'r')
        lines = f.readlines()
        f.close()

        # VERSION 10.3
        version = lines[1] # 2nd line
        self.majorVersion = re.compile('\d+').findall(version)[0]

        return self.majorVersion

    def getMinorVersion(self):
        '''SLES specific way of getting the distro version'''

        f = open(self.srcPath / 'content', 'r')
        lines = f.readlines()
        f.close()

        # VERSION 10.3
        version = lines[1] # 2nd line
        self.minorVersion = re.compile('\d+').findall(version)[1]

        return self.minorVersion

    def getVersionString(self):
        '''SLES specific way of getting the distro version'''

        f = open(self.srcPath / 'content', 'r')
        lines = f.readlines()
        f.close()

        version = lines[1] # 2nd line
        self.versionString = '.'.join(re.compile('\d+').findall(version)[:2])

        return self.versionString

    def getVersion(self):
        '''SLES specific way of getting the distro version'''

        f = open(self.srcPath / 'content', 'r')
        lines = f.readlines()
        f.close()

        # VERSION 10.2-0
        version = lines[1] # 2nd line
        self.version = '.'.join(re.compile('\d+').findall(version)[:2])

        return self.version

    def getArch(self):
        '''SLES specific way of getting the distro architecture'''
        if (self.srcPath / 'boot' / 'i386').exists():
            self.arch = 'i386'
        elif (self.srcPath / 'boot' / 'x86_64').exists():
            self.arch = 'x86_64'

        return self.arch

    def getKernelPackages(self):
        # set up pattern to match sles kernel packages
        pat = re.compile(r'kernel-default-[\d]+?.[\d]+?[\d]*?.[\d.+]+?')

        # get the packagesdir as the starting point
        _pkgsdir = [self.pathLayoutAttributes[k] for k in self.pathLayoutAttributes.keys() if k.startswith('packagesdir')]
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

    # syntactic sugar
    getKernelRpms = getKernelPackages


## Scientific Linux 5
class ScientificLinux5InstallSrc(DistroInstallSrcBase):
    """This class describes how a Scientific Linux installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(ScientificLinux5InstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'scientificlinux'
        self.version = '5'

        # These should describe the key directories that identify a Scientific Linux installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'isolinuxbin' : 'isolinux/isolinux.bin',
            'imagesdir' : 'images',
            'stage2' : 'images/stage2.img',
            'baseosdir' : 'SL',
            'packagesdir' : 'SL',
            'repodatadir' : 'SL/repodata',
            'rhupdatesdir' : 'RHupdates'
        }

        # The following determines the patchfile layout for Scientific Linux
        self.patchLayoutAttributes = {
            'patchdir' : 'images',
            'patchimage' : 'images/updates.img'
        }


    def verifyLocalVersion(self):
        return True

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
                raise CopyError, "Cannot write to %s. Check path and permissions." % dest
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
                raise CopyError, "Cannot write to %s. Check path and permissions." % dest

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
                raise CopyError, "Cannot write to %s. Check path and permissions." % dest
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
                raise CopyError, "Cannot write to %s. Check path and permissions." % dest

    def getArch(self):
        '''Scientific Linux specific way of getting the distro architecture'''
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

    def getMajorVersion(self):
        self.majorVersion = self.getVersion()
        return self.majorVersion

    def getMinorVersion(self):
        r = RPM(str(self.getReleasePkg()))
        self.minorVersion = r.getVersion().split('.')[1]

        return self.minorVersion

    def getVersionString(self):
        r = RPM(str(self.getReleasePkg()))
        self.versionString = '.'.join(r.getVersion().split('.')[:2])

        return self.versionString

    def getVersion(self):
        '''Scientific Linux specific way of getting the distro version'''
        return self.version

    def getReleasePkg(self):

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

                kpkgs =  [f for f in root.walkfiles('sl-release-notes*rpm')]
                if kpkgs: return kpkgs[0]
        except OSError:
            pass



    # syntactic sugar
    getKernelRpms = getKernelPackages

class ScientificLinux5AdditionalInstallSrc(DistroInstallSrcBase):
    """This class describes how a Scientific Linux 5 installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(ScientificLinux5AdditionalInstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'scientificlinux'
        self.version = '5'
        self.arch = 'noarch'
        self.isAdditionalType = True

        # These should describe the key directories that identify a Scientific Linux 5 installation source layout.
        self.pathLayoutAttributes = {
            'baseosdir' : 'SL',
            'packagesdir' : 'SL',
            'fastbugsdir' : 'fastbugs'
        }


    def getKernelPath(self):
        return None

    def getInitrdPath(self):
        return None

    def copyKernel(self, dest, overwrite=False):
        raise CopyError, "Cannot write to %s. Check path and permissions." % dest

    def copyInitrd(self, dest, overwrite=False):
        raise CopyError, "Cannot write to %s. Check path and permissions." % dest

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

    # syntactic sugar
    getKernelRpms = getKernelPackages

    def verifyLocalVersion(self):
        version = None
        discinfo = self.srcPath + '/.discinfo'

        if os.path.exists(discinfo):
            fp = file(discinfo, 'r')
            linelst = fp.readlines()
            fp.close()

            line = linelst[3] #fourth line is usually the arch
            version = line.strip().split()[0].lower()
        else:
            #rpm -qp fedora-release-[0-9]*.rpm --queryformat='%{arch}' 2> /dev/null
            pass

        if self.version ==version:
            return True
        else:
            return False

## End Scientific Linux 5

## Scientific Linux CERN 5
class ScientificLinuxCern5InstallSrc(DistroInstallSrcBase):
    """This class describes how a Scientific Linux CERN installation source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(ScientificLinuxCern5InstallSrc,self).__init__()
        if srcPath.startswith('http://'):
            self.srcPath = srcPath
            self.isRemote = True
        elif srcPath.startswith('file://'):
            self.srcPath = path(srcPath.split('file://')[1])
            self.isRemote = False
        else:
            self.srcPath = path(srcPath)
            self.isRemote = False

        self.ostype = 'scientificlinuxcern'
        self.version = '5'

        # These should describe the key directories that identify a Scientific Linux CERN installation source layout.
        self.pathLayoutAttributes = {
            'isolinuxdir' : 'isolinux',
            'kernel' : 'isolinux/vmlinuz',
            'initrd' : 'isolinux/initrd.img',
            'isolinuxbin' : 'isolinux/isolinux.bin',
            'imagesdir' : 'images',
            'stage2' : 'images/stage2.img',
            'baseosdir' : 'SL',
            'packagesdir' : 'SL',
            'repodatadir' : 'SL/repodata',
            'builddir' : 'build'
        }

        # The following determines the patchfile layout for Scientific Linux CERN
        self.patchLayoutAttributes = {
            'patchdir' : 'images',
            'patchimage' : 'images/updates.img'
        }

    def verifyLocalVersion(self):
        return True

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
                raise CopyError, "Cannot write to %s. Check path and permissions." % dest
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
                raise CopyError, "Cannot write to %s. Check path and permissions." % dest

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
                raise CopyError, "Cannot write to %s. Check path and permissions." % dest
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
                raise CopyError, "Cannot write to %s. Check path and permissions." % dest

    def getArch(self):
        '''Scientific Linux specific way of getting the distro architecture'''
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
        # set up pattern to match Scientific Linux CERN kernel packages
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

    def getMajorVersion(self):
        self.majorVersion = self.getVersion()
        return self.majorVersion

    def getMinorVersion(self):
        r = RPM(str(self.getReleasePkg()))
        self.minorVersion = r.getVersion().split('.')[1]

        return self.minorVersion

    def getVersionString(self):
        r = RPM(str(self.getReleasePkg()))
        self.versionString = '.'.join(r.getVersion().split('.')[:2])

        return self.versionString

    def getVersion(self):
        '''Scientific Linux CERN specific way of getting the distro version'''
        return self.version

    def getReleasePkg(self):

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

                kpkgs = [f for f in root.walkfiles('sl-release-notes*rpm')]
                if kpkgs:
                    # there may be multiple release notes RPMs but we want the latest
                    kpkgs.sort(reverse=True)
                    return kpkgs[0]
        except OSError:
            pass


    # syntactic sugar
    getKernelRpms = getKernelPackages

## End Scientific Linux CERN 5
