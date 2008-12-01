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

        updated = False

        if self.os_name in ['sles', 'suse', 'opensuse']:
            # sles uses syslog-ng
            syslogngconf = '/etc/syslog-ng/syslog-ng.conf.in'

            lines = ['# Forward all log messages to master installer\n',
                     'destination loghost { udp("%s" port(514)); };\n' % self.niihost[0],
                     'log { source(src); destination(loghost); };\n']

            updated = self.appendLinesToFile(syslogngconf, lines)
            
            # sles need an extra step to call SuSEconfig to generate
            # the actual /etc/syslog-ng/syslog-ng.conf.
            if updated:
                retval = self.runCommand('/sbin/SuSEconfig --module syslog-ng')[0]
                if retval != 0:
                    # Somehow SuSEconfig is not able to generate the new syslog-ng.conf
                    return False

        else:
            # redhat and friends
            etcsyslogconf = '/etc/syslog.conf'

            lines = ['# Forward all log messages to master installer\n',
                     '*.*' + '\t' * 7 + '@%s\n' % self.niihost[0]]

            updated = self.appendLinesToFile(etcsyslogconf, lines)

        if updated:
            success, (out, retcode, err) = self.service('syslog', 'restart')
            if not success:
                raise Exception, err

        return True

    def appendLinesToFile(self, file, lines):
        if path(file).exists():
            conf_file = open(file, 'a')
            conf_file.writelines(lines)
            conf_file.flush()
            conf_file.close()
            return True
        else:
            # File does not exist
            return False
