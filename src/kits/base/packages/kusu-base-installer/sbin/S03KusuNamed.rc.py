#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
from kusu.ipfun import getArpaZone
from primitive.system.software.dispatcher import Dispatcher

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'named'
        self.desc = 'Setting up named'
        self.ngtypes = ['installer']
        self.delete = True
        self.named_dir = Dispatcher.get('named_dir')

    def run(self):

        row = self.dbs.AppGlobals.select_by(kname = 'InstallerServeDNS')[0]

        if row.kvalue == '1':
            domain = self.dbs.AppGlobals.select_by(kname = 'DNSZone')[0].kvalue
           
            self.runCommand('/opt/kusu/bin/kusu-genconfig named > /etc/named.conf')
            self.runCommand('/opt/kusu/bin/kusu-genconfig zone > %s/%s.zone' % (self.named_dir, domain))

            updated_nets = []
            for net in self.dbs.Networks.select():
                if not net.usingdhcp and net.type != 'public' and net.network not in updated_nets:
                    arpazone, classnet = getArpaZone(net.network, net.subnet)
                    self.runCommand('/opt/kusu/bin/kusu-genconfig reverse %s > %s/%s.rev' % (net.network, self.named_dir, net.network))
                    updated_nets.append(net.network)

            success, (out, retcode, err) = self.service('named', 'start')
            if not success:
                raise Exception, err
               
            success, (out, retcode, err) = self.service('named', 'enable')
            if not success:
                raise Exception, err

        return True

