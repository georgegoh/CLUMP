#!/usr/bin/env python
#
# Kusu SQL injector
#
# Copyright (C) 2007 Platform Computing Inc.

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

# Author: Shawn Starr <sstarr@platform.com>

import os
import sys
import string
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB

class SQLInjectorApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

    def toolVersion(self, option, opt, value, parser):
        """ Prints out the version of the tool to screen.  """

        print "SQL Injector Version %s\n" % self.version
        sys.exit(0)

    def parseargs(self):
        """ Parse the command line arguments. """

        self.parser.add_option("-v", "--version", action="callback",
                                callback=self.toolVersion)
        self.parser.add_option("-q", "--query", action="store",
                                type="string", dest="querystring")

        (self._options, self._args) = self.parser.parse_args(sys.argv[1:])

    def run(self):
        """ Run the application """

        # Check if root user
        if os.geteuid():
           print self._("nonroot_execution\n")
           sys.exit(-1)

        self.db = KusuDB()
        # Parse command options
        self.parseargs()

        # Handle -q option
        if self._options.querystring:
           try:
               self.db.connect('kusudb', 'apache')
           except:
               print self._("DB_Query_Error\n")

           self.db.execute(self._options.querystring)
           try:
               results = self.db.fetchall()
               for row in results:
                   line = [str(item) for item in row]
                   print '|'.join(line)
           except:
               pass

if __name__ == '__main__':
    app = SQLInjectorApp()
    app.run()
