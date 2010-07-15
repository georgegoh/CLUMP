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

from operator import itemgetter
from setup_errors import KusuProbePluginError
from diskspacecheckreceiver import convert_to_megabytes

GREP_COMMAND = 'grep -P '
PROC_MEMINFO = '/proc/meminfo'

class RamCheckReceiver(object):

    def get_ram_size(self):
        """
            Returns the amount of RAM in the system.
        """
        grep_command = GREP_COMMAND + '^MemTotal\s*:' + ' %s' % PROC_MEMINFO
        run_cmd = subprocess.Popen(grep_command, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        out, err = run_cmd.communicate()
        host_memsize = 0
        if out:
             host_memsize = convert_to_megabytes(out.split()[1], out.split()[2])
        else:
            raise KusuProbePluginError, "Not able to detect amount of RAM in system."

        return host_memsize

    ramSize = property(get_ram_size)


if __name__ == "__main__":
    mem = RAMCheckReceiver()
    mem.run()

