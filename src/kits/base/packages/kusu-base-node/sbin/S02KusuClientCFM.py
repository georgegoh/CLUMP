#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core.plugin import Plugin

class KusuRC(Plugin):
    def __init__(self):
        Plugin.__init__(self)
        self.name = 'cfm'
        self.desc = 'Setting up CFM'
        self.ngtypes = ['compute']
        self.delete = True

    def run(self):
        """Start CFM on compute"""

        self.runCommand('/sbin/chkconfig cfmd on')
        retval = self.runCommand('/etc/init.d/cfmd restart > /dev/null')[0]

        if retval == 0:
            return True
        else:
            return False
