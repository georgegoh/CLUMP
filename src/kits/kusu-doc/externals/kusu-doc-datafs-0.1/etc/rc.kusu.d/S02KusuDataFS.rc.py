#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

from path import path
from kusu.core import rcplugin
import sys

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'Kusu Documentation sources'
        self.desc = 'Setting up Kusu Documentation sources'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setting up Kusu Documentation sources"""
        
        datafs = path('/opt/kusu/share/doc/kusu/Data.fs')
        olddatafs = path('/opt/Plone-3.0.3/zinstance/var/Data.fs')
        
        if not datafs.exists(): return False
            
        if not olddatafs.exists(): return False
            
        # delete the stock Data.fs
        olddatafs.remove()
        
        # copy our Data.fs into the old path
        datafs.copy('/opt/Plone-3.0.3/zinstance/var')
        
        return True
