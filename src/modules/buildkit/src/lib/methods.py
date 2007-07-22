#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.buildkit.kitsource import KusuComponent, ComponentInfo, KusuKit, KitInfo
from kusu.buildkit.builder import AutoToolsWrapper, PackageProfile
from kusu.util.errors import UndefinedOSType, UnknownPackageType, UndefinedComponentInfo, UndefinedKitInfo


def DefaultKit(**kwargs):
    """ The most basic type of kits. """
    if not 'name' in kwargs: raise UndefinedKitInfo
    name = kwargs['name']
    author = kwargs.get('author','')
    vendor = kwargs.get('vendor','')
    license = kwargs.get('license','LGPL')
    version = kwargs.get('version','0.1')
    release = kwargs.get('release','0')
    arch = kwargs.get('arch','noarch')
    kitinfo = KitInfo(name=name,author=author,vendor=vendor,
        license=license,arch=arch,version=version,release=release)
    return Kit(kitinfo)

def Kit(kitinfo):
    """ Convenience method to setup the KusuKit class. """
    return KusuKit(kitinfo)

def Centos5Component(**kwargs):
    """ This is used for Centos5Component 5 components. """
    kwargs['ostype'] = 'centos'
    kwargs['osversion'] = '5'
    return DefaultComponent(**kwargs)

def RHEL5Component(**kwargs):
    """ This is used for RHEL 5 components. """
    kwargs['ostype'] = 'rhel'
    kwargs['osversion'] = '5'
    return DefaultComponent(**kwargs)

def Fedora6Component(**kwargs):
    """ This is used for Fedora Core 6 components. """
    kwargs['ostype'] = 'fedora'
    kwargs['osversion'] = '6'
    return DefaultComponent(**kwargs)

def DefaultComponent(**kwargs):
    """ The default component will associate itself to both the installer and compute
        nodegroups if the ngtypes is not defined.
    """
    if not 'name' in kwargs: raise UndefinedComponentInfo
    name = kwargs['name']
    ostype = kwargs.get('ostype','')
    osversion = kwargs.get('osversion','')
    arch = kwargs.get('arch','noarch')
    compversion = kwargs.get('compversion','0.1')
    comprelease = kwargs.get('comprelease','0')
    ngtypes = kwargs.get('ngtypes',['installer','compute'])
    compinfo = ComponentInfo(name=name,ostype=ostype,osversion=osversion,
        arch=arch,compversion=compversion,comprelease=comprelease,ngtypes=ngtypes)
    kwargs['componentinfo'] = compinfo
    
    return Component(**kwargs)

def Component(**kwargs):
    """ Convenience method to setup KusuComponent class. """
    return KusuComponent(**kwargs)

def BinaryPackage(**kwargs):
    """ This is used to handle binary distribution packages. """
    kwargs['srctype'] = 'binarydist'
    return Package(**kwargs)

def DistroPackage(**kwargs):
    """ This is used to handle distro packages. """
    if 'ostype' not in kwargs: raise UndefinedOSType
    kwargs['srctype'] = 'distro'
    return Package(**kwargs)
    
def RPMPackage(**kwargs):
    """ This is used to handle rpm packages. """
    kwargs['srctype'] = 'rpm'
    return Package(**kwargs)

def SRPMPackage(**kwargs):
    """ This is used to handle srpm packages. """
    kwargs['srctype'] = 'srpm'
    return Package(**kwargs)

def SourcePackage(**kwargs):
    """ This is used to handle GNU Autotools packages. """
    kwargs['srctype'] = 'autotools'
    return Package(**kwargs)

def Package(**kwargs):
    """ Basic convenience package method. """
    if 'srctype' not in kwargs: raise UnknownPackageType
    if kwargs['srctype'] == 'autotools':
        profile = PackageProfile(**kwargs)
        pkg = AutoToolsWrapper(profile)

    return pkg

