#!/usr/bin/env python
# $Id: S02KusuNodeSyslog.rc.py 2101 2007-08-22 10:18:52Z ltsai $
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
        etcsyslogconf = path('/etc/syslog.conf')

        lines = ['# Forward all log messages to master installer\n',
                 '*.*' + '\t' * 7 + '@%s\n' % self.niihost[0]]

        syslog = open(etcsyslogconf, 'a')
        syslog.writelines(lines)
        syslog.flush()
        syslog.close()

        retval, out, err = self.runCommand('/etc/init.d/syslog restart')

        if retval == 0:
            return True
        else:
            return False
