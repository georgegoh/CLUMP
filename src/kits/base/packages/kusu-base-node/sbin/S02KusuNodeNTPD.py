#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin

class KusuRC(Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'ntpd'
        self.desc = 'Setting client ntpd'
        self.ngtypes = ['compute']
        self.delete = True

    def run(self):
        etcntpconf = path('/etc/ntp.conf')

        if not etcntpconf.exists():
            etcntpconf.touch()

        conf = ['server\t\t%s' % self.niihost[0],
                '\nserver\t\t127.127.1.0 #local clock',
                '\nfudge\t\t127.127.1.0 stratum 10',
                '\ndriftfile\t/var/lib/ntp/drift',
                '\ndisable\t\tmonitor',
                '\nrestrict\t127.0.0.1 mask 255.255.255.255\n'
                ]

        f = open(etcntpconf, 'w')
        f.writelines(conf)
        f.close()

        retcode, out, err = self.runCommand('/sbin/chkconfig ntpd on')
        retcode, out, err = self.runCommand('/etc/init.d/ntpd restart')

        if retcode != 0:
            return False

        return True
