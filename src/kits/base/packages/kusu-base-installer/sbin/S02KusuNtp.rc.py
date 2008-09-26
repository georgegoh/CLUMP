#!/usr/bin/env python
# $Id: S02KusuNtp.rc.py 2101 2007-08-22 10:18:52Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin

import os
import pwd

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'ntpd'
        self.desc = 'Setting up ntpd'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        if path('/etc/ntp.conf').exists():
            self.runCommand('/etc/init.d/ntpd start')
            self.runCommand('/sbin/chkconfig ntpd on')
        
        return True
