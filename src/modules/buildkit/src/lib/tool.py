#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import pwd
import subprocess
from kusu.buildkit.kitsource import KitSrcFactory, KusuKit, KusuComponent
from kusu.buildkit.builder import PackageProfile, setupRPMMacrofile, getBuildKitTemplate
from kusu.buildkit.methods import *
from path import path
from kusu.util.errors import  FileDoesNotExistError, KitDefinitionEmpty
from kusu.util.tools import mkdtemp, cpio_copytree
from Cheetah.Template import Template


class BuildKit:
    """This is a convenience class for the buildkit app as well as other external apps or libs to use.
    """
    
    verbose = False
    
    def newKitSrc(self, srcpath):
        """prepare the Kit source directory"""
        srcpath = path(srcpath)
        newkit = KitSrcFactory(srcpath)
        newkit.prepareSrcPath()
        
        # also create a sample build.kit
        defaultname = srcpath.basename()
        s = self.prepareBuildKitTemplate(defaultname)
        f = open('%s/build.kit' % srcpath,'w')
        f.write(s)
        f.close()
        
        
    def getKitSrc(self, srcpath):
        """ Builds the kit based on the kitsrc dir"""
        return KitSrcFactory(srcpath)

    def getKitScript(self, kitsrc, kitscript='build.kit'):
        """ Sweeps the kitsrc dir and attempts to locate the kitscript.
        """
        _kitsrc = path(kitsrc)
        li = _kitsrc.files(kitscript)
        if not li: raise FileDoesNotExistError, kitscript
        
        # TODO : only handle single kitscript
        return li[0]

    def getBuildProfile(self, kitsrc):
        """ Returns the buildprofile based on kitsrc. """
        return setupprofile(kitsrc)
        
    def loadKitScript(self, kitscript):
        """ Loads the kitscript and get a tuple of the kit, components and packages defined in
            that kitscript.
        """
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
        
    def handlePackages(self, packages, buildprofile):
        """ Handles the configuring, building and deploying of the packages. """
        for p in packages:
            p.verbose = self.verbose
            p.buildprofile = buildprofile
            p.setup()
            p.verify()
            p._processAddScripts()
            p.configure()
            p.build()
            p.deploy()
            
    def handleComponents(self, components, buildprofile):
        """ Handles the configuring, building and deploying of the components. """
        for c in components:
            c.buildprofile = buildprofile
            c.setup()
            c._processAddScripts()
            c.deploy(verbose=self.verbose)
            
    def handleKit(self, kit, buildprofile):
        """ Handles the configuring, building and deploying of the kit. """
        kit.buildprofile = buildprofile
        kit.setup()
        kit._processAddScripts()
        kit.deploy(verbose=self.verbose)
        
    def populatePackagesDir(self, buildprofile):
        """ Populates the built or binary packages into the package directory. """
        populatePackagesDir(buildprofile)
        
    def setupRPMMacros(self, buildprofile):
        """ Sets up a proper .rpmmacros file for building purposes. """
        curRPMMacros = setupRPMMacrofile(buildprofile)
        
    def restoreRPMMacros(self, oldrpmmacros):
        """ Restores the old .rpmmacros. """
        userhome = path(pwd.getpwuid(os.getuid())[5])
        rpmmacros = userhome / '.rpmmacros'
        if rpmmacros.exists():
            rpmmacros.remove()
        cmd = 'mv -f %s %s' % (oldrpmmacros,rpmmacros)
        renP = subprocess.Popen(cmd,shell=True)
        renP.wait()
        
    def generateKitInfo(self, kit, filepath):
        """ Generates the kitinfo which contains the metadata information 
            regarding the kit and its components.
        """
        kit.generateKitInfo(filepath)
        
    def prepareBuildKitTemplate(self, defaultname):
        """ Gets the build.kit template and populate it with the correct 
            namespace. The defaultname is just a string to set the default
            component and kit names.
        """
        tmpl = getBuildKitTemplate()
        ns = {}

        # get this system's distro and version
        dist = os.environ.get('KUSU_DIST','')
        distver = os.environ.get('KUSU_DISTVER','')
        if dist == 'fedora' and distver == '6':
            compclass = 'Fedora6Component()'
            compdesc = '%s component for Fedora Core 6.' % defaultname
        elif dist == 'centos' and distver == '5':
            compclass = 'Centos5Component()'
            compdesc = '%s component for CentOS 5.' % defaultname
        elif dist == 'rhel' and distver == '5':
            compclass = 'RHEL5Component()'
            compdesc = '%s component for RHEL5.' % defaultname
        else:
            compclass = 'DefaultComponent()'
            compdesc = '%s component.' % defaultname

        ns['compclass'] = compclass
        ns['compname'] = defaultname
        ns['kitclass'] = 'DefaultKit()'
        ns['kitname'] = defaultname
        ns['kitdesc'] = '%s kit.' % defaultname
        ns['compdesc'] = compdesc
        t = Template(file=str(tmpl),searchList=[ns])
        return str(t)

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
        kitinfo.copy(kitnamedir)
        
        
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

        isofile = 'kit-%(name)s-%(version)s-%(release)s-%(arch)s.iso' % kit
        cmd = 'mkisofs -quiet -V "%s" -r -T -f -o %s/%s .' % (kit['name'],kitsrc,isofile)
        mkP = subprocess.Popen(cmd,shell=True,cwd=isodir)
        mkP.wait()
        isodir.rmtree()
        isopath = kitsrc / isofile
        return isopath
