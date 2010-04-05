#!/usr/bin/env python
# $Id: S03KusuSSH.rc.py 3158 2009-11-02 07:09:37Z mxu $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from path import path
from kusu.core import rcplugin
from primitive.system.software.dispatcher import Dispatcher 

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'ssh-keys'
        self.desc = 'Setting up SSH public keys'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Setup ssh public keys"""

        if path('/root/.ssh/id_rsa').exists() or path('/root/.ssh/id_rsa.pub').exists():
            return True

        sshdir = path('/root/.ssh')

        if not sshdir.exists():
            sshdir.makedirs()

        sshdir.chmod(0700)

        # RSA key, 2048 bits in size, /root/.ssh/id_rsa, no passphrase
        cmd = "ssh-keygen -t rsa -b 2048 -f %s -N ''" % (sshdir / 'id_rsa')
        retcode = self.runCommand(cmd)[0]

        if retcode != 0:
            return False

        # place our public key in web root
        webdir = path(Dispatcher.get('webserver_docroot'))
        if not webdir.exists():
            webdir.makedirs()

        # append public key to authorized_keys
        keyfile = open(sshdir / 'id_rsa.pub', 'rb')
        authorized_keys_file = open(sshdir / 'authorized_keys', 'ab')

        authorized_keys_file.write(keyfile.read())

        keyfile.close()
        authorized_keys_file.close()

        # Generate public/private key pair and authorized_keys file
        # for compute only
        installerPubKey = sshdir / 'id_rsa.pub'
        self.genSSHKeyForComputeOnly(installerPubKey)

        return True

    def genSSHKeyForComputeOnly(self, installerPubKey):
        """Generate public/private key pair and authorized_keys file
           for compute nodes of managed nodegroups only."""

        kususshdir = path('/opt/kusu/etc/.ssh')

        if not kususshdir.exists():
            kususshdir.makedirs()

        # RSA key, 2048 bits in size, /opt/kusu/etc/.ssh/id_rsa, no passphrase
        cmd = "ssh-keygen -t rsa -b 2048 -f %s -N ''" % (kususshdir / 'id_rsa')
        retcode = self.runCommand(cmd)[0]

        if retcode != 0:
            return False

        # append the public key of the installer node and the public key
        # generated for compute-only to authorized_keys
        installerKeyfile = open(installerPubKey, 'rb')
        computeKeyfile = open(kususshdir / 'id_rsa.pub', 'rb')
        authorized_keys_file = open(kususshdir / 'authorized_keys', 'ab')

        authorized_keys_file.write(installerKeyfile.read())
        authorized_keys_file.write(computeKeyfile.read())

        installerKeyfile.close()
        computeKeyfile.close()
        authorized_keys_file.close()

        # /opt/kusu/etc/.ssh and its contents must be read for root only
        os.system('chmod -R 0600 %s' % kususshdir)
        os.system('chown -R root:root %s' % kususshdir)
