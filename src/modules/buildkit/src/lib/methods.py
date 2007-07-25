#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.buildkit.kitsource import KusuComponent, KusuKit
from kusu.buildkit.builder import AutoToolsWrapper, PackageProfile, BinaryPackageWrapper, SRPMWrapper
from kusu.util.errors import UndefinedOSType, UnknownPackageType, UndefinedComponentInfo, UndefinedKitInfo
from path import path

def processKitInfo(kitinfo):
    """ Loads the kitinfo file and returns a tuple containing two elements - the kit metainfo 
        and a list of component metainfo contained in that file. A metainfo is a dict object.
    """
    kitinfo = path(kitinfo)
    if not kitinfo.isfile(): return ({},[])
    
    ns = {}
    execfile(kitinfo,ns)

    kit = ns.get('kit',{})
    components = ns.get('components',[])
    
    return (kit,components)

def DefaultKit(**kwargs):
    """ The most basic type of kits. """

    # set a few defaults if not set initially
    if not 'license' in kwargs: kwargs['license'] = 'LGPL'
    if not 'version' in kwargs: kwargs['version'] = '0.1'
    if not 'release' in kwargs: kwargs['release'] = '0'
    if not 'arch' in kwargs: kwargs['arch'] = 'noarch'
    if not 'scripts' in kwargs: kwargs['scripts'] = []
    if not 'dependencies' in kwargs: kwargs['dependencies'] = []
    if not 'components' in kwargs: kwargs['components'] = []

    kit = KusuKit(**kwargs)

    return kit


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

    # set a few defaults if not set initially
    if not 'arch' in kwargs: kwargs['arch'] = 'noarch'
    if not 'compversion' in kwargs: kwargs['compversion'] = '0.1'
    if not 'comprelease' in kwargs: kwargs['comprelease'] = '0'
    if not 'ngtypes' in kwargs: kwargs['ngtypes'] = ['installer','compute']
    
    component = KusuComponent(**kwargs)
  
    return component


def BinaryPackage(**kwargs):
    """ This is used to handle binary distribution packages. """
    return Package(srctype='binarydist')

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
    if kwargs['srctype'] == 'autotools':
        pkg = PackageProfile(AutoToolsWrapper(),**kwargs)
    elif kwargs['srctype'] == 'binarydist':
        pkg = PackageProfile(BinaryPackageWrapper(),**kwargs)
    elif kwargs['srctype'] == 'distro':
        pass
    elif kwargs['srctype'] == 'rpm':
        pass
    elif kwargs['srctype'] == 'srpm':
        pkg = PackageProfile(SRPMWrapper(),**kwargs)
        

    return pkg

