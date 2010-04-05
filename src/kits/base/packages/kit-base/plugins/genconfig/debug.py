# $Id: debug.py 3135 2009-10-23 05:42:58Z ltsai $
#
#   Copyright 2007 Platform Computing Inc
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
from kusu.genconfig import Report

class thisReport(Report):

    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print self.gettext("genconfig_Debug_Help")


    def runPlugin(self, pluginargs):
        """runPlugin - This method provides the database report for this
        plugin.  All plugins must implement this method."""
        engine = os.getenv("KUSU_DB_ENGINE")
        if engine == 'mysql':
            os.system('mysqldump kusudb')
        elif engine == 'postgres':
            os.system('pg_dump -Unobody kusudb')
        else:
            print('Unknown engine - %s.  Giving up .. ' % engine)

            

                
        
