#!/usr/bin/env python
# $Id$
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
from kusu.buildkit.strategies.kitsource01 import KitSrcFactory, GeneralKitSrc, KitSrcBase, BinaryKitSrc
from kusu.buildkit.strategies.kitsource01 import KusuComponent as KusuComponent01
from kusu.buildkit.strategies.kitsource01 import KusuKit as KusuKit01

PACKAGE_SRC_TYPES = ['autotools','srpm','binarydist','distro','rpm']
NODEGROUP_TYPES = ['installer','compute']


class KusuComponent(KusuComponent01):
    """ Component for Kits. """

    def __init__(self, **kwargs):
        super(KusuComponent, self).__init__(**kwargs)
        self.os = []
        self.follows = ''


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

        if 'filenames' in d:
            d['filenames'].append([])

        return d


class KusuKit(KusuKit01):
    """ Kit class. """

    def __init__(self, **kwargs):
        super(KusuKit, self).__init__(**kwargs)
        self.api = '0.4'
        self.conflicts = []
        self.filenames = []
        self.oldest_upgradeable_version = ''
        self.oldest_upgradeable_release = ''

    def _addScript(self, script, mode='post'):

        if not mode in ['post','pre','postun','preun']: raise UnsupportedScriptMode, mode
        if type(script) == str: script = [script]

        scriptfiles = []
        for s in script:
            scriptfile = self.srcdir / s
            if not scriptfile.exists(): raise FileDoesNotExistError, scriptfile
            scriptfiles.append(scriptfile)

        key = '%sscript' % mode
        self.scripts[key] = scriptfiles

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

    def _prepScripts(self, ns):
        """
        Sets up the pre- and post-[un]install scripts.
        """

        _root = '%s-%s-buildroot' % (ns['pkgname'],ns['pkgversion'])
        buildroot = self.tmpdir / _root
        scriptroot = '/scripts'
        destdir = buildroot / scriptroot[1:]
        if not destdir.exists(): destdir.makedirs()

        scripts = []
        for mode, script in self.scripts.iteritems():
            script_prefix = 0
            if script:
                if type(script) == str: script = [script]
                for s in script:
                    script_file = path(destdir / '%03d-%s%s' % (script_prefix, mode, path(s).ext))
                    path(self.srcdir / s).copy(script_file)
                    scripts.append(scriptroot + '/%s' % script_file.basename())
                    script_prefix += 1

        return scripts

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

        if not hasattr(self.buildprofile, 'filenames'):
            self.buildprofile.filenames = []

        self.generateKitInfo(kifile, self.buildprofile)
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

    def _packRPM(self, verbose=False):
        """ RPM packaging stage for this class. """

        ns = self._generateNS()
        tmpl = getTemplateSpec('kit')
        builddir = path(self.buildprofile.builddir)
        _s = '%s.spec' % ns['pkgname']
        fl = []
        fl.extend(self._prepDocumentation(ns))
        fl.extend(self._prepPlugins(ns))
        fl.extend(self._prepScripts(ns))
        fl.extend(self._prepKitInfo(ns))
        ns['filelist'] = fl
        specfile = builddir / _s
        rpmbuilder =  RPMBuilder(ns=ns,template=tmpl,sourcefile=specfile,verbose=verbose)
        return rpmbuilder.build()

    def generateKitInfo(self, filename, buildprofile=None):
        """ Generates a kitinfo file."""
        complist = [component.generate() for component in self.components]

        _kitinfo  = self.generate()
        if buildprofile:
            _kitinfo['filenames'] = buildprofile.filenames
        f = open(filename,'w')
        f.write('kit = %s\n' % pprint.pformat(_kitinfo))
        f.write('components = %s\n' % pprint.pformat(complist))
        f.close()
