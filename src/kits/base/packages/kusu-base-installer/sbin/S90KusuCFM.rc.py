#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import sys
from path import path
from kusu.core import rcplugin
from kusu.util.cfm import updateCfmfiles

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

            # Create symbolic links to the private key and the
            # authorized_keys file generated under
            # /opt/kusu/etc/.ssh for managed compute nodegroups only.
            ngtype = ng.type
            if ngtype.startswith('compute'):
                self.createLinkToSSHKeyForComputeOnly(dest)

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

        # Redirect all stdout, stderr
        oldOut = sys.stdout
        oldErr = sys.stderr
        f = open('/dev/null', 'w')
        sys.stdout = f
        sys.stderr = f

        # Update cfmfiles.lst
        updateCfmfiles()

        # Restore stdout and stderr
        sys.stdout = oldOut
        sys.stderr = oldErr

        retval = self.runCommand('/opt/kusu/sbin/kusu-cfmsync -p')[0]

        if retval == 0:
            return True
        else:
            return False

    def createLinkToSSHKeyForComputeOnly(self, cfmDir):
        """Create CFM symbolic links to private key and the
           authorized_keys file generated under
           /opt/kusu/etc/.ssh for managed compute nodegroups only"""

        sshKeyDir = path('/opt/kusu/etc/.ssh')
        linkDir = cfmDir / 'root' / '.ssh'
        if not linkDir.exists():
            linkDir.makedirs()

        authorizedKeys = sshKeyDir / 'authorized_keys'
        authorizedKeysLink = linkDir / 'authorized_keys'
        privateKey = sshKeyDir / 'id_rsa'
        privateKeyLink = linkDir / 'id_rsa'

        if not authorizedKeysLink.exists() and authorizedKeys.exists():
            authorizedKeys.symlink(authorizedKeysLink)

        if not privateKeyLink.exists() and privateKey.exists():
            privateKey.symlink(privateKeyLink)

        # /etc/cfm/<nodegroup>/root and its contents must be
        # read for root only
        os.system('chmod -R 0600 %s' % linkDir.parent)
        os.system('chown -R root:root %s' % linkDir.parent)
