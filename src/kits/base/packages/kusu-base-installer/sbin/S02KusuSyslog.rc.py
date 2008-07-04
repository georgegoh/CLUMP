#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin
from path import path

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'syslog'
        self.desc = 'Setting up syslog'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Enable remote syslog logging"""
       
        syslogFound = False
        rsylogFound = False

        if path('/etc/sysconfig/syslog').exists():
            src = path('/etc/sysconfig/syslog')
            syslogFound = True
        elif path('/etc/sysconfig/rsyslog').exists():
            src = path('/etc/sysconfig/rsyslog')
            rsyslogFound = True
        else:
            return False
 
        f = open(src, 'r')
        syslog = f.read()
        f.close()

        line = 'SYSLOGD_OPTIONS="-m 0"'
        index = syslog.find(line)

        f = open(src, 'w')
        f.write(syslog[:index] + 'SYSLOGD_OPTIONS="-m 0 -r"' + syslog[index+len(line):])
        f.close()

        if syslogFound:
            retval, out, err = self.runCommand('/etc/init.d/syslog restart')
        elif rsyslogFound:
            retval, out, err = self.runCommand('/etc/init.d/rsyslog restart')

        if retval == 0:
            return True
        else:
            return False
