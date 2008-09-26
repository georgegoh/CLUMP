#!/usr/bin/env python
# $Id: S02KusuMotd.rc.py 2101 2007-08-22 10:18:52Z ltsai $
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
        lines = f.readlines()
        f.close()

        motdlines = []
        # find the lines containing 'Kusu * Installer Node'
        for x in xrange(len(lines)):
            # find returns 0 when line begins with find term
            if not lines[x].find('Kusu') \
                and lines[x].find('Installer Node') > 0:
                motdlines.append(x)

        if not motdlines:
            lines.append('')
            motdlines.append(-1)

        for motdline in motdlines:
            lines[motdline] = 'Kusu %s Installer Node\n' % VERSION

        f = open('/etc/motd', 'w')
        f.writelines(lines)
        f.close()

        return True
