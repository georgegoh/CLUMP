#!/usr/bin/env python
# Copyright (C) 2007 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import subprocess
from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):
    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'ulimit'
        self.desc = 'Increasing ulimit memlock'
        self.ngtypes = ['compute']
        self.delete = False

    def getTotalMem(self):
        p = subprocess.Popen("cat /proc/meminfo | grep 'MemTotal:' | awk '{ print $2 }'",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if not out:
            raise Exception, "Cannot find total memory size in system."
        print out
        total_mem = out.strip()
        return long(total_mem)

    def run(self):
        p = subprocess.Popen("ulimit -l %ld && service sshd restart" % self.getTotalMem(),
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err:
            raise Exception, "Couldn't set new limit for memlock."
        subprocess.call("modprobe ib_ipoib; modprobe ib_uverbs; modprobe ib_umad", shell=True)
        return True
