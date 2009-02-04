#!/usr/bin/env python
# $Id$
#
# Copyright 2009 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
import pwd
import atexit
from path import path
from kusu.core.app import KusuApp
from kusu.util.tools import getArch
from kusu.util.errors import BuildkitArchError, InvalidBuildProfile, PackageBuildError
from kusu.buildkit import getSyntaxValidator
from kusu.buildkit.tool01 import BuildKit as BuildKit01
from kusu.buildkit.tool02 import BuildKit as BuildKit02

# i18n - grab from KusuApp.
_ = KusuApp()._

def printMsgExit(msg, exitcode=1):
    print msg
    sys.exit(exitcode)


def restoreRpmMacros(oldrpmmacros):
    """ Restore the old .rpmmacros
    """
    rpmmacros = oldrpmmacros.splitext()[0]
    if oldrpmmacros.exists():
        if rpmmacros.exists(): rpmmacros.remove()
        oldrpmmacros.rename(rpmmacros)
        msg = _('Original .rpmmacros restored.')
        print msg


def removeRpmMacros():
    userhome = path(pwd.getpwuid(os.getuid())[5])
    rpmmacros = userhome / '.rpmmacros'
    if rpmmacros.exists(): rpmmacros.remove()


def makeKitv01(args, options):
    """ Make a kit according to API v 0.1 spec. """
    print 'v0.1'

    # instantiate version 0.1 of Buildkit api.
    bkinst = BuildKit01()

    kitsrc = path(args['kit']).abspath()
    _kitdir = args.get('dir','')

    if not _kitdir:
        makeiso = True
    else:
        kitdir = path(_kitdir).abspath()
        makeiso = False

    # get the kitsrc
    msg = _('Verifying the Kit Source directory found in %(kitsrc)s..' % {'kitsrc':kitsrc})
    print msg
    _kitsrc = bkinst.getKitSrc(kitsrc)

    if not _kitsrc.verifySrcPath():
        msg = _('Unable to use %(kitsrc)s as a Kit Source directory!' % {'kitsrc':kitsrc})
        printMsgExit(msg)

    bp = None
    try:
        msg = _('Setting up BuildProfile for this kit..')
        print msg
        bp = bkinst.getBuildProfile(kitsrc)
    except InvalidBuildProfile:
        msg = _('Unable to create a BuildProfile based on this Kit Source directory!')
        printMsgExit(msg)

    if not bp.builddir or not bp.pkgdir or not bp.srcdir or not bp.tmpdir:
        msg = _('Unable to create a BuildProfile based on this Kit Source directory!')
        self.printMsgExit(msg)

    # set up the .rpmmacros
    msg = _('Setting up a proper .rpmmacros for building this kit')
    print msg
    rpmmacrosExist, oldrpmmacros = bkinst.setupRPMMacros(bp)
    if rpmmacrosExist:
        atexit.register(restoreRpmMacros,oldrpmmacros)
    else:
        atexit.register(removeRpmMacros)

    # get the kitscript
    _ks = options.kitscript
    kitscript = ''
    try:
        msg = _('Looking for the kitscript %(kitscript)s..' % {'kitscript':_ks})
        print msg
        kitscript = bkinst.getKitScript(kitsrc,_ks)
    except FileDoesNotExistError:
        msg = _('kitscript %(kitscript)s not found!' % {'kitscript':_ks})
        printMsgExit(msg)

    # looks like everything is down pat, now the hard stuff
    msg = _('Found kitscript. Loading it..')
    print msg
    kit, components, packages = bkinst.loadKitScript(kitscript)

    # get the current arch
    curArch = getArch()
    arch = kit['arch']

    if arch != curArch and arch != 'noarch':
        msg = _('Creating kit for %(arch)s is not possible on this system. The allowed architectures are noarch and %(curArch)s.' \
                % {'arch':arch,'curArch':curArch})
        printMsgExit(msg)

    if arch != 'noarch':
        msg = _('Building kit for %(arch)s architecture..' % {'arch':arch})
    else:
        msg = _('Building kit for all architectures..' % {'arch':arch})
    print msg

    # validate the syntax
    # set up a counter
    c = 0
    missingAttributes = []
    # first the packages
    for pkg in packages:
        sv = getSyntaxValidator(pkg)
        if not sv.validate():
            for a in sv.getMissingAttributes():
                if not a in missingAttributes: missingAttributes.append(a)
            c += 1

    if c > 0:
        msg = _('There are missing attributes for the package(s): %(missinglist)r' %
                {'missinglist':missingAttributes})
        print msg
        msg = _('Please fix this and build again.')
        printMsgExit(msg)

    # set up a counter
    c = 0
    missingAttributes = []
    # second the comps
    for comp in components:
        sv = getSyntaxValidator(comp)
        if not sv.validate():
            for a in sv.getMissingAttributes():
                if not a in missingAttributes: missingAttributes.append(a)
            c += 1

    if c > 0:
        msg = _('There are missing attributes for the component(s): %(missinglist)r' %
                {'missinglist':missingAttributes})
        print msg
        msg = _('Please fix this and build again.')
        printMsgExit(msg)

    # set up a counter
    c = 0
    missingAttributes = []
    # lastly the kit
    sv = getSyntaxValidator(kit)
    if not sv.validate():
        for a in sv.getMissingAttributes():
            if not a in missingAttributes: missingAttributes.append(a)
        c += 1

    if c > 0:
        msg = _('There are missing attributes for the kit: %(missinglist)r' %
                {'missinglist':missingAttributes})
        print msg
        msg = _('Please fix this and build again.')
        printMsgExit(msg)

    # lets build the packages if any:
    if packages:
        try:
            msg = _('Building the package(s)..')
            print msg
            bkinst.handlePackages(packages,bp)
        except FileDoesNotExistError, e:
            msg = _('File %(filename)s not found! Please fix this and build again.' \
                    % {'filename':e})
            printMsgExit(msg)
        except PackageAttributeNotDefined, e:
            msg = _('Package attribute %(attribute)s is not defined! Please fix this and build again.' \
                % {'attribute':e})
            printMsgExit(msg)
        except PackageBuildError, e:
            msg = _('Error building package %(name)s! Please fix this and build again.' \
                    % {'name':e})
            printMsgExit(msg)

    if components:
        try:
            msg = _('Building the packages for component(s)..')
            bkinst.handleComponents(components,bp)
            print msg
        except PackageBuildError, e:
            msg = _('Error building component %(name)s! Please fix this and build again.' \
                    % {'name':e})
            printMsgExit(msg)
            
    if kit:
        try:
            msg = _('Building the package for the kit..')
            bkinst.handleKit(kit,bp)
            print msg
        except PackageBuildError, e:
            msg = _('Error building kit! Please fix this and build again.')
            printMsgExit(msg)
            
    # populate the packages dir
    msg = _('Populating the packages directory with the Kit artifacts..')
    print msg
    bkinst.populatePackagesDir(bp,arch)
        
    # generate the kitinfo file
    msg = _('Generating kitinfo..')
    print msg
    kitinfo = '%s/kitinfo' % kitsrc
    bkinst.generateKitInfo(kit,kitinfo)
        
    # finally, make the kit artifact
    if makeiso:
        msg = _('Creating the Kit iso..')
        print msg
        kitiso = bkinst.makeKitISO(kitsrc)
        
        if not kitiso:
            msg = _('Error creating Kit ISO!')
            printMsgExit(msg)
                
        msg = _('Kit ISO created.')
        print msg
        msg = _('ISO file is at %(isofile)s.' % {'isofile':kitiso})
        print msg
    else:
        msg = _('Creating the Kit dir..')
        print msg
        bkinst.makeKitDir(kitsrc,kitdir)
        msg = _('Kit directory created..')
        print msg
        msg = _('Kit directory is at %(kitdir)s.' % {'kitdir':kitdir})
        print msg


def makeKitv02(args, options):
    """ Make a skeleton for a kit conforming to API v0.2. """
    print 'v0.2'

    # instantiate version 0.2 of Buildkit api.
    bkinst = BuildKit02()

    kitsrc = path(args['kit']).abspath()
    _kitdir = args.get('dir','')

    if not _kitdir:
        makeiso = True
    else:
        kitdir = path(_kitdir).abspath()
        makeiso = False

    # get the kitsrc
    msg = _('Verifying the Kit Source directory found in %(kitsrc)s..' % {'kitsrc':kitsrc})
    print msg
    _kitsrc = bkinst.getKitSrc(kitsrc)

    if not _kitsrc.verifySrcPath():
        msg = _('Unable to use %(kitsrc)s as a Kit Source directory!' % {'kitsrc':kitsrc})
        printMsgExit(msg)

    bp = None
    try:
        msg = _('Setting up BuildProfile for this kit..')
        print msg
        bp = bkinst.getBuildProfile(kitsrc)
    except InvalidBuildProfile:
        msg = _('Unable to create a BuildProfile based on this Kit Source directory!')
        printMsgExit(msg)

    if not bp.builddir or not bp.pkgdir or not bp.srcdir or not bp.tmpdir:
        msg = _('Unable to create a BuildProfile based on this Kit Source directory!')
        self.printMsgExit(msg)

    # set up the .rpmmacros
    msg = _('Setting up a proper .rpmmacros for building this kit')
    print msg
    rpmmacrosExist, oldrpmmacros = bkinst.setupRPMMacros(bp)
    if rpmmacrosExist:
        atexit.register(restoreRpmMacros,oldrpmmacros)
    else:
        atexit.register(removeRpmMacros)

    # get the kitscript
    _ks = options.kitscript
    kitscript = ''
    try:
        msg = _('Looking for the kitscript %(kitscript)s..' % {'kitscript':_ks})
        print msg
        kitscript = bkinst.getKitScript(kitsrc,_ks)
    except FileDoesNotExistError:
        msg = _('kitscript %(kitscript)s not found!' % {'kitscript':_ks})
        printMsgExit(msg)

    # looks like everything is down pat, now the hard stuff
    msg = _('Found kitscript. Loading it..')
    print msg
    kit, components, packages = bkinst.loadKitScript(kitscript)

    # get the current arch
    curArch = getArch()
    arch = kit['arch']

    if arch != curArch and arch != 'noarch':
        msg = _('Creating kit for %(arch)s is not possible on this system. The allowed architectures are noarch and %(curArch)s.' \
                % {'arch':arch,'curArch':curArch})
        printMsgExit(msg)

    if arch != 'noarch':
        msg = _('Building kit for %(arch)s architecture..' % {'arch':arch})
    else:
        msg = _('Building kit for all architectures..' % {'arch':arch})
    print msg

    # validate the syntax
    # set up a counter
    c = 0
    missingAttributes = []
    # first the packages
    for pkg in packages:
        sv = getSyntaxValidator(pkg)
        if not sv.validate():
            for a in sv.getMissingAttributes():
                if not a in missingAttributes: missingAttributes.append(a)
            c += 1

    if c > 0:
        msg = _('There are missing attributes for the package(s): %(missinglist)r' %
                {'missinglist':missingAttributes})
        print msg
        msg = _('Please fix this and build again.')
        printMsgExit(msg)

    # set up a counter
    c = 0
    missingAttributes = []
    # second the comps
    for comp in components:
        sv = getSyntaxValidator(comp)
        if not sv.validate():
            for a in sv.getMissingAttributes():
                if not a in missingAttributes: missingAttributes.append(a)
            c += 1

    if c > 0:
        msg = _('There are missing attributes for the component(s): %(missinglist)r' %
                {'missinglist':missingAttributes})
        print msg
        msg = _('Please fix this and build again.')
        printMsgExit(msg)

    # set up a counter
    c = 0
    missingAttributes = []
    # lastly the kit
    sv = getSyntaxValidator(kit)
    if not sv.validate():
        for a in sv.getMissingAttributes():
            if not a in missingAttributes: missingAttributes.append(a)
        c += 1

    if c > 0:
        msg = _('There are missing attributes for the kit: %(missinglist)r' %
                {'missinglist':missingAttributes})
        print msg
        msg = _('Please fix this and build again.')
        printMsgExit(msg)

    # lets build the packages if any:
    if packages:
        try:
            msg = _('Building the package(s)..')
            print msg
            bkinst.handlePackages(packages,bp)
        except FileDoesNotExistError, e:
            msg = _('File %(filename)s not found! Please fix this and build again.' \
                    % {'filename':e})
            printMsgExit(msg)
        except PackageAttributeNotDefined, e:
            msg = _('Package attribute %(attribute)s is not defined! Please fix this and build again.' \
                % {'attribute':e})
            printMsgExit(msg)
        except PackageBuildError, e:
            msg = _('Error building package %(name)s! Please fix this and build again.' \
                    % {'name':e})
            printMsgExit(msg)

    if components:
        try:
            msg = _('Building the packages for component(s)..')
            bkinst.handleComponents(components,bp)
            print msg
        except PackageBuildError, e:
            msg = _('Error building component %(name)s! Please fix this and build again.' \
                    % {'name':e})
            printMsgExit(msg)
            
    if kit:
        try:
            msg = _('Building the package for the kit..')
            bkinst.handleKit(kit,bp)
            print msg
        except PackageBuildError, e:
            msg = _('Error building kit! Please fix this and build again.')
            printMsgExit(msg)
            
    # populate the packages dir
    msg = _('Populating the packages directory with the Kit artifacts..')
    print msg
    bkinst.populatePackagesDir(bp,arch)
        
    # generate the kitinfo file
    msg = _('Generating kitinfo..')
    print msg
    kitinfo = '%s/kitinfo' % kitsrc
    bkinst.generateKitInfo(kit,kitinfo)
        
    # finally, make the kit artifact
    if makeiso:
        msg = _('Creating the Kit iso..')
        print msg
        kitiso = bkinst.makeKitISO(kitsrc)
        
        if not kitiso:
            msg = _('Error creating Kit ISO!')
            printMsgExit(msg)
                
        msg = _('Kit ISO created.')
        print msg
        msg = _('ISO file is at %(isofile)s.' % {'isofile':kitiso})
        print msg
    else:
        msg = _('Creating the Kit dir..')
        print msg
        bkinst.makeKitDir(kitsrc,kitdir)
        msg = _('Kit directory created..')
        print msg
        msg = _('Kit directory is at %(kitdir)s.' % {'kitdir':kitdir})
        print msg


makeKitFactory = {'0.1': makeKitv01,
    '0.2': makeKitv02,
    'default': makeKitv01} # default will be v0.1
