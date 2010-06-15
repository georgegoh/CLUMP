#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import sys
try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from path import path
from setup_errors import KusuProbePluginError
import message

GREP_ZONE_COMMAND = 'grep -P \'^ZONE\' '
GREP_UTC_COMMAND = 'grep -P \'^UTC\' '
TIMEZONE_FILE = '/etc/sysconfig/clock'

class TimezoneReceiver(object):

    def __init__(self, args=None):
        super(TimezoneReceiver, self).__init__()

    def probe_timezone(self):
        message.display("Probing for timezone settings")
        if not path(TIMEZONE_FILE).exists():
            raise KusuProbePluginError, "Kusu Installer failed to probe timezone."

        #Get the zone
        command = GREP_ZONE_COMMAND +  TIMEZONE_FILE
        run_cmd = subprocess.Popen(command, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        out, err = run_cmd.communicate()
        if out:
             try:
                 self._timezone = out.rstrip().split('=')[1]
             except Exception, msg:
                 raise KusuProbePluginError, "Kusu Installer failed to probe timezone zone. %s" % msg
        else:
            raise KusuProbePluginError, "Kusu Installer failed to probe timezone zone."


        #check if UTC is enabled
        command = GREP_UTC_COMMAND +  TIMEZONE_FILE
        run_cmd = subprocess.Popen(command, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        out, err = run_cmd.communicate()
        if out:
             try:
                 if  out.rstrip().split('=')[1] and out.rstrip().split('=')[1].lower() == 'true':
                    self._utc = 1 
                 else: 
                    self._utc = 0
             except Exception, msg:
                 raise KusuProbePluginError, "Kusu Installer failed to probe timezone utc. %s" % msg
        else:
            raise KusuProbePluginError, "Kusu Installer failed to probe timezone utc."

       
        message.success()
        return True 

    def get_time_zone(self):
        """ Interface to expose the timezone property """
        return {'zone': self._timezone, 'utc' : self._utc, 'ntp': 'pool.ntp.org'}

    timezone  = property(get_time_zone)

if __name__ == "__main__":
    time = TimezoneReceiver()
    time.probe_timezone()
    print time.timezone
