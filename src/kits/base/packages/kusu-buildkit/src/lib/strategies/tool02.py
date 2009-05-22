#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import pwd
import subprocess
from kusu.buildkit.strategies.kitsource02 import KitSrcFactory, KusuKit, KusuComponent
from kusu.buildkit.builder import PackageProfile, setupRPMMacrofile, getBuildKitTemplate, getScriptTemplate
from kusu.buildkit.methods import *
from path import path
from kusu.util.errors import  FileDoesNotExistError, KitDefinitionEmpty, PackageBuildError
from kusu.util.tools import mkdtemp, cpio_copytree, getArch
from kusu.util.kits import processKitInfo
from Cheetah.Template import Template
import tool01

class BuildKit(tool01.BuildKit):
    """This is a convenience class for the buildkit app as well as other external apps or libs to use.
    """

    def __init__(self):
        super(BuildKit, self).__init__()
        import kusu.buildkit.methods as methods
        methods.KIT_API = '0.2'

    def newKitSrc(self, srcpath, arch=None):
        """prepare the Kit source directory"""
        srcpath = path(srcpath)
        newkit = KitSrcFactory(srcpath)
        newkit.prepareSrcPath()

        # also create a sample build.kit
        defaultname = srcpath.basename()
        s = self.prepareBuildKitTemplate(defaultname, arch)
        f = open('%s/build.kit' % srcpath,'w')
        f.write(s)
        f.close()

    def prepareBuildKitTemplate(self, defaultname, arch=None, tmplname='build.kit.v02.tmpl'):
        """ Gets the build.kit template and populate it with the correct
            namespace. The defaultname is just a string to set the default
            component and kit names.
        """
        t = super(BuildKit, self).prepareBuildKitTemplate(defaultname,
                                                          arch, tmplname)
        return t

    def loadKitScript(self, kitscript):
        """ Loads the kitscript and get a tuple of the kit, components and packages defined in
            that kitscript.
        """
        import kusu.buildkit.methods as methods
        methods.KIT_API = '0.2'
        d = dict(methods.__dict__)
        hidden_keys = [s for s in d.keys() if s.startswith('_')]
        for k in hidden_keys:
            d.pop(k)
        globals().update(d)

        ns = {}
        execfile(kitscript,globals(),ns)

        pkgs = [ns[key] for key in ns.keys() if isinstance(ns[key], PackageProfile)]
        comps = [ns[key] for key in ns.keys() if isinstance(ns[key], KusuComponent)]
        kits = [ns[key] for key in ns.keys() if isinstance(ns[key], KusuKit)]

        # FIXME: only a single kit is supported right now
        if not kits:
            kit = []
        else:
            kit = kits[0]

        return (kit,comps,pkgs)

    def handleComponents(self, components, buildprofile):
        """ Handles the configuring, building and deploying of the components. """
        for c in components:
            c.buildprofile = buildprofile
            c.setup()
            c._processAddScripts()
            exitcode = c.deploy(verbose=self.verbose)
            if exitcode != 0:
                raise PackageBuildError, c.name

    def handleKit(self, kit, buildprofile):
        """ Handles the configuring, building and deploying of the kit. """
        kit.buildprofile = buildprofile
        kit.setup()
        exitcode = kit.deploy(verbose=self.verbose)
        if exitcode != 0:
            raise PackageBuildError, kit.name

    def populatePackagesDir(self, buildprofile, arch):
        """ Populates the built or binary packages into the package directory. """
        populatePackagesDir(buildprofile, arch)

    def setupRPMMacros(self, buildprofile):
        """ Sets up a proper .rpmmacros file for building purposes. """
        return setupRPMMacrofile(buildprofile)

    def restoreRPMMacros(self, oldrpmmacros):
        """ Restores the old .rpmmacros. """
        userhome = path(pwd.getpwuid(os.getuid())[5])
        rpmmacros = userhome / '.rpmmacros'
        if rpmmacros.exists():
            rpmmacros.remove()
        cmd = 'mv -f %s %s' % (oldrpmmacros,rpmmacros)
        renP = subprocess.Popen(cmd,shell=True)
        renP.wait()

    def generateKitInfo(self, kit, filepath, buildprofile=None):
        """ Generates the kitinfo which contains the metadata information
            regarding the kit and its components.
        """
        kit.generateKitInfo(filepath, buildprofile=None)

    def stripOutSVN(self, dirpath):
        """ Removes .svn assets from the dirpath.
        """
        dirpath = path(dirpath)
        svnlist = [f for f in dirpath.walk('.svn')]
        for l in svnlist:
            l.rmtree()

    def stripOutDebugInfo(self, dirpath):
        """ Removes any debuginfo packages
        """
        dirpath = path(dirpath)
        dblist = [f for f in dirpath.walkfiles('*-debuginfo-*rpm')]
        for db in dblist:
            db.remove()

    def makeKitDir(self, kitsrc, kitdir):
        """ Creates a Kusu Kit Directory based on the Kit Source dir.
        """
        kitsrc = path(kitsrc).abspath()
        kitdir = path(kitdir).abspath()
        if not kitdir.exists(): kitdir.mkdir()
        pkgdir = path(kitsrc / 'packages')

        # sweep and get the kitinfo files
        li = kitsrc.files('kitinfo')
        kitinfo = path(li[0])

        kit,comps = processKitInfo(kitinfo)

        if not kit:
            raise KitDefinitionEmpty

        # TODO : right now, we don't make use of the kitversion, only kitnames
        # TODO : also, only a single kit is supported right now

        kitnamedir = path(kitdir / kit['name'])
        if kitnamedir.exists(): kitnamedir.rmtree()
        kitnamedir.mkdir()
        cpio_copytree(pkgdir,kitnamedir)
        self.stripOutSVN(kitnamedir)
        if not self.debuginfo: self.stripOutDebugInfo(kitnamedir)


    def makeKitISO(self, kitsrc):
        """ Creates a Kusu Kit ISO based on the kitsrc dir.
            Returns the isofile.
        """
        tmpdir = kitsrc / 'tmp'
        isodir = mkdtemp(dir=tmpdir,prefix='isodir-')
        self.makeKitDir(kitsrc,isodir)
        # sweep and get the kitinfo files
        li = kitsrc.files('kitinfo')
        kitinfo = path(li[0])

        kit,comps = processKitInfo(kitinfo)

        if not kit:
            if isodir.exists(): isodir.rmtree
            raise KitDefinitionEmpty

        isofile = 'kit-%(name)s-%(version)s-%(release)s.%(arch)s.iso' % kit
        cmd = 'mkisofs -quiet -V "%s" -r -T -f -o %s/%s .' % (kit['name'],kitsrc,isofile)
        mkP = subprocess.Popen(cmd,shell=True,cwd=isodir)
        mkP.wait()
        isodir.rmtree()
        isopath = kitsrc / isofile
        return isopath
