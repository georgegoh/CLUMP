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
        self.desc = 'Generating hosts, hosts.equiv, and resolv.conf'
        self.ngtypes = ['installer']
        self.delete = False

    def run(self):
        etchosts = path('/etc/hosts')

        if not etchosts.exists():
            etchosts.touch()

        retcode, out, err = self.runCommand("genconfig hosts > " + etchosts)

        if not retcode == 0:
            return False

        etchostsequiv = path('/etc/hosts.equiv')
        if not etchostsequiv.exists():
            etchostsequiv.touch()

        retcode, out, err = self.runCommand("genconfig hostsequiv > " +
                                            etchostsequiv)

        if not retcode == 0:
            return False

        resolv = path('/etc/resolv.conf')

        if not resolv.exists():
            resolv.touch()

        retcode, out, err = self.runCommand("genconfig resolv > " + resolv)

        if not retcode == 0:
            return False

        return True

