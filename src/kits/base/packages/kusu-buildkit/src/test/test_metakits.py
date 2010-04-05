#!/usr/bin/env python
# $Id: test_metakits.py 476 2008-01-25 12:36:55Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This suite tests meta kits"""

import subprocess
from kusu.util import tools
from path import path


class TestMetaKit:
    
    def setUp(self):
        """ set up fixtures. """
        self.scratchdir = path(tools.mkdtemp(prefix='buildkit-metakit-'))
        
    def tearDown(self):
        """ Housekeeping. """
        if self.scratchdir.exists(): self.scratchdir.rmtree()
        
    def testMetaKitFromDir(self):
        """ Test to create a meta kit from kit directories. """
        
        # kit foo
        cmd1 = 'buildkit new kit=foo'
        cmd2 = 'buildkit make kit=foo dir=t'
        fooP = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        fooP.wait()
        fooP = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        fooP.wait()
        
        
        fooKitDir = path(self.scratchdir / 't/foo')
        
        assert fooKitDir.exists()
        
        # kit bar
        cmd1 = 'buildkit new kit=bar'
        cmd2 = 'buildkit make kit=bar dir=t'
        barP = subprocess.Popen(cmd1,shell=True,cwd=self.scratchdir)
        barP.wait()
        barP = subprocess.Popen(cmd2,shell=True,cwd=self.scratchdir)
        barP.wait()
        
        
        barKitDir = path(self.scratchdir / 't/bar')
        
        assert barKitDir.exists()
        
        # create metakit
        cmd = 'buildkit make-meta dir=t'
        metaP = subprocess.Popen(cmd,shell=True,cwd=self.scratchdir)
        metaP.wait()
        
        isoname = '+'.join(sorted(['foo','bar'])) + '.iso'        
        assert path(self.scratchdir / isoname).exists()
        
    def testEmptyMetaKitDir(self):
        """ Test to validate make-meta on an empty directory. """
        
        emptydir = self.scratchdir / 'empty'
        emptydir.mkdir()
        
        cmd = 'buildkit make-meta dir=empty'
        metaP = subprocess.Popen(cmd,shell=True,cwd=self.scratchdir)
        metaP.wait()
        
        assert metaP.returncode != 0
