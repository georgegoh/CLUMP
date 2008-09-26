#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'dhcpd'
        self.desc = 'Setting up dhcpd'
        self.ngtypes = ['installer']
        self.delete = True

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
                dhcpd = f.readlines()
                f.close()

                argline = -1
                for x in xrange(len(dhcpd)):
                    # returns 0 when string begins with find term
                    if not dhcpd[x].find('DHCPDARGS='):
                        argline = x
                        break

                # we haven't found the line, so append it at the end
                if argline == -1:
                    dhcpd.append('')

                dhcpd[argline] = 'DHCPDARGS="%s"\n' % ' '.join(dhcpdnics)

                f = open('/etc/sysconfig/dhcpd', 'w')
                f.writelines(dhcpd)
                f.close()

                retval, out, err = self.runCommand('/sbin/chkconfig dhcpd on')
                retval, out, err = self.runCommand('/etc/init.d/dhcpd restart')

                if retval == 0:
                    return True
                else:
                    return False

        else:
            return False
