#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from path import path
from kusu.util.errors import KitSrcAlreadyExists, UnsupportedNGType


PACKAGE_SRC_TYPES = ['autotools','srpm','binarydist','distro','rpm']
NODEGROUP_TYPES = ['installer','compute']


def KitSrcFactory(srcPath):
    """ Factory function that returns a KitSrcBase instance. """
    # right now, we only return GeneralKitSrc
    return GeneralKitSrc(srcPath)


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
            if 'file' in v.keys():
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
            'artifactsdir' : {'dir':'artifacts'},
            'binpkgsdir' : {'dir':'packages'},
            'srcpkgsdir' : {'dir':'sources'},
            'tmpdir' : {'dir':'tmp'},
            'kitinfo' : {'file':'kitinfo'}
        }
        
class BinaryKitSrc(KitSrcBase): pass

class KitInfo(object):
    """ This class contains the metadata information regarding the kit. """
    author = ''
    name = ''
    vendor = ''
    license = ''
    arch = 'noarch'
    version = '0.1'
    release = '0'

    def __init__(self, **kwargs):
        self.author = kwargs.get('author','')
        self.name = kwargs.get('name','')
        self.vendor = kwargs.get('vendor','')
        self.license = kwargs.get('license','')
        self.arch = kwargs.get('arch','noarch')
        self.version = kwargs.get('version','0.1')
        self.release = kwargs.get('release','0')
        
    def generate(self):
        """ Returns a metadata tuple containing the kitinfo and individual compinfos. """
        
        d = {}
        d['name'] = self.name
        d['license'] = self.license
        d['vendor'] = self.vendor
        d['author'] = self.author
        d['arch'] = self.arch
        d['version'] = self.version
        d['release'] = self.release
        
        return d
        

class ComponentInfo(object):
    """ This class contains the metadata information regarding the component.
    """

    ngtypes = []
    name = ''
    ostype = ''
    osversion = ''
    compversion = '0.1'
    comprelease = '0'
    
    def __init__(self,**kwargs):
        self.name = kwargs.get('name','')
        self.ostype = kwargs.get('ostype','')
        self.osversion = kwargs.get('osversion','')
        self.ngtypes = kwargs.get('ngtypes',[])
        self.compversion = kwargs.get('compversion','0.1')
        self.comprelease = kwargs.get('comprelease','0')
    
    def associateWith(self, ngtype):
        """ Add ngtype for this component to belong to. """
        if ngtype not in NODEGROUP_TYPES: raise UnsupportedNGType
        if ngtype not in self.ngtypes: self.ngtypes.append(ngtype)
        
    def generate(self):
        """ Returns a metadata dict. """
        d = {}
        d['ngtypes'] = self.ngtypes
        d['name'] = self.name
        d['ostype'] = self.ostype
        d['osversion'] = self.osversion
        d['compversion'] = self.compversion
        d['comprelease'] = self.comprelease
        
        return d

class KusuComponent(object):
    """ Component for Kits. """

    dependencies = []
    scripts = []
    componentinfo = None
    
    def __init__(self,**kwargs):
        self.dependencies = kwargs.get('dependencies',[])
        self.scripts = kwargs.get('scripts',[])
        self.componentinfo = kwargs.get('componentinfo',None)
    
    def associateWith(self, ngtype):
        """ Add ngtype for this component to belong to. """
        self.componentinfo.associateWith(ngtype)
        
    def addDep(self, package, absoluteversion=False):
        """ Add package as a dependency. If absoluteversion is set to True, 
            the package version have to be exact. 
            '=' instead of just '>='.
        """
        if package not in self.dependencies:
            self.dependencies.append((package,absoluteversion))

    def addScripts(self, script, mode='post'):
        """ Add script for this component. Available modes are
            post, pre, postun and preun. 
        """
        if not script in self.scripts:
            self.scripts.append((script,mode))
            
    def _packRPM(self):
        """ RPM packaging stage for this class. """
        pass
        
    def pack(self, pkgtype='rpm'):
        """ Packaging stage. This is what the user would call. """
        
        if pkgtype == 'rpm':
            return self._packRPM()
            
class KusuKit(object):
    """ Kit class. """
    
    dependencies = []
    scripts = []
    components = []
    kitinfo = None
    
    def __init__(self, kitinfo):
        self.kitinfo = kitinfo

    def addComponent(self, component):
        """ Add component to this kit. """
        if not component in self.components:
            self.components.append(component)
            
    addComp = addComponent

    def addDep(self, package):
        """ Add package as a dependency. """
        if not package in self.dependencies:
            self.dependencies.append(package)

    def addScripts(self, script, mode='post'):
        """ Add script for this component. Available modes are
            post, pre, postun and preun. 
        """
        if not script in self.scripts:
            self.scripts.append((script,mode))

    def _packRPM(self):
        """ RPM packaging stage for this class. """
        pass

    def generateKitInfo(self, filename):
        """ Generates a .kitinfo file."""
        li = [component.componentinfo.generate() for component in self.components]
        compsinfo = {}
        for l in li:
            compsinfo.update(l)

        _kitinfo  = self.kitinfo.generate()
        f = open(filename,'w')
        f.write('kit = %r\n' % _kitinfo)
        f.write('components = %r\n' % compsinfo)
        f.close()
        
    def pack(self, pkgtype='rpm'):
        """ Packaging stage. This is what the user would call. """

        if pkgtype == 'rpm':
            return self._packRPM()


            
