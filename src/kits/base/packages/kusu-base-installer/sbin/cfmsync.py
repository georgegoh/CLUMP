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

UPDATEFILE    = 1
UPDATEPACKAGE = 2
FORCEFILES    = 4


import os
import sys
import string

from kusu.core.app import *
from kusu.core.db import KusuDB
from kusu.cfms import PackBuilder



class UpdateApp(KusuApp):
    def __init__(self, argv):
        KusuApp.__init__(self)


    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        self.stdoutMessage("Version %s\n", self.version)
        sys.exit(0)


    def toolHelp(self):
        """toolHelp - provide a help screen for this tool."""
        self.stdoutMessage("cfmsync_Help")
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
        ngid=0

        if self.options.wantver:
            # Print version
            self.toolVersion()
            sys.exit(0)

        if not self.options.updatefile and not self.options.updatepackages:
            self.toolHelp()

        if self.options.nodegrp:
            # Validate the node group name
            db = KusuDB()
            db.connect('kusudb', 'apache')
            query = ('select ngid from nodegroups where ngname="%s"' % self.options.nodegrp)
            try:
                db.execute(query)
                data = db.fetchone()
            except:
                self.stderrout("DB_Query_Error: %s\n", query)
                sys.exit(-1)

            if not data:
                self.stdoutMessage('cfmsync_invalid_node_group\n')
                sys.exit(-1)

            ngid = data[0]

        type = 0
        if self.options.updatefile:
            global UPDATEFILE
            type = type | UPDATEFILE
        if self.options.updatepackages:
            global UPDATEPACKAGE
            type = type | UPDATEPACKAGE
            
        pb = PackBuilder(self.errorMessage, self.stdoutMessage)

        if self.options.updatepackages:
            if os.path.exists(CFMCLIENT):
                cmd = "%s -t %i -i self" % (CFMCLIENT, UPDATEPACKAGE)
            else:
                cmd = "cfmclient -t %i -i self" % UPDATEPACKAGE
                
            if self.options.nodegrp:
                # Only update a given nodegroup 
                pb.getPackageList(self.options.nodegrp)
                if ngid == 1:
                    os.system(cmd)
            else:
                # Update all node groups
                pb.getPackageList()
                os.system(cmd)

        if self.options.updatefile:
            size = pb.updateCFMdir()
            if size:
                self.stdoutMessage("Distributing %i KBytes to all nodes.\n", (size / 1024))
            
        pb.genFileList()

        # Signal the nodes to start updating
        if self.options.nodegrp:
            pb.signalUpdate(type, self.options.nodegrp)
        else:
            pb.signalUpdate(type)


if __name__ == '__main__':
    app = UpdateApp(sys.argv)
    _ = app.langinit()
    app.run()
