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
        self.name = 'kusu'
        self.desc = 'Setting up kusu infrastructure'

    def run(self):
        self.runCommand('sh /etc/rc.kusu.d/S01KusuSetup')

        return True
