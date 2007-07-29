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
        
    def testBuildEmptyKit(self):
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
        
        
        
        

