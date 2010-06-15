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
        if self.appglobals['InstallerServeDHCP'] == '0':
            self.desc = 'Disabling dhcpd'
        else:
            self.desc = 'Setting up dhcpd'

        self.ngtypes = ['installer']
        self.delete = True

        self.interfaceKey = "DHCPDARGS"
        if self.os_name in ["sles", "opensuse", "suse"]:
            self.interfaceKey = "DHCPD_INTERFACE"

    def run(self):
    
        if self.appglobals['InstallerServeDHCP'] == '0':
            success, (out, retcode, err) = self.service('dhcpd', 'stop')
               
            success, (out, retcode, err) = self.service('dhcpd', 'disable')

            return True

        if path('/etc/dhcpd.conf').exists():
            retval = self.runCommand('$KUSU_ROOT/bin/kusu-genconfig dhcpd > /etc/dhcpd.conf')[0]
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
                    if not dhcpd[x].find('%s=' % self.interfaceKey):
                        argline = x
                        break

                # we haven't found the line, so append it at the end
                if argline == -1:
                    dhcpd.append('')

                dhcpd[argline] = '%s="%s"\n' % (self.interfaceKey, ' '.join(dhcpdnics))

                f = open('/etc/sysconfig/dhcpd', 'w')
                f.writelines(dhcpd)
                f.close()

                success, (out, retcode, err) = self.service('dhcpd', 'restart')
                if not success:
                    raise Exception, err
                   
                success, (out, retcode, err) = self.service('dhcpd', 'enable')
                if not success:
                    raise Exception, err

                return True
                    
        else:
            return False

