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

from kusu.core.app import *
from kusu.core.db import KusuDB
from kusu.cfms import PackBuilder, UPDATEFILE, UPDATEPACKAGE, FORCEFILES, UPDATEREPO

class UpdateApp(KusuApp):
    def __init__(self, argv):
        KusuApp.__init__(self)


    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        self.stdoutMessage("kusu-cfmsync version %s\n", self.version)
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
        self.parser.add_option("-u", "--repoupdate", action="store_true",
                               dest="updaterepo", default=False)
        self.parser.add_option("-v", "--version", action="store_true",
                               dest="wantver", default=False)

        (self.options, self.args) = self.parser.parse_args(sys.argv)


    def getActionDesc(self):
        return "Synchronizing nodegroup(s)"

    def run(self):
        """run - Run the application"""
        self.parseargs()
        ngid=0
        ngname=None

        # Check if root user
        if os.geteuid():
            print self._("nonroot_execution\n")
            sys.exit(-1)

        if self.options.wantver:
            # Print version
            self.toolVersion()
            sys.exit(0)

        if not self.options.updatefile and not self.options.updatepackages and not self.options.updaterepo:
            self.toolHelp()

        # Test Db connection
        db = KusuDB()
        try:
            db.connect('kusudb', 'apache')
        except:
            self.logErrorEvent(self._("DB_Query_Error"))            
            sys.exit(-1)
            
        if self.options.nodegrp:
            # Validate the node group name
            query = ('select ngid,ngname from nodegroups where ngname="%s"' % self.options.nodegrp)
            try:
                db.execute(query)
                data = db.fetchone()
            except:
                self.logErrorEvent(self._("DB_Query_Error: %s") % query)
                sys.exit(-1)

            if not data:
                self.logErrorEvent(self._('cfmsync_invalid_node_group'))
                sys.exit(-1)

            ngid = data[0]
            ngname = data[1]

        type = 0
        if self.options.updatefile:
            type = type | UPDATEFILE
        if self.options.updatepackages:
            type = type | UPDATEPACKAGE
        if self.options.updaterepo:
            type = type | UPDATEREPO
        
        if ngid == 0:
            msg = self._("cfmsync_event_start_sync_all")
        else:
            msg = self._("cfmsync_event_start_sync_ng") % ngname
            
        self.logEvent(msg, toStdout=False)

        pb = PackBuilder(self.errorMessage, self.stdoutMessage)
        # Update the installer and setup sync actions for other nodegroup(s)
        pb.consolidatedSync(action_type=type, ngname=self.options.nodegrp, ngid=ngid)

        # Reinitialize the PackBuilder instance in case kusu db
        # is restarted due to an upgrade of the RPMs. Otherwise
        # pb will be holding on to a broken db connection.
        pb = PackBuilder(self.errorMessage, self.stdoutMessage)

        # Signal the nodes to start updating
        pb.signalUpdate(type, ngname)

        if ngid == 0:
            msg = self._("cfmsync_event_finish_sync_all")
        else:
            msg = self._("cfmsync_event_finish_sync_ng") % ngname
            
        self.logEvent(msg, toStdout=False)


if __name__ == '__main__':
    app = UpdateApp(sys.argv)
    _ = app.langinit()
        
    app.run()
