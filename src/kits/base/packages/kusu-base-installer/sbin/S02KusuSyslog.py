#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'syslog'
        self.desc = 'Setting up syslog'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Enable remote syslog logging"""
        
        f = open('/etc/sysconfig/syslog', 'r')
        syslog = f.read()
        f.close()

        line = 'SYSLOGD_OPTIONS="-m 0"'
        index = syslog.find(line)
        
        f = open('/etc/sysconfig/syslog', 'w')
        f.write(syslog[:index] + 'SYSLOGD_OPTIONS="-m 0 -r"' + syslog[index+len(line):])
        f.close()

        retval, out, err = self.runCommand('/etc/init.d/syslog restart')

        if retval == 0:
            return True
        else:
            return False
