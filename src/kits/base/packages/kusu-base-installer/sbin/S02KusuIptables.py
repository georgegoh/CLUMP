#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core.plugin import Plugin
from kusu.hardware import probe 

class KusuRC(Plugin):
    def __init__(self):
        Plugin.__init__(self)
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

