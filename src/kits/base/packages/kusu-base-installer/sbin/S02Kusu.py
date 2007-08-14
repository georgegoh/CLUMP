#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'kusu'
        self.desc = 'Setting up Kusu infrastructure'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        self.runCommand('sh /etc/rc.kusu.d/S01KusuSetup')

        return True

