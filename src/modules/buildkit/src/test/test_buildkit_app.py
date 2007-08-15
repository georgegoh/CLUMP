#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.util import tools
import subprocess
from kusu.buildkit import *
from path import path
from cStringIO import StringIO

class TestBuildKitApp(object):
    """ Basic tests for the app"""

    def setUp(self):
        """ Prep tests. """
        self.scratchdir = path(tools.mkdtemp(prefix='test-buildkit-app-'))

        
    def tearDown(self):
        """ Housekeeping. """
        if self.scratchdir.exists(): self.scratchdir.rmtree()
        
    def testNewKitSrcDir(self):
        """ Test to create a Kit Source directory. """
        cmd = 'buildkit new kit=test > /dev/null 2>&1'
        p = subprocess.Popen(cmd,shell=True,cwd=self.scratchdir)
        p.wait()

        assert p.returncode == 0
        
    def testVerifyNewKitSrcDir(self):
        """ Test to verify a Kit Source directory. """
        cmd = 'buildkit new kit=test > /dev/null 2>&1' 
        p = subprocess.Popen(cmd,shell=True,cwd=self.scratchdir)
        p.wait()
        kitsrc = KitSrcFactory(self.scratchdir / 'test')
        
        assert kitsrc.verifySrcPath() is True
        
    def testBuildEmptyKitISO(self):
        """ Test to create an empty kit and build it. """
        cmd1 = 'buildkit new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()
        
        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()
        
        kitsrcdir = self.scratchdir / 'test'
        isofile = kitsrcdir / 'kit-test-0.1-0-noarch.iso'
        
        assert isofile.exists()
        
    def testBuildEmptyKitDir(self):
        """ Test to create an empty kit and build it. """
        cmd1 = 'buildkit new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test dir=testdir > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitdir = self.scratchdir / 'testdir'
        kitinfo = kitdir / 'test/kitinfo'

        assert kitinfo.exists()
        
    def testKitInfoFile(self):
        """ Test to create valid kitinfo and validate it. """
        kitstr = """\
# define a default component
comp = Fedora6Component()
comp.name = 'foo'
comp.description = 'foo component for Fedora Core 6.'

# Add any packages defined earlier by using the comp.addDep method
#comp.addDep(pkg1)

# define a default kit
k = DefaultKit()
k.name = 'foo'
k.description = 'foo kit.'

# Adding the component defined earlier
k.addComponent(comp)
"""
        cmd1 = 'buildkit new kit=foo > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=foo dir=testdir > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()
        kitfile = self.scratchdir / 'foo/build.kit'
        f = open(kitfile,'w')
        f.write(kitstr)
        f.close()
        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitdir = self.scratchdir / 'testdir'
        kitinfo = kitdir / 'foo/kitinfo'
        assert kitinfo.exists()
        
        kit,comps = processKitInfo(kitinfo)

        # assert the kit
        assert kit['name'] == 'foo'
        assert kit['description'] == 'foo kit.'
        assert kit['removable'] == True
        assert kit['license'] == 'LGPL'
        assert kit['pkgname'] == 'kit-foo'
        assert kit['version'] == '0.1'

        # assert the component
        assert len(comps) == 1
        comp = comps[0]
        assert comp['arch'] == 'noarch'
        assert comp['ostype'] == 'fedora'
        assert comp['osversion'] == '6'
        assert comp['ngtypes'] == ['installer','compute']
        assert comp['name'] == 'foo'
        assert comp['description'] == 'foo component for Fedora Core 6.'
        assert comp['pkgname'] == 'component-foo'
        assert comp['compversion'] == '0.1'
        assert comp['comprelease'] == '0'

        
    def testRemovableFalseInKitInfoFile(self):
        """ Test to validate removable attribute for kitinfo. """
        kitstr = """\
# define a default component
comp = Fedora6Component()
comp.name = 'foo'
comp.description = 'foo component for Fedora Core 6.'

# Add any packages defined earlier by using the comp.addDep method
#comp.addDep(pkg1)

# define a default kit
k = DefaultKit()
k.name = 'foo'
k.description = 'foo kit.'
k.removable = False

# Adding the component defined earlier
k.addComponent(comp)
"""
        cmd1 = 'buildkit new kit=foo > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=foo dir=testdir > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()
        kitfile = self.scratchdir / 'foo/build.kit'
        f = open(kitfile,'w')
        f.write(kitstr)
        f.close()
        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitdir = self.scratchdir / 'testdir'
        kitinfo = kitdir / 'foo/kitinfo'
        assert kitinfo.exists()

        kit,comps = processKitInfo(kitinfo)

        # assert the kit
        assert kit['removable'] == False

    def testRemoveableIsRemovableInKitInfoFile(self):
        """ Test to validate removeable/removable attribute for kitinfo. """
        kitstr = """\
# define a default component
comp = Fedora6Component()
comp.name = 'foo'
comp.description = 'foo component for Fedora Core 6.'

# Add any packages defined earlier by using the comp.addDep method
#comp.addDep(pkg1)

# define a default kit
k = DefaultKit()
k.name = 'foo'
k.description = 'foo kit.'
k.removeable = False

# Adding the component defined earlier
k.addComponent(comp)
"""
        cmd1 = 'buildkit new kit=foo > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=foo dir=testdir > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()
        kitfile = self.scratchdir / 'foo/build.kit'
        f = open(kitfile,'w')
        f.write(kitstr)
        f.close()
        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitdir = self.scratchdir / 'testdir'
        kitinfo = kitdir / 'foo/kitinfo'
        assert kitinfo.exists()

        kit,comps = processKitInfo(kitinfo)

        # assert the kit
        assert kit['removable'] == False


        

