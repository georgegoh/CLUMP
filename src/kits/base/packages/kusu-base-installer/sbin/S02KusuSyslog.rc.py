#!/usr/bin/env python
# $Id$
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
        self.name = 'syslog'
        self.desc = 'Setting up syslog'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Enable remote syslog logging"""

        updated = False

        if self.os_name in ['sles', 'suse', 'opensuse']:
            # sles uses syslog-ng. 
            # 1. Uncomment the appropriate line in
            #    syslog-ng.conf.in.
            # 2. Run "/sbin/SuSEconfig --module syslog-ng" to
            #    make it update /etc/syslog-ng/syslog-ng.conf.
            syslog_ng_conf = '/etc/syslog-ng/syslog-ng.conf.in'
            updated = self.replaceLineInFile('/etc/syslog-ng/syslog-ng.conf.in', 
                                             '#udp(ip("0.0.0.0") port(514));',
                                             'udp(ip("0.0.0.0") port(514));')

            if updated:
                retval = self.runCommand('/sbin/SuSEconfig --module syslog-ng')[0]
                if retval != 0:
                    # Somehow SuSEconfig is not able to generate the new syslog-ng.conf
                    return False

        else:
            # for rhel and friends
            updated = self.replaceLineInFile('/etc/sysconfig/syslog',
                                             'SYSLOGD_OPTIONS="-m 0"',
                                             'SYSLOGD_OPTIONS="-m 0 -r"')

        if updated:
            success, (out, retcode, err) = self.service('syslog', 'restart')
            if not success:
                raise Exception, err

        return True

    def replaceLineInFile(self, file, orig_line, new_line):
        if path(file).exists():
            f = open(file, 'r')
            conf_file = f.read()
            f.close()

            index = conf_file.find(orig_line)
            if index == -1:
                # Did not find the line. Abort.
                return False
            
            f = open(file, 'w')
            f.write(conf_file[:index] + new_line + conf_file[index+len(orig_line):])
            f.close()
            return True
        else:
            # Did not find the file.
            return False

