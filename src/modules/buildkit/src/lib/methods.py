#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.buildkit.kitsource import KusuComponent, KusuKit, KitSrcFactory
from kusu.buildkit.builder import PackageProfile, BuildProfile
from kusu.buildkit.builder import AutoToolsWrapper, RPMWrapper, DistroPackageWrapper, BinaryPackageWrapper, SRPMWrapper
from kusu.util.errors import UndefinedOSType, InvalidBuildProfile, KitinfoSyntaxError
from path import path
import subprocess

def setupprofile(basedir=''):
    """ Convenience method to setup buildprofile. 
    """
    if not basedir:
        # check if the current directory looks like a build environment
        _basedir = path.getcwd()
        _kitsrc = KitSrcFactory(_basedir)
        if _kitsrc.verifyLocalSrcPath():
            builddir = _basedir / 'artifacts'
            pkgdir = _basedir / 'packages'
            srcdir = _basedir / 'sources'
            docsdir = _basedir / 'docs'
            pluginsdir = _basedir / 'plugins'
            tmpdir = _basedir / 'tmp'
            return BuildProfile(builddir=builddir,tmpdir=tmpdir,
                srcdir=srcdir,pkgdir=pkgdir,docsdir=docsdir,pluginsdir=pluginsdir)
        else:
            raise InvalidBuildProfile
    _basedir = path(basedir)
    _kitsrc = KitSrcFactory(_basedir)
    if _kitsrc.verifyLocalSrcPath():        
        builddir = _basedir / 'artifacts'
        srcdir = _basedir / 'sources'
        docsdir = _basedir / 'docs'
        pluginsdir = _basedir / 'plugins'
        pkgdir = _basedir / 'packages'
        tmpdir = _basedir / 'tmp'
        return BuildProfile(builddir=builddir,tmpdir=tmpdir,
            srcdir=srcdir,pkgdir=pkgdir,docsdir=docsdir,pluginsdir=pluginsdir)
    else:
        raise InvalidBuildProfile
        
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

    for fspec in filespecs:
        for f in builtdir.walkfiles(fspec):
            _f = f.basename()
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


def processKitInfo(kitinfo):
    """ Loads the kitinfo file and returns a tuple containing two elements - the kit metainfo 
        and a list of component metainfo contained in that file. A metainfo is a dict object.
    """
    kitinfo = path(kitinfo)
    if not kitinfo.isfile(): return ({},[])
    
    ns = {}

    # If there is a syntax error in the kitinfo file, holla!
    try:
        execfile(kitinfo,ns)
    except SyntaxError, e:
        error_message = "%s in kitinfo file %s at line %s, column %s" % \
                        (e.msg, e.filename, e.lineno, e.offset)
        raise KitinfoSyntaxError, error_message

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
    if not 'description' in kwargs: kwargs['description'] = ''
    if 'removeable' in kwargs:
        kwargs['removable'] = kwargs['removeable']
        del kwargs['removeable']
    if not 'removable' in kwargs and not 'removeable' in kwargs:
        kwargs['removable'] = True
        
    if not 'pkgname' in kwargs: kwargs['pkgname'] = ''
    if not 'name' in kwargs: kwargs['name'] = ''
    
    if not 'srctype' in kwargs: kwargs['srctype'] = 'kit'

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
    if not 'description' in kwargs: kwargs['description'] = ''
    if not 'srctype' in kwargs: kwargs['srctype'] = 'component'
    if not 'name' in kwargs: kwargs['name'] = ''
    if not 'pkgname' in kwargs: kwargs['pkgname'] = ''
    if not 'ostype' in kwargs: kwargs['ostype'] = ''
    if not 'osversion' in kwargs: kwargs['osversion'] = ''
    
    component = KusuComponent(**kwargs)
  
    return component


def BinaryPackage(**kwargs):
    """ This is used to handle binary distribution packages. """
    return Package(srctype='binary')

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
    elif kwargs['srctype'] == 'distro':
        pkg = PackageProfile(DistroPackageWrapper(),**kwargs)
    elif kwargs['srctype'] == 'rpm':
        pkg = PackageProfile(RPMWrapper(),**kwargs)
    elif kwargs['srctype'] == 'srpm':
        pkg = PackageProfile(SRPMWrapper(),**kwargs)
        

    return pkg

