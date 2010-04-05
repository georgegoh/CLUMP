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
        self.name = 'skel'
        self.desc = 'Setting up user skel files'
        self.ngtypes = ['installer']
        self.delete = False

    def run(self):
        """Setup /etc/skel/.bashrc file"""
        retval = self.runCommand('$KUSU_ROOT/bin/kusu-genconfig bashrc > /etc/skel/.bashrc')[0]

        f = path('/etc/skel/.bashrc')
        f.chmod(0644)

        return True
