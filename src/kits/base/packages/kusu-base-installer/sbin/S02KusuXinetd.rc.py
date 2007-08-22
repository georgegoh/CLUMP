#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin

import os
import pwd

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'xinetd'
        self.desc = 'Setting up xinetd'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        pxelinux = path('/tftpboot/kusu/pxelinux.cfg')
        if not pxelinux.exists():
            pxelinux.makedirs()

            apache = pwd.getpwnam('apache')
            uid = apache[2]
            gid = apache[3]

            pxelinux.chmod(0775)
            pxelinux.chown(uid, gid)

        tftp = path('/etc/xinetd.d/tftp')
        if tftp.exists():
            f = open(tftp, 'r')
            lines = f.readlines()
            f.close()

            try:
                idx = lines.index('\tserver_args\t\t= -s /tftpboot\n')

                f = open(tftp, 'w')
                f.writelines(lines[:idx] + ['\tserver_args\t\t= -s /tftpboot/kusu\n'] + lines[idx+1:])
                f.close()

                self.runCommand('/sbin/chkconfig tftp on')
            except:pass

        syslinux = path('/usr/lib/syslinux/pxelinux.0')
        if syslinux.exists():
            syslinux.copy('/tftpboot/kusu/pxelinux.0')

        self.runCommand('/etc/init.d/xinetd restart')
        self.runCommand('/sbin/chkconfig xinetd on')

        return True
