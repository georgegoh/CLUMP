#!/usr/bin/env python
# $Id: S02KusuDHCPD.rc.py 2101 2007-08-22 10:18:52Z ltsai $
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
        self.name = 'named'
        self.desc = 'Setting up named'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):

        row = self.dbs.AppGlobals.select_by(kname = 'InstallerServeDNS')[0]

        if row.kvalue == '1':
            domain = self.dbs.AppGlobals.select_by(kname = 'DNSZone')[0]
           
            self.runCommand('/opt/kusu/bin/genconfig named > /etc/named.conf')
            self.runCommand('/opt/kusu/bin/genconfig zone > /var/named/%s.zone' % domain)

            for net in self.dbs.Networks.select():
                self.runCommand('/opt/kusu/bin/genconfig reverse %s > /var/named/%s.rev' % (net.network,net.network))

            self.runCommand('/etc/init.d/named start')
            self.runCommand('/sbin/chkconfig named on')
            
        return True
