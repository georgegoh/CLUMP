#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core.plugin import Plugin

try:
    import subprocess
except:
    from popen5 import subprocess

class KusuRC(Plugin):
    def __init__(self):
        Plugin.__init__(self)
        self.name = 'ssh'
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
        cmds = ['ssh-keygen', '-t', 'rsa', '-b', '2048',
                '-f', sshdir / 'id_rsa', '-N', '']
        sshP = subprocess.Popen(cmds, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = sshP.communicate()
        retcode = sshP.returncode

        if retcode != 0:
            return False

        # place our public key in web root
        webdir = path('/var/www/html')

        if not webdir.exists():
            webdir.makedirs()

        # copy public key to webdir
        (sshdir / 'id_rsa.pub').copy(webdir / 'public_keys')

        return True
