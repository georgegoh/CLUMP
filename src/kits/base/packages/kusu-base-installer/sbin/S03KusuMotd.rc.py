#!/usr/bin/env python
# $Id: S03KusuMotd.rc.py 3137 2009-10-23 06:26:27Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
import sys

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
            lines[motdline] = '%s %s (build %s) Installer Node\n' % ('${KUSU_RELEASE_NAME}', '${VERSION_STR}', '${KUSU_REVISION}')

        f = open('/etc/motd', 'w')
        f.writelines(lines)
        f.close()

        return True
