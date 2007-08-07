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
        self.name = 'dhcpd'
        self.desc = 'Setting up dhcpd'

    def run(self):

        if path('/etc/dhcpd.conf').exists():
            retval = self.runCommand('$KUSU_ROOT/bin/genconfig dhcpd > /etc/dhcpd.conf')[0]
            if retval != 0:
                return False

            myname = \
                self.dbs.AppGlobals.selectfirst_by(kname='PrimaryInstaller').kvalue
            nics = self.dbs.Nodes.selectfirst_by(name=myname).nics

            dhcpdnics = []
            for nic in nics:
                if nic.network.type == 'provision':
                    dhcpdnics.append(nic.network.device)

            if dhcpdnics:
                f = open('/etc/sysconfig/dhcpd', 'r')
                dhcpd = f.read()
                f.close()

                line = 'DHCPDARGS='
                index = dhcpd.find(line)

                f = open('/etc/sysconfig/dhcpd', 'w')
                f.write(dhcpd[:index] + 'DHCPDARGS=%s' % ' '.join(dhcpdnics) + \
                        dhcpd[index + len(line):])
                f.close()

                retval, out, err = self.runCommand('/sbin/chkconfig dhcpd on')
                retval, out, err = self.runCommand('/etc/init.d/dhcpd restart')

                if retval == 0:
                    return True
                else:
                    return False

        else:
            return False
