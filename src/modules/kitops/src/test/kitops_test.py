#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.kitops.kitops import KitOps

class TestKitOps:
    def setUp(self):
        self.koinst = KitOps()

    def testSetPrefix(self):
        some_prefix = '/some/prefix'
        self.koinst.setPrefix(some_prefix)
        
        assert self.koinst.prefix == some_prefix
        assert self.koinst.kits_dir.startswith(some_prefix)
        assert self.koinst.pxeboot_dir.startswith(some_prefix)
