#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.buildkit.kitsource import KusuComponent
from kusu.buildkit.builder import GNUBuildTools, PackageProfile
from kusu.util.errors import UndefinedOSType, UnknownPackageType


def DefaultComponent(**kwargs):
    """ The default component will associate itself to both the installer and compute
        nodegroups.
    """
    kwargs['ngtypes'] = ['installer','compute']
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
    pkg = PackageProfile(**kwargs)
    pkg.tools = GNUBuildTools()
    pkg.setup = pkg.tools.setup
    pkg.configure = pkg.tools.configure    
    pkg.build = pkg.tools.build    
    pkg.install = pkg.tools.install
    pkg.pack = pkg.tools.pack
    pkg.cleanup = pkg.tools.cleanup
    
    return pkg

