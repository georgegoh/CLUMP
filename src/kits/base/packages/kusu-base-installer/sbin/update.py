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

from kusu.kusuapp import KusuApp
from kusu.kusudb import KusuDB
from kusu.cfms import PackBuilder
from kusu.cfmnet import CFMNet


class UpdateApp(KusuApp):
    def __init__(self, argv):
        KusuApp.__init__(self)


    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        self.stdoutMessage("Version %s\n", self.version)
        sys.exit(0)


    def toolHelp(self):
        """toolHelp - provide a help screen for this tool."""
        self.stdoutMessage("update_Help")
        sys.stdout.write('\n')
        sys.exit(0)


    def parseargs(self):
        """parseargs - Parse the command line arguments and populate the
        class variables"""
        
        self.parser.add_option("-n", "--nodegroup", action="store",
                               type="string", dest="nodegrp")
        self.parser.add_option("-f", "--files", action="store_true",
                               dest="updatefile", default=False)
        self.parser.add_option("-p", "--packages", action="store_true",
                               dest="updatepackages", default=False)
        self.parser.add_option("-v", "--version", action="store_true",
                               dest="wantver", default=False)

        (self.options, self.args) = self.parser.parse_args(sys.argv)

            

    def run(self):
        """run - Run the application"""
        self.parseargs()

        if self.options.wantver:
            # Print version
            self.toolVersion()
            sys.exit(0)

        if not self.options.updatefile and not self.options.updatepackages:
            self.toolHelp()
            
        pb = PackBuilder()
        pb.getNodegroups()

        if self.options.updatepackages:
            if self.options.nodegrp:
                # Only update a given nodegroup 
                pb.getPackageList()
            else:
                # Update all node groups
                pb.getPackageList(self.options.nodegrp)

        if self.options.updatefile:
            pb.updateCFMdir()
            
        pb.genFileList()



if __name__ == '__main__':
    app = UpdateApp(sys.argv)
    _ = app.langinit()
    app.run()
