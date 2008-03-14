#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.util import tools, rpmtool
import subprocess
from kusu.buildkit import *
from path import path
from cStringIO import StringIO
from nose import SkipTest
from subprocess import Popen, PIPE

RPMdir = path(tools.mkdtemp(prefix='buildkit-assets-'))
URI = 'http://www.osgdc.org/pub/build/tests/modules/buildkit/'

def setUp():
    cmd = "lftp -e 'mget *.rpm && exit' %s > /dev/null 2>&1" % URI
    lftpP = subprocess.Popen(cmd,shell=True,cwd=RPMdir)
    lftpP.wait()
    
def tearDown():
    if RPMdir.exists(): RPMdir.rmtree()

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
        
        # get the current arch
        _arch = tools.getArch()
        
        if _arch == 'x86':
            arch = 'i386'
        else:
            arch = _arch
        
        isoname = 'kit-test-0.1-0.%s.iso' % arch
        isofile = kitsrcdir / isoname
        
        assert isofile.exists()
        
    def testBuildx86EmptyKitISO(self):
        """ Test to create an empty x86 kit and build it. """
        
        if getArch() != 'x86': raise SkipTest
        
        cmd1 = 'buildkit --arch=x86 new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitsrcdir = self.scratchdir / 'test'

        isoname = 'kit-test-0.1-0.i386.iso'
        isofile = kitsrcdir / isoname

        assert isofile.exists()

    def testBuildx86_64EmptyKitISO(self):
        """ Test to create an empty x86_64 kit and build it. """
        
        if getArch() != 'x86_64': raise SkipTest
        
        cmd1 = 'buildkit --arch=x86_64 new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitsrcdir = self.scratchdir / 'test'

        isoname = 'kit-test-0.1-0.x86_64.iso'
        isofile = kitsrcdir / isoname

        assert isofile.exists()


    def testBuildnoarchEmptyKitISO(self):
        """ Test to create an empty noarch kit and build it. """
        cmd1 = 'buildkit --arch=noarch new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitsrcdir = self.scratchdir / 'test'

        isoname = 'kit-test-0.1-0.noarch.iso'
        isofile = kitsrcdir / isoname

        assert isofile.exists()

        
        
    def testBuildEmptyKitDir(self):
        """ Test to create an empty kit and build it. """
        cmd1 = 'buildkit --arch=noarch new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test dir=testdir > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitdir = self.scratchdir / 'testdir'
        _tdir = self.scratchdir / 'tdir'
        _tdir.mkdir()
        rpmfile = kitdir / 'test/kit-test-0.1-0.noarch.rpm'
        assert rpmfile.exists()
        kitrpm = rpmtool.RPM(str(rpmfile))
        kitrpm.extract(_tdir)
        _li = [f for f in _tdir.walkfiles('kitinfo')]
        assert len(_li) == 1
        kitinfo = _li[0]

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
k.arch = 'noarch'

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
        _tdir = self.scratchdir / 'tdir'
        _tdir.mkdir()
        rpmfile = kitdir / 'foo/kit-foo-0.1-0.noarch.rpm'
        assert rpmfile.exists()
        kitrpm = rpmtool.RPM(str(rpmfile))
        kitrpm.extract(_tdir)
        _li = [f for f in _tdir.walkfiles('kitinfo')]
        assert len(_li) == 1
        kitinfo = _li[0]
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
k.arch = 'noarch'

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
        _tdir = self.scratchdir / 'tdir'
        _tdir.mkdir()
        rpmfile = kitdir / 'foo/kit-foo-0.1-0.noarch.rpm'
        assert rpmfile.exists()
        kitrpm = rpmtool.RPM(str(rpmfile))
        kitrpm.extract(_tdir)
        _li = [f for f in _tdir.walkfiles('kitinfo')]
        assert len(_li) == 1
        kitinfo = _li[0]
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
k.arch = 'noarch'

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
        _tdir = self.scratchdir / 'tdir'
        _tdir.mkdir()
        rpmfile = kitdir / 'foo/kit-foo-0.1-0.noarch.rpm'
        assert rpmfile.exists()
        kitrpm = rpmtool.RPM(str(rpmfile))
        kitrpm.extract(_tdir)
        _li = [f for f in _tdir.walkfiles('kitinfo')]
        assert len(_li) == 1
        kitinfo = _li[0]
        assert kitinfo.exists()

        kit,comps = processKitInfo(kitinfo)

        # assert the kit
        assert kit['removable'] == False

    def testPackagesExist(self):
        """ Test to check if the rpms are downloaded and exist. """
        assert RPMdir.exists()

        foos = ['foo%i-1-1.i386.rpm'%i for i in xrange(10)]
        for foo in foos:
            assert path(RPMdir / foo).exists()

        bars = ['bar%i-1-1.x86_64.rpm'%i for i in xrange(10)]
        for bar in bars:
            assert path(RPMdir / bar).exists()

        bazs = ['baz%i-1-1.noarch.rpm'%i for i in xrange(10)]
        for baz in bazs:
            assert path(RPMdir / baz).exists()
            
    
    def testBuildKitLostScript(self):
        """Test to build a kit while post script doesn't exist."""

        cmd1 = 'buildkit new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test'

        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()

        # delete the post script file
        path(self.scratchdir / 'test/sources/00-post-script.sh').remove()

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir, stderr=PIPE, stdout=PIPE)
        p.wait()

        _errmsg = 'Error opening file %s/test/sources/00-post-script.sh, The file does not exist.' % self.scratchdir
        _stdstring = ''

        # get output message of the buildkit command

        _pipestd = p.stdout
        for _eachline in _pipestd:
            _stdstring += _eachline

        _pipestd.close()

        # check if the error occurs
        _idx = _stdstring.index(_errmsg, 0, len(_stdstring))

        assert _idx > 0


    def testBuildx86Kit(self):
        """ Test to build a kit containing x86 packages. """
        
        if getArch() != 'x86': raise SkipTest
        
        cmd1 = 'buildkit --arch=x86 new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test dir=testdir > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()
        
        # copy the rpms into the srcdir
        
        for p in RPMdir.walkfiles('*.rpm'):
            p.copy(self.scratchdir / 'test/sources')

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitdir = self.scratchdir / 'testdir'
        _tdir = self.scratchdir / 'tdir'
        _tdir.mkdir()
        rpmfile = kitdir / 'test/kit-test-0.1-0.i386.rpm'
        assert rpmfile.exists()
        kitrpm = rpmtool.RPM(str(rpmfile))
        kitrpm.extract(_tdir)
        _li = [f for f in _tdir.walkfiles('kitinfo')]
        assert len(_li) == 1
        kitinfo = _li[0]

        assert kitinfo.exists()
        
        rpmdir = kitdir / 'test'
        # there should not be any x86_64 packages here
        rpmfiles = rpmdir.files('*.x86_64.rpm')
        assert not rpmfiles

        rpmfiles = rpmdir.files('*86.rpm')
        assert rpmfiles
        
        rpmfiles = rpmdir.files('*.noarch.rpm')
        assert rpmfiles

    def testBuildx86_64Kit(self):
        """ Test to build a kit containing x86_64 packages. """
        
        if getArch() != 'x86_64': raise SkipTest
        
        cmd1 = 'buildkit --arch=x86_64 new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test dir=testdir > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()

        # copy the rpms into the srcdir

        for p in RPMdir.walkfiles('*.rpm'):
            p.copy(self.scratchdir / 'test/sources')

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitdir = self.scratchdir / 'testdir'
        _tdir = self.scratchdir / 'tdir'
        _tdir.mkdir()
        rpmfile = kitdir / 'test/kit-test-0.1-0.x86_64.rpm'
        assert rpmfile.exists()
        kitrpm = rpmtool.RPM(str(rpmfile))
        kitrpm.extract(_tdir)
        _li = [f for f in _tdir.walkfiles('kitinfo')]
        assert len(_li) == 1
        kitinfo = _li[0]

        assert kitinfo.exists()

        rpmdir = kitdir / 'test'

        rpmfiles = rpmdir.files('*.x86_64.rpm')
        assert rpmfiles

        # there should not be any x86 packages here
        rpmfiles = rpmdir.files('*86.rpm')
        assert not rpmfiles

        rpmfiles = rpmdir.files('*.noarch.rpm')
        assert rpmfiles
        
    def testBuildnoarchKit(self):
        """ Test to build a kit containing noarch packages. """
        cmd1 = 'buildkit --arch=noarch new kit=test > /dev/null 2>&1'
        cmd2 = 'buildkit make kit=test dir=testdir > /dev/null 2>&1'
        p = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        p.wait()

        # copy the rpms into the srcdir

        for p in RPMdir.walkfiles('*.rpm'):
            p.copy(self.scratchdir / 'test/sources')

        p = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        p.wait()

        kitdir = self.scratchdir / 'testdir'
        _tdir = self.scratchdir / 'tdir'
        _tdir.mkdir()
        rpmfile = kitdir / 'test/kit-test-0.1-0.noarch.rpm'
        assert rpmfile.exists()
        kitrpm = rpmtool.RPM(str(rpmfile))
        kitrpm.extract(_tdir)
        _li = [f for f in _tdir.walkfiles('kitinfo')]
        assert len(_li) == 1
        kitinfo = _li[0]

        assert kitinfo.exists()

        rpmdir = kitdir / 'test'

        rpmfiles = rpmdir.files('*.x86_64.rpm')
        assert rpmfiles

        rpmfiles = rpmdir.files('*86.rpm')
        assert rpmfiles

        rpmfiles = rpmdir.files('*.noarch.rpm')
        assert rpmfiles
