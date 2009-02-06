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

        files = [path('/etc/cfm/shadow.merge'),
                 path('/etc/cfm/passwd.merge'),
                 path('/etc/cfm/group.merge'),
                 path('/etc/pam.d/system-auth-ac'),
                 path('/etc/hosts'),
                 path('/etc/hosts.equiv'),
                 path('/etc/ssh/ssh_config'),
                 path('/etc/ssh/ssh_host_dsa_key'),
                 path('/etc/ssh/ssh_host_key'),
                 path('/etc/ssh/ssh_host_rsa_key'),
                 path('/etc/ssh/ssh_host_dsa_key.pub'),
                 path('/etc/ssh/ssh_host_key.pub'),
                 path('/etc/ssh/ssh_host_rsa_key.pub')]

        # FIXME: Rightfully /etc/pam.d/system-auth-ac only needs to be
        # distributed to rhel/centos nodes. However, we currently do
        # not have a clean way to do this based on the OS of each
        # nodegroup. We can handle that issue partly in this script but
        # should the user make a copy of a nodegroup using ngedit and
        # changes the OS (say from centos to sles), the CFM symlinks
        # are going to be wrong. In this particular instance, having
        # /etc/pam.d/system-auth-ac in SLES is OK since it is not
        # referenced by other pam config files.

        ngs = self.dbs.NodeGroups.select()

        for ng in ngs:
            ngname = ng.ngname

            if ngname == 'unmanaged':
                continue

            dest = path('/etc') / 'cfm' / ngname

            if not dest.exists(): dest.makedirs()

            for file in files:
                if file in ['/etc/cfm/shadow.merge', 
                            '/etc/cfm/passwd.merge', 
                            '/etc/cfm/group.merge']:
                    # We want to leave the symlinks for these
                    # special files within /etc/cfm/<ngname>/etc
                    newDir = dest / 'etc'
                else:
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
        pb.genMergeFiles()
        size = pb.updateCFMdir()
        pb.genFileList()

        # Restore stdout and stderr
        sys.stdout = oldOut
        sys.stderr = oldErr

        retval = self.runCommand('/opt/kusu/sbin/cfmsync -p')[0]

        if retval == 0:
            return True
        else:
            return False

