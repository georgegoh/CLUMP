#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
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

from kusu.buildkit.builder import PackageProfile, BuildProfile
from kusu.buildkit.builder import AutoToolsWrapper, RPMWrapper, DistroPackageWrapper, BinaryPackageWrapper, SRPMWrapper, BinaryDirectoryWrapper
from kusu.util.errors import UndefinedOSType
from kusu.buildkit.strategy import KusuKitFactory, KusuComponentFactory


from path import path
import subprocess

KIT_API='0.1'


def populatePackagesDir(buildprofile, arch='noarch'):
    """ Sweeps through the kitsrc dir and makes the built packages
        available in the packages dir.

    """
    # TODO : need to handle DEBs too instead of just RPMs

    filespecs = []

    if arch == 'x86':
        fspec = '*86.rpm'
    elif arch == 'x86_64':
        fspec = '*.x86_64.rpm'
    elif arch == 'noarch':
        fspec = '*.rpm'
    if not fspec in filespecs: filespecs.append(fspec)

    # add noarch packages no matter what
    if not '*.noarch.rpm' in filespecs: filespecs.append('*.noarch.rpm')

    # locate the built rpms
    builtdir = buildprofile.builddir / 'packages/RPMS'
    buildprofile.filenames = []
    for fspec in filespecs:
        for f in builtdir.walkfiles(fspec):
            _f = f.basename()
            if not _f in buildprofile.filenames:
                buildprofile.filenames.append(_f)
            if not path(buildprofile.pkgdir / _f).exists():
                pass
            else:
                path(buildprofile.pkgdir / _f).remove()

            cmd = 'ln -sf %s %s' % (f,buildprofile.pkgdir)
            lnP = subprocess.Popen(cmd,shell=True)
            lnP.wait()


    # also locate rpms that are located in the srcdir

    for fspec in filespecs:
        for f in buildprofile.srcdir.walkfiles(fspec):
            if f.endswith('.src.rpm'):
                pass
            else:
                cmd = 'ln -sf %s %s' % (f,buildprofile.pkgdir)
                lnP = subprocess.Popen(cmd,shell=True)
                lnP.wait()


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
    if not 'description' in kwargs: kwargs['description'] = ''
    if 'removeable' in kwargs:
        kwargs['removable'] = kwargs['removeable']
        del kwargs['removeable']
    if not 'removable' in kwargs and not 'removeable' in kwargs:
        kwargs['removable'] = True

    if not 'pkgname' in kwargs: kwargs['pkgname'] = ''
    if not 'name' in kwargs: kwargs['name'] = ''

    if not 'srctype' in kwargs: kwargs['srctype'] = 'kit'

    kit = KusuKitFactory[KIT_API](**kwargs)

    return kit


def Centos5Component(**kwargs):
    """ This is used for Centos5Component 5 components. """
    kwargs['ostype'] = 'centos'
    kwargs['osversion'] = '5'
    kwargs['osmajor'] = '5'
    return DefaultComponent(**kwargs)

def RHEL5Component(**kwargs):
    """ This is used for RHEL 5 components. """
    kwargs['ostype'] = 'rhel'
    kwargs['osversion'] = '5'
    kwargs['osmajor'] = '5'
    return DefaultComponent(**kwargs)

def ScientificLinux5Component(**kwargs):
    """ This is used for Scientific Linux 5 components. """
    kwargs['ostype'] = 'scientificlinux'
    kwargs['osversion'] = '5'
    kwargs['osmajor'] = '5'
    return DefaultComponent(**kwargs)

def ScientificLinuxCern5Component(**kwargs):
    """ This is used for Scientific Linux 5 components. """
    kwargs['ostype'] = 'scientificlinuxcern'
    kwargs['osversion'] = '5'
    kwargs['osmajor'] = '5'
    return DefaultComponent(**kwargs)

def Fedora6Component(**kwargs):
    """ This is used for Fedora Core 6 components. """
    kwargs['ostype'] = 'fedora'
    kwargs['osversion'] = '6'
    kwargs['osmajor'] = '6'
    return DefaultComponent(**kwargs)

def SLES10Component(**kwargs):
    """ This is used for SLES 10 components. """
    kwargs['ostype'] = 'sles'
    kwargs['osversion'] = '10'
    kwargs['osmajor'] = '10'
    return DefaultComponent(**kwargs)

def OPENSUSE103Component(**kwargs):
    """ This is used for OPENSUSE 10.3 components. """
    kwargs['ostype'] = 'opensuse'
    kwargs['osversion'] = '10.3'
    kwargs['osmajor'] = '10'
    kwargs['osminor'] = '3'
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
    if not 'description' in kwargs: kwargs['description'] = ''
    if not 'srctype' in kwargs: kwargs['srctype'] = 'component'
    if not 'name' in kwargs: kwargs['name'] = ''
    if not 'pkgname' in kwargs: kwargs['pkgname'] = ''
    if not 'ostype' in kwargs: kwargs['ostype'] = ''
    if not 'osversion' in kwargs: kwargs['osversion'] = ''
    if not 'osmajor' in kwargs: kwargs['osmajor'] = ''
    if not 'osminor' in kwargs: kwargs['osminor'] = ''

    component = KusuComponentFactory[KIT_API](**kwargs)

    return component


def BinaryPackage(**kwargs):
    """ This is used to handle binary distribution packages. """
    return Package(srctype='binary')

def BinaryDirectory(**kwargs):
    """ This is used to handle binary distribution packages. """
    return Package(srctype='binarydir')


def DistroPackage(**kwargs):
    """ This is used to handle distro packages. """
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
    elif kwargs['srctype'] == 'binary':
        pkg = PackageProfile(BinaryPackageWrapper(),**kwargs)
    elif kwargs['srctype'] == 'binarydir':
        pkg = PackageProfile(BinaryDirectoryWrapper(),**kwargs)
    elif kwargs['srctype'] == 'distro':
        pkg = PackageProfile(DistroPackageWrapper(),**kwargs)
    elif kwargs['srctype'] == 'rpm':
        pkg = PackageProfile(RPMWrapper(),**kwargs)
    elif kwargs['srctype'] == 'srpm':
        pkg = PackageProfile(SRPMWrapper(),**kwargs)


    return pkg

