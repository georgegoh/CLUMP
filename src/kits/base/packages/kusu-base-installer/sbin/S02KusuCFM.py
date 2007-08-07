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

    def run(self):
        """Setting up CFM"""

        files = [path('/etc/shadow'),
                 path('/etc/passwd'),
                 path('/etc/group'),
                 path('/etc/hosts')]

        ngs = self.dbs.NodeGroups.select()

        for ng in ngs:
            ngname = ng.ngname

            if ngname == 'unmanaged':
                continue

            dest = path('/etc') / 'cfm' / ngname

            if not dest.exists(): dest.makedirs()

            for file in files:
                newDir = dest + file.parent
                if not newDir.exists():
                    newDir.makedirs()

                newFile = newDir / file.basename()
                if not newFile.exists():
                    file.symlink(newFile)

            fstab = newDir / 'fstab.append'
            if not fstab.exists():
                f = open(fstab, 'w')
                f.write('# Appended by CFM\n')
                f.write('# Entries below this come from the CFM\'s fstab.append\n')
                f.close()

        return True
