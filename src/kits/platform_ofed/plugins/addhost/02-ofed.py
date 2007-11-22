# $Id$
#
#  Copyright (C) 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

import sys
import subprocess
from kusu.addhost import AddHostPluginBase

class AddHostPlugin(AddHostPluginBase):
    def updated(self):
        p = subprocess.Popen("/bin/sed 's/alias ib[0-9] [_a-zA-Z0-9]*/ ib_uverbs ib_umad < /etc/modprobe.conf",
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err:
            subprocess.call("echo 'alias ib0 ib_ipoib ib_uverbs ib_umad' >> /etc/modprobe.conf",
                            shell=True)
        else:
            conf = open('/etc/modprobe.conf', 'w')
            conf.write(out)
            conf.close()
