#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import subprocess
from path import path
from Cheetah.Template import Template
import tarfile
from random import choice
import string
import os
import pwd
from kusu.buildkit.kitsource import KitSrcFactory
from kusu.util.tools import cpio_copytree

SUPPORTED_TARFILES_EXT = ['.tgz','.tar.gz','.tbz2','.tar.bz2']

def genrandomstr(length=8):
    chars = string.letters + string.digits
    return ''.join([choice(chars) for i in range(length)])

def setupRPMMacrofile(buildprofile):
    """ Creates a proper .rpmmacros file for purposes of building kits. 
        If an existing .rpmmacros exists, it will be renamed and this
        function will return the old .rpmmacros file for safekeeping.
    """
    userhome = path(pwd.getpwuid(os.getuid())[5])
    rpmmacros = userhome / '.rpmmacros'

    oldrpmmacros = None
    if rpmmacros.exists():
        ext = genrandomstr()
        oldrpmmacros = '.'.join([rpmmacros,ext])
        rpmmacros.rename(oldrpmmacros)

    rpmtopdir = path(buildprofile.builddir / 'packages')
    if not rpmtopdir.exists(): 
        rpmtopdir.mkdir()
        path(rpmtopdir / 'BUILD').mkdir()
        path(rpmtopdir / 'RPMS').mkdir()
    kusuroot = path(os.environ.get('KUSU_ROOT','/opt/kusu'))
    tmpldir = kusuroot / 'etc/buildkit-templates'
    rpmmacroTmpl = path(tmpldir / 'rpmmacros.tmpl')

    d = {}
    d['topdir'] = rpmtopdir
    d['tmppath'] = path(buildprofile.tmpdir)

    t = Template(file=str(rpmmacroTmpl),searchList=[d])
    f = open(rpmmacros,'w')
    f.write(str(t))

    if oldrpmmacros: return oldrpmmacros


def prepareNS(packageprofile):
    """ Prepare a namespace dict for generating templates. """
    d = {}
    d['pkgname'] = packageprofile.name
    d['approot'] = packageprofile.installroot
    d['pkgversion'] = packageprofile.version
    d['pkgrelease'] = packageprofile.release
    if packageprofile.license:
        d['license'] = packageprofile.license
    if packageprofile.author:
        d['author'] = packageprofile.author
    if packageprofile.vendor:
        d['vendor'] = packageprofile.vendor
    
    return d


def getPackageSpecTmpl(templatesdir):
    """ Gets the specfile template for package. """
    root = path(templatesdir)
    spectmpl = root.files('package.spec.tmpl')[0]
    
    return spectmpl
    
def getComponentSpecTmpl(templatesdir):
    """ Gets the specfile template for package. """
    root = path(templatesdir)
    spectmpl = root.files('component.spec.tmpl')[0]
    
    return spectmpl
    
def getKitSpecTmpl(templatesdir):
    """ Gets the specfile template for package. """
    root = path(templatesdir)
    spectmpl = root.files('kit.spec.tmpl')[0]
    
    return spectmpl    

def getDirName(p):
    """ Returns the unpacked directory name of a tarfile. """
    li = [ext for ext in SUPPORTED_TARFILES_EXT if ext in p]
    if li:
        return p.split(li[0])[0]

def unpackTarfile(filepath, destroot=None):
    """ Convenience method to unpack tarfiles. """
    if not destroot:
        destroot = path.getcwd()
    else:
        destroot = path(destroot)

    pkg = tarfile.open(filepath)
    for f in pkg:
        pkg.extract(f,destroot)

def setupprofile(**kwargs):
    """ Convenience method to setup buildprofile. """
    if not kwargs:
        # check if the current directory looks like a build environment
        _basedir = path.getcwd()
        _kitsrc = KitSrcFactory(_basedir)
        if _kitsrc.verifyLocalSrcPath():
            builddir = _basedir / 'artifacts'
            tmpdir = _basedir / 'tmp'
            return BuildProfile(builddir=builddir,tmpdir=tmpdir)
    builddir = kwargs.get('builddir', '')
    tmpdir = kwargs.get('tmpdir', '')
    return BuildProfile(builddir=builddir,tmpdir=tmpdir)

class BuildProfile(object):
    """ Profile used to store build site configuration. """
    
    def __init__(self, **kwargs):
        self.builddir = kwargs.get('builddir','')
        self.tmpdir = kwargs.get('tmpdir','')
        kusuroot = path(os.environ.get('KUSU_ROOT','/opt/kusu'))
        tmpldir = kusuroot / 'etc/buildkit-templates'
        self.templatesdir = kwargs.get('templatesdir', tmpldir)

class PackageProfile(object):
    """ Package-specific profile used to build packages. """
    
    def __init__(self,**kwargs):
        """docstring for __init__"""
        self.name = kwargs.get('name',None)
        self.version = kwargs.get('version',None)
        self.release = kwargs.get('release','0')
        self.filepath = kwargs.get('filepath',None)
        self.installroot = kwargs.get('installroot',None)
        self.author = kwargs.get('author','')
        self.vendor = kwargs.get('vendor','')
        self.license = kwargs.get('license','')
        self.buildprofile = kwargs.get('buildprofile',setupprofile())


class GNUBuildTools(object):
    """ Wrapper around GNU Autotools system. """

    verbose = False
    
    def setup(self, filepath, buildprofile, packageNS):
        """ Setups the tool. filepath refers to the path of the tarfile.
            buildprofile refers to the profile that will be used for building.
            packageNS is the namespace used for generating files from templates.
        """
        self.builddir = path(buildprofile.builddir)
        self.tmpdir = path(buildprofile.tmpdir)
        self.templatesdir = path(buildprofile.templatesdir)
        self.filepath = path(filepath)
        self.namespace = packageNS
        self.fullname = getDirName(self.filepath.basename())
        self.buildsrc = self.tmpdir / self.fullname
        
    def cleanup(self):
        if self.buildsrc.exists(): self.buildsrc.rmtree()
        
    def configure(self, **kwargs):
        """ Configuration stage for this class. """
        if not self.buildsrc.exists():
            unpackTarfile(self.filepath,self.tmpdir)
        
        configure_args = []
        for k,v in kwargs.items():
            configure_args.append('%s=%s' % (k,v))

        if self.verbose:
            cmd = ' '.join(['./configure'] + configure_args)
        else:
            cmd = ' '.join(['./configure'] + configure_args + ['> /dev/null 2>&1'])

        configP = subprocess.Popen(cmd,shell=True,cwd=self.buildsrc)
        configP.wait()
        
        
    def build(self, **kwargs):
        """ Build stage for this class. """
        
        make_args = []
        for k,v in kwargs.items():
            make_args.append('%s=%s' % (k,v))
    
        if self.verbose:
            cmd = ' '.join(['make'] + make_args)
        else:
            cmd = ' '.join(['make'] + make_args + ['> /dev/null 2>&1'])
        
        makeP = subprocess.Popen(cmd,shell=True,cwd=self.buildsrc)
        makeP.wait()        
       
    def install(self, **kwargs):
        """ Installation stage for this class. """

        makeinstall_args = []
        for k,v in kwargs.items():
            makeinstall_args.append('%s=%s' % (k,v))
        
        if self.verbose:
            cmd = ' '.join(['make'] + makeinstall_args + ['install'])
        else:
            cmd = ' '.join(['make'] + makeinstall_args + ['install > /dev/null 2>&1'])

        makeinstallP = subprocess.Popen(cmd,shell=True,cwd=self.buildsrc)
        makeinstallP.wait()        

        
    def _packRPM(self):
        """ RPM packaging stage for this class. """
        buildroot = 'packages/BUILD/%s-%s-%s' % (self.namespace['pkgname'],
            self.namespace['pkgversion'],
            self.namespace['pkgrelease'])
            
        destroot = self.tmpdir / buildroot
        if destroot.exists(): destroot.rmtree()
        destroot.makedirs()
        self.install(prefix=destroot)
        tmpl = getPackageSpecTmpl(self.templatesdir)
        _specfile = '.'.join([self.namespace['pkgname'],'spec'])
        specfile = self.builddir / _specfile
        
        rpmbuilder = RPMBuilder(ns=self.namespace,template=tmpl,sourcefile=specfile,verbose=self.verbose)
        rpmbuilder.write()
        rpmbuilder.build()
        
        
    def pack(self, pkgtype='rpm'):
        """ Packaging stage. """
        
        if pkgtype == 'rpm':
            return self._packRPM()

class SRPMBuildTools(object):
    """ Wrapper around SRPM build system. """

    verbose = False

    def setup(self, filepath, buildprofile, packageNS):
        """ Setups the tool. filepath refers to the path of the srpm file.
            buildprofile refers to the profile that will be used for building.
            packageNS is the namespace used for generating files from templates.
        """
        self.builddir = path(buildprofile.builddir)
        self.tmpdir = path(buildprofile.tmpdir)
        self.templatesdir = path(buildprofile.templatesdir)
        self.filepath = path(filepath)
        self.namespace = packageNS
        self.fullname = getDirName(self.filepath.basename())
        self.buildsrc = self.tmpdir / self.fullname

    def cleanup(self):
        if self.buildsrc.exists(): self.buildsrc.rmtree()

    def configure(self, **kwargs):
        """ Configuration stage for this class. """
        # not needed for SRPM packages.
        pass

    def build(self, **kwargs):
        """ Build stage for this class. """

        # not needed for SRPM packages.
        pass      

    def install(self, **kwargs):
        """ Installation stage for this class. """

        # not needed for SRPM packages.
        pass

    def _packRPM(self):
        """ RPM packaging stage for this class. """
        buildroot = 'packages/BUILD/%s-%s-%s' % (self.namespace['pkgname'],
            self.namespace['pkgversion'],
            self.namespace['pkgrelease'])

        destroot = self.tmpdir / buildroot
        if destroot.exists(): destroot.rmtree()
        destroot.makedirs()
        self.install(prefix=destroot)
        tmpl = getPackageSpecTmpl(self.templatesdir)
        srpmfile = self.filepath

        rpmbuilder = RPMBuilder(ns=self.namespace,template=tmpl,sourcefile=srpmfile,verbose=self.verbose)
        rpmbuilder.write()
        rpmbuilder.build()


    def pack(self, pkgtype='rpm'):
        """ Packaging stage. """

        if pkgtype == 'rpm':
            return self._packRPM()

class BinaryPackageBuildTools(object):
    """ Wrapper around binary distribution packages. """

    verbose = False

    def setup(self, filepath, buildprofile, packageNS):
        """ Setups the tool. filepath refers to the path of the binary distribution tarfile.
            buildprofile refers to the profile that will be used for building.
            packageNS is the namespace used for generating files from templates.
        """
        self.builddir = path(buildprofile.builddir)
        self.tmpdir = path(buildprofile.tmpdir)
        self.templatesdir = path(buildprofile.templatesdir)
        self.filepath = path(filepath)
        self.namespace = packageNS
        self.fullname = getDirName(self.filepath.basename())
        self.buildsrc = self.tmpdir / self.fullname

    def cleanup(self):
        if self.buildsrc.exists(): self.buildsrc.rmtree()

    def configure(self, **kwargs):
        """ Configuration stage for this class. """

        # unpack the tarfile
        if not self.buildsrc.exists():
            unpackTarfile(self.filepath,self.tmpdir)
        
        
    def build(self, **kwargs):
        """ Build stage for this class. """
        pass      

    def install(self, prefix):
        """ Installation stage for this class. """
        destroot = path(prefix).abspath()
        cpio_copytree(self.buildsrc,destroot)

    def _packRPM(self):
        """ RPM packaging stage for this class. """
        buildroot = 'packages/BUILD/%s-%s-%s' % (self.namespace['pkgname'],
            self.namespace['pkgversion'],
            self.namespace['pkgrelease'])
            
        destroot = self.tmpdir / buildroot
        if destroot.exists(): destroot.rmtree()
        destroot.makedirs()
        self.install(destroot)
        tmpl = getPackageSpecTmpl(self.templatesdir)
        _specfile = '.'.join([self.namespace['pkgname'],'spec'])
        specfile = self.builddir / _specfile
        
        rpmbuilder = RPMBuilder(ns=self.namespace,template=tmpl,sourcefile=specfile,verbose=self.verbose)
        rpmbuilder.write()
        rpmbuilder.build()


    def pack(self, pkgtype='rpm'):
        """ Packaging stage. """

        if pkgtype == 'rpm':
            return self._packRPM()



class RPMBuilder:

    ns = {}
    template = ''
    sourcefile = ''
    verbose = False

    def __init__(self, ns, template, sourcefile, verbose=False):
        self.ns = ns
        self.template = template
        self.sourcefile = sourcefile
        self.verbose = verbose

    def write(self):
        f = path(self.specfile)
        out = open(f, 'w')
        t = Template(file=str(self.template), searchList=[self.ns])  
        out.write(str(t))
        out.close()

    def build(self):

        if self.sourcefile.endswith('.spec'):
            # spec file
            if self.verbose:
                cmd = 'rpmbuild -bb %s' % (self.sourcefile)
            else:
                cmd = 'rpmbuild -bb %s > /dev/null 2>&1' % (self.sourcefile)

        if self.sourcefile.endswith('.src.rpm') or self.sourcefile.endswith('.srpm'):
            # srpm file
            if self.verbose:
                cmd = 'rpmbuild --rebuild %s' % (self.sourcefile)
            else:
                cmd = 'rpmbuild --rebuild %s > /dev/null 2>&1' % (self.sourcefile)


        
        rpmP = subprocess.Popen(cmd,shell=True,)
        rpmP.wait()
        


