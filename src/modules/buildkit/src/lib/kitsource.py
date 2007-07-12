#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module contains the kitsource methods and classes for Kusu Kits"""

from path import path
from kusu.util.errors import KitSrcAlreadyExists, FileDoesNotExistError
from kusu.util.errors import NotImplementedError, DirDoesNotExistError
from kusu.util.errors import PackageBuildError, KitBuildError
import tempfile
import tarfile
from kusu.util import tools
import subprocess

SUPPORTED_TARFILES_EXT = ['.tgz','.tar.gz','.tbz2','.tar.bz2']

def getDirName(p):
    """ Returns the unpacked directory name of a tarfile. """
    li = [ext for ext in SUPPORTED_TARFILES_EXT if ext in p]
    if li:
        return p.split(li[0])[0]

class KitSrcBase(object):
    """ Base class for a Kit source and the operations that can work on it. """
    def __init__(self):
        """The following attributes should be defined by the subclasses.

        self.srcPath - refers to the path of the Kit source.
        self.arch - Architechure of the Kit.
        self.type - The type of the Kit. It should be in lowercase for consistency. May be used for comparison cases.
        self.version - Version of the Kit.
        self.pathLayoutAttributes - a dict describing the layout of key directories/files for the installation source. 

        The keys should the logical names of each layout attribute and the value should be the relative paths of the 
        directories/files."""

        self.srcPath = None
        self.type = None
        self.arch = None
        self.version = None
        self.arch = None
        self.pathLayoutAttributes = {}

    def verifySrcPath(self):
        """Call the correct verify*SrcPath method."""

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
        
    def prepareSrcPath(self):
        """Make the paths as described in the pathLayoutAttributes."""
        
        try:
            if self.srcPath.exists(): raise KitSrcAlreadyExists
        except AttributeError:
            # we could be testing on a NoneType object instead of a Path object
            pass
        
        # create the initial srcPath
        self.srcPath.mkdir()
        
        # create the paths for each attribute listed
        for k,v in self.pathLayoutAttributes.items():
            if k.endswith('comp'):
                if 'dir' in v.keys():
                    path(self.srcPath / v['dir']).makedirs()
                elif 'file' in v.keys():
                    path(self.srcPath / v['file']).touch()
            if k.endswith('comprc'):
                if 'dir' in v.keys():
                    path(self.srcPath / v['dir']).makedirs()
                    for i in ['pre', 'preun', 'post', 'postun']: 
                        path(self.srcPath / v['dir'] / i).mkdir()
                elif 'file' in v.keys():
                    path(self.srcPath / v['file']).touch()
            if k.endswith('dir'):
                if 'dir' in v.keys():
                    path(self.srcPath / v['dir']).makedirs()                    
                    
        
class GeneralKitSrc(KitSrcBase):
    """This class describes how a general kit source should be and the operations that can work on it."""

    def __init__(self, srcPath):
        super(GeneralKitSrc,self).__init__()
        self.srcPath = path(srcPath)

        self.type = 'general'

        # These should describe the key directories that identify a kit source layout.
        self.pathLayoutAttributes = {
            'rhelcomp' : {'dir':'components/rhel'},
            'rhelcomprc' : {'dir':'components/rhel/rc'},
            'centoscomp' : {'dir':'components/centos'},
            'centoscomprc' : {'dir':'components/centos/rc'},
            'fedoracomp' : {'dir':'components/fedora'},
            'fedoracomprc' : {'dir':'components/fedora/rc'},            
            'susecomp' : {'dir':'components/suse'},
            'susecomprc' : {'dir':'components/suse/rc'},            
            'ubuntucomp' : {'dir':'components/ubuntu'},
            'ubuntucomprc' : {'dir':'components/ubuntu/rc'},
            'scriptsdir' : {'dir':'scripts'},
            'pkgsdir' : {'dir':'packages'},
            'srcdir' : {'dir':'sources'},
            'tmpdir' : {'dir':'tmp'},
            'kitinfo' : {'file':'dotkitinfo'}
        }
        
class BinaryKitSrc(KitSrcBase): pass

def KitSrcFactory(srcPath):
    """ Factory function that returns a KitSrcBase instance. """
    # right now, we only return GeneralKitSrc
    return GeneralKitSrc(srcPath)
    
class SourcePkg(object):
    """ This class describes how a tarball archive (archives created with tar and gzip/bzip2) should be and
        the operations that can work on it.
    """
    
    def __init__(self, packageprofile):
        """ packageprofile refers to the build-specific information regarding
            package. 
        """
        self.packageprofile = packageprofile
                    
    def unpack(self,destdir=None):
        """ Unpacks the source package to the current directory if 
            the destdir is not defined.
        """
        raise NotImplementedError
        

class GNUBuildTarballPkg(SourcePkg):
    """ GNU build tarballs refers to tarballs that uses the GNU Autoconf/Automake/Autogen build system. """

    def __init__(self,packageprofile):
        SourcePkg.__init__(self,packageprofile)
        # assets that make up a GNUBuildTarballPkg goes here
        self._assets = ['configure', 
                        'configure.ac']
        self.alreadyBuilt = False
        
    def unpack(self,destdir=None):
        if not destdir:
            destdir = path.getcwd()
        else:
            destdir = path(destdir)
            
        pkg = tarfile.open(self.packageprofile.filepath)
        for f in pkg:
            pkg.extract(f,destdir)

        
    def verify(self):
        """ Verify that it is indeed a GNU build tarball"""
        if not tarfile.is_tarfile(self.packageprofile.filepath): return False
        tmppath = path(tools.mkdtemp(prefix='kitsrc-'))
        self.unpack(tmppath)
        
        if not tmppath.dirs():
            # definitely not a standard GNUBuildTarballPkg
            if tmppath.exists(): tmppath.rmtree
            return False
        srcdir = tmppath.dirs()[0]

        assetsMissing = [ f for f in self._assets if not path(srcdir / f).exists() ]
        if tmppath.exists(): tmppath.rmtree()
        if assetsMissing: return False

        return True
        
    def build(self):
        """ Build the source package based on the packageprofile"""
        
        prefix = self.packageprofile.installroot
            
        if not self.packageprofile.builddir: raise DirDoesNotExistError
        builddir = path(self.packageprofile.builddir)
        if not builddir.exists(): raise DirDoesNotExistError
        srcdir = builddir / self.packageprofile.dirname
        if srcdir.exists(): srcdir.rmtree()        
        self.unpack(builddir)
        if not srcdir.exists(): raise PackageBuildError, "Unpacked Dir not found!"
        
        configure_args = []
        make_args = []
        if prefix:
            configure_args.append('--prefix=%s' % prefix)
     
        cmd = ' '.join(['./configure'] + configure_args)
        configP = subprocess.Popen(cmd,shell=True,cwd=srcdir)
        configP.wait()

        cmd = ' '.join(['make'] + make_args)
        makeP = subprocess.Popen(cmd,shell=True,cwd=srcdir)
        makeP.wait()
        
        self.alreadyBuilt = True
        self.srcdir = srcdir
        

    def install(self):
        """ Installs the artefacts created during build """
        buildroot = self.packageprofile.buildroot

        makeinstall_args = []
        if buildroot:
            makeinstall_args.append('prefix=%s' % buildroot)        
        
        if not self.alreadyBuilt: self.build()
        cmd = ' '.join(['make'] + makeinstall_args + ['install'])
        makeinstallP = subprocess.Popen(cmd,shell=True,cwd=self.srcdir)
        makeinstallP.wait()
        
    def cleanup(self):
        """ Housekeeping """
        if self.srcdir.exists(): self.srcdir.rmtree()
        self.alreadyBuilt = False
        self.srcdir = None
        
        
class BinaryDistTarballPkg(SourcePkg):
    """ Binary distribution tarball packages refers to packages that contain already built artefacts such
        as subdirectories (bin,etc,lib) and files.    
    """
    
    def __init__(self,packageprofile):
        SourcePkg.__init__(self,packageprofile)
        
    def install(self):
        """ Installs the artefacts created during build """
        pass

        
class SRPMPkg(SourcePkg):
    """ This class describes how a Source RPM package should be and the operations that work on it. """
    
    def __init__(self, packageprofile):
        SourcePkg.__init__(self, packageprofile)

    def verify(self):
        """ Verify that it is indeed a SRPM package. """
        return False 
        
    def unpack(self):
        """ Unpack the SRPM package. """
        pass
        
    def build(self,prefix=None):
        """ Build the SRPM package. """
        pass
        
    def install(self):
        """ Installs the artefacts created during build. """
        pass


        