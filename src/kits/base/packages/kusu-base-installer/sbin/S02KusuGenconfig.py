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
        self.name = 'genhosts'
        self.desc = 'Generating /etc/hosts'
        self.ngtypes = ['installer']
        self.delete = False

    def run(self):
        etchosts = path('/etc/hosts')

        if not etchosts.exists():
            etchosts.touch()

        retcode, out, err = self.runCommand("genconfig hosts > " + etchosts)

        if not retcode == 0:
            return False

        return True

