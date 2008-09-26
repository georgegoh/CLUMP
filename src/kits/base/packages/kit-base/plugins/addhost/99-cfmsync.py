# Copyright (C) 2007-2008 Platform Computing Inc.

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
from kusu.addhost import *

class AddHostPlugin(AddHostPluginBase):
    def common(self):
        """Instruct the cfmsync to run after a node is added"""
        os.system('/opt/kusu/sbin/cfmsync -f')

    def updated(self):
        """Called when user runs 'addhost -u'"""
        self.common()

    def finished(self, nodelist, prePopulateMode):
        """Called when addhost exits"""
        self.common()
