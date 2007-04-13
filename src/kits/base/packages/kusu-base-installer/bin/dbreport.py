#!/usr/bin/python
#
# $Id$
#
#   Copyright 2007 Platform Computing Corporation
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

from kusu.kusuapp import KusuApp
from kusu.kusudb import KusuDB

PLUGINS='/opt/kusu/lib/plugins/dbreport'

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
    


class DbReportApp(KusuApp):
    def __init__(self, argv):
        self.args       = argv
        

    def parseargs(self, toolinst):
        """parseargs - Parse the command line arguments and populate the
        class variables"""
        self.user       = ''
        self.password   = ''
        self.database   = ''
        self.pluginargs = []
        self.plugin     = ''
        self.action     = 'run'   # This will be [help|run]
        
        args = self.args[1:]
        i = 0
        while i < len(args):
            if args[i] == '-v':
                toolinst.toolVersion()
            elif args[i] == '-h':
                self.action = 'help'
            else:
                if args[i] == '-d':
                    if len(args) > (i+1):
                        self.database = args[i+1]
                    else:
                        toolinst.toolHelp()
                elif args[i] == '-u':
                    if len(args) > (i+1):
                        self.user = args[i+1]
                    else:
                        toolinst.toolHelp()
                elif args[i] == '-p':
                    if len(args) > (i+1):
                        self.password = args[i+1]
                    else:
                        toolinst.toolHelp()
                else:
                    # Must be the plugin
                    self.plugin = args[i]
                    if len(args) > (i+1):
                        self.pluginargs = args[i+1:]
                    break
                i = i + 1
            i = i + 1
            

    def run(self):
        """run - Run the application"""
        dbrinst = Report(self.gettext)
        self.parseargs(dbrinst)
        # print "Action     = %s" % self.action
        # print "Database   = %s" % self.database
        # print "User       = %s" % self.user
        # print "Password   = %s" % self.password
        # print "Plugin     = %s" % self.plugin
        # print "Pluginargs = %s" % self.pluginargs

        if self.action == 'help':
            if self.plugin == '':
                dbrinst.toolHelp()
                sys.exit(0)

        if self.plugin == '':
            dbrinst.toolHelp()
            sys.exit(1)
        else:
            # Validate the plugin
            global PLUGINS
            sys.path.append(PLUGINS)
            pname = os.path.join(PLUGINS, '%s.py' % self.plugin)
        
            if os.access(pname, os.R_OK) == 0:
                self.errorMessage("dbreport_cannot_find_plugin: %s\n", self.plugin)
                sys.exit(-1)

        # Do we need a new database connection?
        if self.database != '' or self.user != '' or self.password != '':
            if self.database == '' or self.user == '' or self.password == '':
                self.errorMessage("dbreport_provide_database_user_password\n")
                sys.exit(-1)
                
            dbrinst.altDb(self.database, self.user, self.password)
            
        # Need to instanciate the plugin and run what is needed there
        dbrinst.run(self.plugin, self.action, self.pluginargs)

        
if __name__ == '__main__':
    app = DbReportApp(sys.argv)
    _ = app.langinit()
    app.run()
