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

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'cfm'
        self.desc = 'Setting up CFM'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setting up CFM"""

        files = [path('/etc/shadow'),
                 path('/etc/passwd'),
                 path('/etc/group'),
                 path('/etc/hosts'),
                 path('/etc/hosts.equiv'),
                 path('/etc/ssh/ssh_config'),
                 path('/etc/ssh/ssh_host_dsa_key'),
                 path('/etc/ssh/ssh_host_key'),
                 path('/etc/ssh/ssh_host_rsa_key'),
                 path('/etc/ssh/ssh_host_dsa_key.pub'),
                 path('/etc/ssh/ssh_host_key.pub'),
                 path('/etc/ssh/ssh_host_rsa_key.pub')]

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

            fstab = dest / 'etc' / 'fstab.append'
            if not fstab.exists():
                f = open(fstab, 'w')
                f.write('# Appended by CFM\n')
                f.write('# Entries below this come from the CFM\'s fstab.append\n')
                f.close()

        

        # Redirect all stdout, stderr
        oldOut = sys.stdout
        oldErr = sys.stderr
        f = open('/dev/null', 'w')
        sys.stdout = f
        sys.stderr = f

        # Update the cfm files
        from kusu.cfms import PackBuilder
        from kusu.core import app 
        kApp = app.KusuApp()
        _ = kApp.langinit()
        pb = PackBuilder(kApp.errorMessage, kApp.stdoutMessage)
        size = pb.updateCFMdir()
        pb.genFileList()

        # Restore stdout and stderr
        sys.stdout = oldOut
        sys.stderr = oldErr 

        return True
