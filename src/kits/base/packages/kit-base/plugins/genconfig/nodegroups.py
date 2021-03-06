# $Id$
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

from kusu.genconfig import Report
import sys
import psycopg2

class thisReport(Report):
    
    def toolHelp(self):
        """toolHelp - This method provides the help screen for this particular
        plugin.  All plugins must implement this method."""
        print self.gettext("genconfig_Nodegroups_Help")


    def runPlugin(self, pluginargs):
        """runPlugin - This method provides the database report for this
        plugin.  All plugins must implement this method."""

        if pluginargs and pluginargs[0] != '':
            query = ('select ngname from nodegroups where %s' % pluginargs[0])
        else:
            query = ('select ngname from nodegroups')
            
        try:
            self.db.execute(query)

        except psycopg2.ProgrammingError, e:
            sys.stderr.write(self.gettext("Error: Invalid optional SQL condition provided.\n\n"))
            self.toolHelp()
            sys.exit(-1)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n\n"))
            self.toolHelp()
            sys.exit(-1)

        else:            
            data = self.db.fetchall()
            if data:
                for row in data:
                    print "%s" % (row[0])
                
        
