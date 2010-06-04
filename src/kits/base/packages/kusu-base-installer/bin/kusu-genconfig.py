#!/usr/bin/python
#
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

from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
from kusu.genconfig import Report


class DbReportApp(KusuApp):
    def __init__(self, argv):
        KusuApp.__init__(self)
        self.args       = argv
        self.ngrepo = ''

    def toolVersion(self):
        """ 
        toolVersion()
        Prints out the version of the tool to screen. 
        """

        print "kusu-genconfig version %s" % self.version
        sys.exit(0)

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
                self.toolVersion()
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
                elif args[i] == '-r':
                    self.action = 'rname'
                    if len(args) > (i+1):
                        self.ngrepo = args[i+1]
                    else:
                        toolinst.toolHelp()
                elif args[i] == '-n':
                    self.action = 'ngname'
                    if len(args) > (i+1):
                        self.ngrepo = args[i+1]
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
        elif self.action == 'rname':
            dbrinst.setRepoPlugins(self.ngrepo)
        elif self.action == 'ngname':
            dbrinst.setNGPlugins(self.ngrepo)

        if self.plugin == '':
            dbrinst.toolHelp()
            sys.exit(1)
        else:
            if os.getuid() != 0:
                sys.stderr.write('You need to be root to run genconfig plugins.\n')
                sys.exit(1)

            # Validate the plugin
            for p in dbrinst.plugins:
                pname = os.path.join(p, '%s.py' % self.plugin)
                if os.access(pname, os.R_OK) == 0:
                    self.errorMessage("genconfig_cannot_find_plugin: %s\n", self.plugin)
                    sys.exit(-1)
                if os.path.isfile(pname):
                    sys.path.append(p)

        # Do we need a new database connection?
        if self.database != '' or self.user != '' or self.password != '':
            if self.database == '' or self.user == '' or self.password == '':
                self.errorMessage("genconfig_provide_database_user_password\n")
                sys.exit(-1)
                
            dbrinst.altDb(self.database, self.user, self.password)

        # Need to instanciate the plugin and run what is needed there
        dbrinst.run(self.plugin, self.action, self.pluginargs)

        
if __name__ == '__main__':
    app = DbReportApp(sys.argv)
    _ = app.langinit()
    app.run()
