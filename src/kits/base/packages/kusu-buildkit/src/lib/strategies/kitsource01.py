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
            for _k,_v in v.items():
                p = self.srcPath / _v
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
                    if k == 'pluginsdir':
                        pdir = path(self.srcPath / v['dir'])
                        pdir.mkdir()
                        path(pdir / 'addhost').mkdir()
                        path(pdir / 'ngedit').mkdir()
                        path(pdir / 'genconfig').mkdir()
                    else:
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
            'pluginsdir' : {'dir':'plugins'},
            'docsdir' : {'dir':'docs'},
            'tmpdir' : {'dir':'tmp'}
        }

class BinaryKitSrc(KitSrcBase): pass


class KusuComponent(Struct):
    """ Component for Kits. """


    def __init__(self, **kwargs):
        self.dependencies = []                   # list of dependencies for this component
        self.ngtypes = ['installer','compute']   # list of nodegroup types for this component
        self.driverpacks = []                    # list of driverpacks for this kit
        self.arch = 'noarch'
        self.compversion = '0.1'
        self.comprelease = '0'
        Struct.__init__(self,kwargs)
        self._queuecmds = []

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

        self.scripts = {}
        self.scripts['postscript'] = ''
        self.scripts['postunscript'] = ''
        self.scripts['preunscript'] = ''
        self.scripts['prescript'] = ''

        for package, absver in self.dependencies:
            # also add to driverpacks list if this package is a driverpack type
            if package.driverpack:
                # create a small driverpack dict since we only want specific data
                dpack = {}
                dpack['name'] = package.filename
                p = path(self.srcdir / package.filename)
                rpm = RPM(str(p))
                dpack['description'] = rpm.description
                if dpack not in self.driverpacks: self.driverpacks.append(dpack)

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
        d = self.copy()
        # we don't want to return everything
        if 'buildprofile' in d: del d['buildprofile']
        if 'builddir' in d: del d['builddir']
        if 'pkgdir' in d: del d['pkgdir']
        if 'srcdir' in d: del d['srcdir']
        if 'templatesdir' in d: del d['templatesdir']
        if 'tmpdir' in d: del d['tmpdir']
        if '_queuecmds' in d: del d['_queuecmds']
        if 'docsdir' in d: del d['docsdir']
        if 'pluginsdir' in d: del d['pluginsdir']
        del d['dependencies']

        return d

    def addDep(self, package, absoluteversion=False):
        """ Add package as a dependency. If absoluteversion is set to True,
            the package version have to be exact.
            '=' instead of just '>='.
        """
        if package not in self.dependencies:
            self.dependencies.append((package,absoluteversion))


    def addScript(self, script, mode='post'):
        """ Add script for this component. Available modes are
            post, pre, postun and preun.
        """
        self._queuecmds.append((self._addScript,script,mode))

    def _addScript(self, script, mode='post'):

        if not mode in ['post','pre','postun','preun']: raise UnsupportedScriptMode, mode
        scriptfile = self.srcdir / script
        if not scriptfile.exists(): raise FileDoesNotExistError, scriptfile
        key = '%sscript' % mode
        self.scripts[key] = stripShebang(scriptfile)

    def _generateNS(self):
        """ Generates the namespace needed for the pack operation.
        """
        _ns = {}
        # also create a pkgname for this kit
        self.pkgname = 'component-%s' % self.name
        _ns['pkgname'] = self.pkgname
        _ns['pkgversion'] = self.compversion
        _ns['pkgrelease'] = self.comprelease
        _ns['name'] = self.name
        _ns['arch'] = self.arch
        _ns['dependencies'] = self.dependencies
        _ns['description'] = self.description
        _ns['prescript'] = self.scripts['prescript']
        _ns['preunscript'] = self.scripts['preunscript']
        _ns['postscript'] = self.scripts['postscript']
        _ns['postunscript'] = self.scripts['postunscript']

        return _ns

    def _packRPM(self, verbose=False):
        """ RPM packaging stage for this class. """

        ns = self._generateNS()

        tmpl = getTemplateSpec('component')
        builddir = path(self.builddir)
        _s = '%s.spec' % ns['pkgname']
        specfile = builddir / _s
        rpmbuilder =  RPMBuilder(ns=ns,template=tmpl,sourcefile=specfile,verbose=verbose)
        return rpmbuilder.build()

    def deploy(self, pkgtype='rpm', verbose=False):
        """ Deploying stage. This is what the user would call. """

        if pkgtype == 'rpm':
            return self._packRPM(verbose)

class KusuKit(Struct):
    """ Kit class. """

    def __init__(self, **kwargs):
        self.components = []     # list of components belonging to this kit
        self.dependencies = []   # list of dependencies for this kit
        self.license = 'LGPL'    # license for this kit
        self.version = '0.1'
        self.release = '0'
        self.arch = 'noarch'
        Struct.__init__(self,kwargs)
        self._queuecmds = []

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

        self.scripts = {}
        self.scripts['postscript'] = ''
        self.scripts['postunscript'] = ''
        self.scripts['preunscript'] = ''
        self.scripts['prescript'] = ''

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

    def addScript(self, script, mode='post'):
        """ Add script for this component. Available modes are
            post, pre, postun and preun.
        """
        self._queuecmds.append((self._addScript,script,mode))

    def _addScript(self, script, mode='post'):

        if not mode in ['post','pre','postun','preun']: raise UnsupportedScriptMode, mode
        scriptfile = self.srcdir / script
        if not scriptfile.exists(): raise FileDoesNotExistError, scriptfile
        key = '%sscript' % mode
        self.scripts[key] = stripShebang(scriptfile)


    def generate(self):
        """ Returns a metadata for this kit. """
        d = self.copy()
        if 'removeable' in d:
            d['removable'] = d['removeable']
            del d['removeable']
        # we don't want to return everything
        if 'buildprofile' in d: del d['buildprofile']
        if 'builddir' in d: del d['builddir']
        if 'pkgdir' in d: del d['pkgdir']
        if 'srcdir' in d: del d['srcdir']
        if 'templatesdir' in d: del d['templatesdir']
        if 'tmpdir' in d: del d['tmpdir']
        if 'docsdir' in d: del d['docsdir']
        if 'pluginsdir' in d: del d['pluginsdir']
        del d['components']
        if '_queuecmds' in d: del d['_queuecmds']

        if self.arch == 'x86':
            d['arch'] = 'i386'
        else:
            d['arch'] = self.arch

        return d

    def addComponent(self, component):
        """ Add component to this kit. """
        if not component in self.components:
            self.components.append(component)

    addComp = addComponent

    def addDep(self, package):
        """ Add package as a dependency. """
        if not package in self.dependencies:
            self.dependencies.append(package)

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
        docsdir = '/depot/www/kits/%s/%s' % (ns['name'], ns['pkgversion'])
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
        plugdir = path('/opt/kusu/lib/plugins')
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
        kiroot = '/depot/kits/%s/%s/%s' % (ns['name'],ns['pkgversion'],ns['arch'])
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
        _ns['prescript'] = self.scripts['prescript']
        _ns['preunscript'] = self.scripts['preunscript']
        _ns['postscript'] = self.scripts['postscript']
        _ns['postunscript'] = self.scripts['postunscript']


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
        fl.extend(self._prepKitInfo(ns))
        ns['filelist'] = fl
        specfile = builddir / _s
        rpmbuilder =  RPMBuilder(ns=ns,template=tmpl,sourcefile=specfile,verbose=verbose)
        return rpmbuilder.build()

    def generateKitInfo(self, filename, buildprofile=None):
        """ Generates a .kitinfo file."""
        complist = [component.generate() for component in self.components]

        _kitinfo  = self.generate()
        f = open(filename,'w')
        f.write('kit = %s\n' % pprint.pformat(_kitinfo))
        f.write('components = %s\n' % pprint.pformat(complist))
        f.close()

    def deploy(self, pkgtype='rpm', verbose=False):
        """ Deploying stage. This is what the user would call. """

        if pkgtype == 'rpm':
            return self._packRPM(verbose)
