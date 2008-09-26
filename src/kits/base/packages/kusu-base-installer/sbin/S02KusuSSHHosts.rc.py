#!/usr/bin/env python
# $Id: S02KusuSSHHosts.rc.py 2334 2007-09-24 07:44:22Z ggoh $
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
        self.name = 'ssh'
        self.desc = 'Setting up SSH host file'
        self.ngtypes = ['installer']
        self.delete = False

    def run(self):
        """Setup ssh host file"""
        retval = self.runCommand('$KUSU_ROOT/bin/genconfig ssh > /etc/ssh/ssh_config')[0]

        f = path('/etc/ssh/ssh_config')
        f.chmod(0644)

        return True
