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




class KusuComponent(object):
    """ Component for Kits. """

    dependencies = []
    scripts = []
    ngtypes = []
    
    def __init__(self,**kwargs):
        self.dependencies = kwargs.get('dependencies',[])
        self.scripts = kwargs.get('scripts',[])
        self.ngtypes = kwargs.get('ngtypes',[])
    
    def associateWith(self, ngtype):
        """ Add ngtype for this component to belong to. """
        if ngtype not in NODEGROUP_TYPES: raise UnsupportedNGType
        if ngtype not in self.ngtypes: self.ngtypes.append(ngtype)
        
    def addDep(self, package):
        """ Add package as a dependency. """
        if package not in self.dependencies:
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
        
    def pack(self, pkgtype='rpm'):
        """ Packaging stage. This is what the user would call. """
        
        if pkgtype == 'rpm':
            return self._packRPM()
            
class KusuKit(object):
    """ Kit class. """
    
    dependencies = []
    scripts = []
    components = []

    def addComponent(self, component):
        """ Add component to this kit. """
        if not component in self.components:
            self.components.append(component)

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

    def pack(self, pkgtype='rpm'):
        """ Packaging stage. This is what the user would call. """

        if pkgtype == 'rpm':
            return self._packRPM()


            
