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

import os
import sys
import string

from kusuapp import KusuApp
from kusudb import KusuDB

PLUGINS='/opt/kusu/lib/plugins/genconfig'

class Report:
    """This class will be used to generate various configuration files
    for applications and services on the installer and on other nodes."""
    
    def __init__(self, gettext):
        """__init__  - Initializer for the Report class.  For internationalization
        it must be passed the gettext object"""
        self.user     = 'nobody'
        self.database = 'kusudb'
        self.password = ''
        self.gettext  = gettext


    def toolHelp(self):
        """toolHelp - This method will provide the help for each of the
        plugins.  Each plugin must override this method."""
        msg = self.gettext("dbreport_Help")
        print msg
        global PLUGINS
        dirlist = os.listdir(PLUGINS)
        for file in dirlist:
            if file[-3:] == '.py' and file[0:2] != '__':
                print "%s\t" % file[:-3],
        print ""
        sys.exit(0)


    def runPlugin(self, pluginargs):
        """runPlugin - Each plugin will impliment this method.  This is what does
        the real work"""
        pass


    def run(self, plugin, action, pargs):
        """run - This method is responsible for calling the appropriate interface
        from the plugin"""
    
        exec "from " + plugin + " import *"
        pinst = thisReport(self.gettext)
        if action == 'help':
            pinst.toolHelp()

        else:
            # Get a database connection for the plugin to use
            pinst.db = KusuDB()
            pinst.db.connect(self.database, self.user, self.password)
            
            # Run the plugin
            pinst.runPlugin(pargs)  


    def altDb(self, database, user, password):
        """altDb - Change the database user, password and database"""
        self.database = database
        self.user = user
        self.password = password
    
