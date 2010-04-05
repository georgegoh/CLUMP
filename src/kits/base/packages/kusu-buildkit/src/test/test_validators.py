#!/usr/bin/env python
# $Id: test_validators.py 476 2008-01-25 12:36:55Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.buildkit import checker
from kusu.buildkit import BuildKit
from kusu.buildkit import KusuComponent, KusuKit, PackageProfile
from kusu.util import tools as utiltools
from path import path

class TestKitscriptValidators(object):
    """ Test suite for validating kitscript syntax. """

    def setUp(self):
        self.goodbuildkits = { 'autotools':"""\
# build.kit template

# Define your packages here by using a correct packageprofile class.
# Available types are SourcePackage(), RPMPackage(), SRPMPackage(),
# DistroPackage(), BinaryPackage()

pkg1 = SourcePackage()
pkg1.name = 'foo'
pkg1.version = '1.0'
pkg1.release = '0'
pkg1.installroot = '/opt/foo'
pkg1.filename = 'foo-1.0.tar.gz'

# define a default component
comp = Fedora6Component()
comp.name = 'hello'
comp.description = 'hello component for Fedora Core 6.'

# Add any packages defined earlier by using the comp.addDep method
comp.addDep(pkg1)

# define a default kit
k = DefaultKit()
k.name = 'hello'
k.description = 'hello kit.'

# Adding the component defined earlier
k.addComponent(comp)
"""}

        self.badbuildkits = { 'autotools':"""\
# build.kit template

# Define your packages here by using a correct packageprofile class.
# Available types are SourcePackage(), RPMPackage(), SRPMPackage(),
# DistroPackage(), BinaryPackage()

pkg1 = SourcePackage()
pkg1.name = 'foo'
pkg1.version = '1.0'
pkg1.release = '0'
#pkg1.installroot = '/opt/foo'
#pkg1.filename = 'foo-1.0.tar.gz'

# define a default component
comp = Fedora6Component()
#comp.name = 'hello'
comp.description = 'hello component for Fedora Core 6.'

# Add any packages defined earlier by using the comp.addDep method
comp.addDep(pkg1)

# define a default kit
k = DefaultKit()
k.name = 'hello'
k.description = 'hello kit.'

# Adding the component defined earlier
k.addComponent(comp)
"""
        
        
        }
    
        # set up scratchdir
        self.scratchdir = path(utiltools.mkdtemp())

    def tearDown(self):
        pass
        
    def testValidateGoodAutotoolsBuildKit(self):
        """ Test to validate good autotools build.kit kitscript"""
        buildkitsrc = self.goodbuildkits['autotools']
        buildkitfile = self.scratchdir / 'build.kit'
        f = open(buildkitfile,'w')
        f.write(buildkitsrc)
        f.close()
        
        assert buildkitfile.exists()
        bkinst = BuildKit()
        kit,comps,packages = bkinst.loadKitScript(buildkitfile)
        
        assert kit.name == 'hello'
        
        assert len(packages) == 1
        pkg1 = packages[0]
        assert pkg1.name == 'foo'
        v = checker.getSyntaxValidator(pkg1)
        assert v.validate() is True
        
        assert len(comps) == 1
        comp1 = comps[0]
        v = checker.getSyntaxValidator(comp1)
        assert v.validate() is True
        
        v = checker.getSyntaxValidator(kit)
        assert v.validate() is True
        

    def testValidateBadAutotoolsBuildKit(self):
        """ Test to validate bad autotools build.kit kitscript"""
        buildkitsrc = self.badbuildkits['autotools']
        buildkitfile = self.scratchdir / 'build.kit'
        f = open(buildkitfile,'w')
        f.write(buildkitsrc)
        f.close()

        assert buildkitfile.exists()
        bkinst = BuildKit()
        kit,comps,packages = bkinst.loadKitScript(buildkitfile)

        assert kit.name == 'hello'

        assert len(packages) == 1
        pkg1 = packages[0]
        assert pkg1.name == 'foo'
        v = checker.getSyntaxValidator(pkg1)
        assert v.validate() is False
        missattrs = ['filename','installroot']
        assert v.getMissingAttributes() == missattrs

        assert len(comps) == 1
        comp1 = comps[0]
        v = checker.getSyntaxValidator(comp1)
        assert v.validate() is False
        assert v.getMissingAttributes() == ['name']

        
        
            
