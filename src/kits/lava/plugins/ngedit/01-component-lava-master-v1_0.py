# Copyright (C) 2007 Platform Computing Inc
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

import os
import snack
from kusu.ngedit.ngedit import NGEPluginBase

class NGPlugin(NGEPluginBase):
    name= 'Lava NGEdit Plugin'
    msg = 'This is a non-interactive component plugin'

    def __init__(self, database, kusuApp=None, gridWidth=45):
        NGEPluginBase.__init__(self, database, kusuApp=kusuApp, gridWidth=gridWidth)
        self.database = database
        self.setHelpLine("Lava Kit")

    def add(self):
        assert(self.ngid)
	query = ('select ngname from nodegroups where ngid = %s' % self.ngid)
	try:
	    self.database.execute(query)
	    ngname = self.database.fetchone()
	except:
            return
   
	os.system('mkdir -p \"/etc/cfm/%s/opt/lava/conf\"' % ngname)

    def remove(self):
        assert(self.ngid)
        query = ('select ngname from nodegroups where ngid = %s' % self.ngid)
        try:
            self.database.execute(query)
            ngname = self.database.fetchone()
        except:
            return

        os.system('rm -rf \"/etc/cfm/%s/opt/lava/conf\"' % ngname)
