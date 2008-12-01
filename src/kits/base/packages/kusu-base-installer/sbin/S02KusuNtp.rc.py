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

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'ntpd'
        self.desc = 'Setting up ntpd'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        if path('/etc/ntp.conf').exists():
        
            ntp_server = Dispatcher.get('ntp_server')

            success, (retcode, out, err) = self.service(ntp_server, 'start')
            if not success:
                raise Exception, err
            success, (retcode, out, err) = self.service(ntp_server, 'enable')
            if not success:
                raise Exception, err

            return True
