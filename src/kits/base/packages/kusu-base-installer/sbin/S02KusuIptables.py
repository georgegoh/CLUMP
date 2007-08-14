#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
from kusu.hardware import probe 

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'iptables'
        self.desc = 'Setting up iptables'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        #probe.getAllInterfaces()
        #path('/etc/systcl.conf')
        #path('/etc/sysconfig/iptables')
        #self.dbs
        #retval = self.runCommand('/etc/init.d/iptables restart')[0]
        return True

