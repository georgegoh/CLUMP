#!/usr/bin/env python
# $Id: S03KusuNodeNTPD.rc.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
from kusu.core import rcplugin
from primitive.system.software.dispatcher import Dispatcher

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'ntpd'
        self.desc = 'Setting client ntpd'
        self.ngtypes = ['compute', 'compute-imaged', 'compute-diskless']
        self.delete = True

    def run(self):
        etcntpconf = path('/etc/ntp.conf')

        if not etcntpconf.exists():
            etcntpconf.touch()

        conf = ['server\t\t%s' % self.niihost[0],
                '\n# server\t\t127.127.1.0 #local clock',
                '\n# fudge\t\t127.127.1.0 stratum 10',
                '\ndriftfile\t/var/lib/ntp/drift',
                '\ndisable\t\tmonitor',
                '\nrestrict\t127.0.0.1 mask 255.255.255.255\n'
                ]

        f = open(etcntpconf, 'w')
        f.writelines(conf)
        f.close()

        ntp_server = Dispatcher.get('ntp_server')

        success, (retcode, out, err) = self.service(ntp_server, 'restart')
        if not success:
            raise Exception, err
        success, (retcode, out, err) = self.service(ntp_server, 'enable')
        if not success:
            raise Exception, err

        return True
