#!/usr/bin/env python
# $Id: kitsource.py 4056 2009-01-16 02:16:38Z ggoh $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from path import path
from kusu.util.errors import KitSrcAlreadyExists, UnsupportedNGType, UnsupportedScriptMode, FileDoesNotExistError
from kusu.util.structure import Struct
from kusu.util.tools import cpio_copytree
from kusu.util.rpmtool import RPM
from kusu.buildkit.builder import RPMBuilder, getTemplateSpec, stripShebang
import pprint
from kusu.buildkit.strategies.kitsource01 import KitSrcBase as KitSrcBase01
from kusu.buildkit.strategies.kitsource01 import GeneralKitSrc as GeneralKitSrc01
from kusu.buildkit.strategies.kitsource01 import KusuComponent as KusuComponent01
from kusu.buildkit.strategies.kitsource01 import KusuKit as KusuKit01

PACKAGE_SRC_TYPES = ['autotools','srpm','binarydist','distro','rpm']
NODEGROUP_TYPES = ['installer','compute']


def KitSrcFactory(srcPath):
    """ Factory function that returns a KitSrcBase instance. """
    # right now, we only return GeneralKitSrc
    return GeneralKitSrc(srcPath)

class KitSrcBase(KitSrcBase01):
    def __init__(self):
        super(KitSrcBase,self).__init__()
       
class GeneralKitSrc(GeneralKitSrc01):
    def __init__(self, srcPath):
        super(GeneralKitSrc,self).__init__(srcPath)
        
class BinaryKitSrc(KitSrcBase): pass


class KusuComponent(KusuComponent01):
    """ Component for Kits. """
    
    def __init__(self, **kwargs):
        super(KusuComponent, self).__init__(**kwargs)
        self.os = []

       
    def verify(self):
        # FIXME: needs to be fill out
        pass
        
    def _processAddScripts(self):
        """ Process any queued commands.
        """
        for cmd in self._queuecmds:
            if len(cmd) > 1:
                func = cmd[0]
                args = cmd[1:]
            else:
                func = cmd[0]
                args = []

            func(*args)
        
    def associateWith(self, ngtype):
        """ Add ngtype for this component to belong to. """
        if ngtype not in NODEGROUP_TYPES: raise UnsupportedNGType
        if ngtype not in self.ngtypes: self.ngtypes.append(ngtype)
        
    def generate(self):
        """ Returns a metadata dict. """
        d = super(KusuComponent, self).generate()

        if 'ostype' in d: del d['ostype']
        if 'osversion' in d: del d['osversion']
        if 'osmajor' in d: del d['osmajor']
        if 'osminor' in d: del d['osminor']
       
        if self.osminor: 
            osminor = self.osminor
        else:
            osminor = '*'

        d['os'] = [ {'name': self.ostype, 'major': self.osmajor, 'minor': osminor, 'arch': self.arch } ]
 
        return d


class KusuKit(KusuKit01):
    """ Kit class. """

    def __init__(self, **kwargs):
        super(KusuKit, self).__init__(**kwargs)
        self.api = '0.2'
        self.conflicts = []
        self.filenames = []

    def setup(self):
        """ Prepares the attributes for this class. This method have to be called before any
            other operation.
        """
        self.builddir = path(self.buildprofile.builddir)
        self.srcdir = path(self.buildprofile.srcdir)
        self.pkgdir = path(self.buildprofile.pkgdir)
        self.tmpdir = path(self.buildprofile.tmpdir)
        self.templatesdir = path(self.buildprofile.templatesdir)
        self.docsdir = path(self.buildprofile.docsdir)
        self.pluginsdir = path(self.buildprofile.pluginsdir)

    def verify(self):
        # FIXME: needs to be fill out
        pass

    def _processAddScripts(self):
        # Not used
        pass

    def addScript(self, script, mode='post'):
        # Not used
        pass

    def generate(self):
        """ Returns a metadata for this kit. """
        d = super(KusuKit, self).generate()
        if 'scripts' in d: del d['scripts']
        return d

    def _prepDocumentation(self, ns):
        """ Sets up the kit documentation.
            Returns the list of files.
        """
        srcdir = self.docsdir
        _filelist = srcdir.files()
        if not _filelist: return []
        _root = '%s-%s-buildroot' % (ns['pkgname'],ns['pkgversion'])
        buildroot = self.tmpdir / _root
        if not buildroot.exists(): buildroot.makedirs()
        docsdir = '/www'
        docsdir = path(docsdir)
        destdir = buildroot / str(docsdir)[1:]
        if not destdir.exists(): destdir.makedirs()
        cpio_copytree(srcdir,destdir)
        filelist = []
        for f in destdir.files():
            filelist.append(str(path(docsdir / f.basename())))
            
        return filelist

    def _prepPlugins(self, ns):
        """ Sets up the kit plugins.
            Returns the list of files.
        """
        srcdir = self.pluginsdir
        _filelist = []
        ngeditPlugins = srcdir / 'ngedit'
        addhostPlugins = srcdir / 'addhost'
        genconfigPlugins = srcdir / 'genconfig'
        _filelist = ngeditPlugins.files() + addhostPlugins.files() + \
            genconfigPlugins.files()
        if not _filelist: return []
        
        _root = '%s-%s-buildroot' % (ns['pkgname'],ns['pkgversion'])
        buildroot = self.tmpdir / _root
        if not buildroot.exists: buildroot.makedirs()
        plugdir = path('/')
        destdir = buildroot / str(plugdir)[1:]
        if not destdir.exists(): destdir.makedirs()
        cpio_copytree(srcdir,destdir)
        fl = [f.split(str(srcdir) + '/')[1] for f in _filelist]
        filelist = []
        for f in fl:
            filelist.append(str(path(plugdir / f)))
        return filelist
        
    def _prepKitInfo(self,ns):
        """ Sets up the kitinfo
            Returns the path for kitinfo
        """
        _root = '%s-%s-buildroot' % (ns['pkgname'],ns['pkgversion'])
        buildroot = self.tmpdir / _root
        kiroot = '/'
        destdir = buildroot / kiroot[1:]
        if not destdir.exists(): destdir.makedirs()
        kifile = path(destdir / 'kitinfo')
        self.generateKitInfo(kifile)
        _kitfile = kiroot + '/kitinfo'
        return [_kitfile]

    def _generateNS(self):
        """ Generates the namespace needed for the pack operation.
        """
        _ns = {}
        # also create a pkgname for this kit
        self.pkgname = 'kit-%s' % self.name
        _ns['pkgname'] = self.pkgname
        _ns['name'] = self.name

        if self.arch == 'x86':
            _ns['arch'] = 'i386'
        else:
            _ns['arch'] = self.arch

        _ns['pkgversion'] = self.version
        _ns['pkgrelease'] = self.release       
        _ns['license'] = self.license
        _ns['description'] = self.description
        
        return _ns
