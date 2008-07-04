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
        self.ngtypes = ['compute']
        self.delete = True

    def run(self):
        """Forward all log messages to master installer"""

        syslogFound = False
        rsylogFound = False

        if path('/etc/syslog.comf').exists():
            src = path('/etc/syslog.conf')
            syslogFound = True
        elif path('/etc/rsyslog.conf').exists():
            src = path('/etc/rsyslog.conf')
            rsyslogFound = True
        else:
            return False
 
        lines = ['# Forward all log messages to master installer\n',
                 '*.*' + '\t' * 7 + '@%s\n' % self.niihost[0]]

        syslog = open(src, 'a')
        syslog.writelines(lines)
        syslog.flush()
        syslog.close()

        if syslogFound:
            retval, out, err = self.runCommand('/etc/init.d/syslog restart')
        elif rsyslogFound:
            retval, out, err = self.runCommand('/etc/init.d/rsyslog restart')

        if retval == 0:
            return True
        else:
            return False
