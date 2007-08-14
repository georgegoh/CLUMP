#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
import sys

VERSION = 1.0

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'motd'
        self.desc = 'Setting up motd'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        f = open('/etc/motd', 'r')
        lines = f.read()
        f.close()

        f = open('/etc/motd', 'w')
        f.write(lines)
        f.write('Kusu %s Installer Node\n' % VERSION)
        f.close()

        return True
