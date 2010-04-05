#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
from primitive.system.software.dispatcher import Dispatcher

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
        pixieRoot = self.dbs.AppGlobals.selectfirst_by(kname='PIXIE_ROOT').kvalue

        pxelinux = path('%s/pxelinux.cfg' % pixieRoot)
        if not pxelinux.exists():
            pxelinux.makedirs()

            user, group = Dispatcher.get('webserver_usergroup')
            uid, gid = pwd.getpwnam(user)[2:4]

            pxelinux.chmod(0775)
            pxelinux.chown(uid, gid)

        tftp = path(Dispatcher.get('tftp_conf'))
        if tftp.exists():
            f = open(tftp, 'r')
            lines = f.readlines()
            f.close()

            # Old method:
            # idx = lines.index('\tserver_args\t\t= -s /tftpboot\n')

            # For sles, their /etc/xinetd.d/tftp file does not use tabs.
            # So here's a more generic way by stripping all whitespace
            # before comparing.
            idx = None
            for line in lines:
                orig_line = line
                args = [arg.strip() for arg in line.strip().split('=')]
                if args == ['server_args', '-s /tftpboot']:
                    idx = lines.index(orig_line)
                    break

            if idx:
                f = open(tftp, 'w')
                f.writelines(lines[:idx] + ['\tserver_args\t\t= -s %s\n' % pixieRoot] + lines[idx+1:])
                f.close()

                success, (output, ret, err) = self.service('tftp', 'enable')
                if not success:
                    raise Exception, err

        syslinux = path(Dispatcher.get('pxelinux0_path'))
        if syslinux.exists():
            syslinux.copy('%s/pxelinux.0' % pixieRoot)

        success, (out, ret, err) = self.service('xinetd', 'restart')
        if not success:
            raise Exception, err

        success, (out, ret, err) = self.service('xinetd', 'enable')
        if not success:
            raise Exception, err

        return True

