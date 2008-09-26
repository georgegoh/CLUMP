# Copyright (C) 2008 Platform Computing Inc.

# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import os
import snack
from kusu.ngedit.ngedit import NGEPluginBase

class NGPlugin(NGEPluginBase):
    name= 'Base Installer plugin screen #2'
    msg = 'This is a non-interactive component plugin'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.setHelpLine("Help Line for base-installer component's plugin screen")

    def add(self):
        assert(self.ngid)
        os.system("touch /tmp/KuSu_%s_add" %self.ngid)

    def remove(self):
        assert(self.ngid)
        if os.path.exists("/tmp/KuSu_%s_add" %self.ngid):
            os.remove("/tmp/KuSu_%s_add" %self.ngid)
            #os.system("rm /tmp/KuSu_%s_add" %self.ngid)
