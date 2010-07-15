#!/usr/bin/python
#
# $Id$
#
#  Copyright (C) 2007 Platform Computing
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
from kusu.core.app import KusuApp
from kusu.buildimage import BuildImage
from kusu.util.errors import BuildImageException, YumFailedToRunError, BuildImageError

class BuildImageApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        global version
        self.stdoutMessage("kusu-buildimage version %s\n", self.version)
        sys.exit(0)


    def toolHelp(self):
        """toolHelp - provide a help screen for this tool."""
        self.stdoutMessage("buildimage_Help")
        sys.stdout.write('\n')
        sys.exit(0)


    def parseargs(self):
        """parseargs - Parse the command line arguments and populate the
        class variables"""

        self.parser.add_option("-n", "--nodegroup", action="store",
                               type="string", dest="nodegrp")
        self.parser.add_option("-i", "--image", action="store",
                               type="string", dest="image")
        self.parser.add_option("-d", "--database", action="store",
                               type="string", dest="database")
        self.parser.add_option("-u", "--user", action="store",
                               type="string", dest="user")
        self.parser.add_option("-p", "--password", action="store",
                               type="string", dest="password")
        self.parser.add_option("-v", "--version", action="store_true",
                               dest="wantver", default=False)

        (self.options, self.args) = self.parser.parse_args(sys.argv)


    def run(self):
        """run - Run the application"""

        self.parseargs()
        image = ''

        # Check if root user
        if os.geteuid():
            print self._("nonroot_execution\n")
            sys.exit(-1)

        if self.options.wantver:
            # Print version
            self.toolVersion()
            sys.exit(0)

        imgfun = BuildImage()
        imgfun.setTextMeths(self.errorMessage, self.stdoutMessage)

        # Do we need a new database connection?
        if self.options.database or self.options.user or self.options.password :
            if self.options.database == '' or self.options.user == '' or self.options.password == '':
                self.errorMessage("genconfig_provide_database_user_password\n")
                sys.exit(-1)

            imgfun.altDb(self.options.database, self.options.user, self.options.password)

        if self.options.image:
            image = self.options.image

        if self.options.nodegrp:
            # Generate the node group
            try:
                imgfun.makeImage(self.options.nodegrp, image)
            except BuildImageException, e:
                self.stderrMessage("%s" % e)
                sys.exit(0)
            except (BuildImageError, YumFailedToRunError), e:
                self.stderrMessage('Error: %s' % e)
                sys.exit(-1)
        else:
            # Missing node group name
            self.stdoutMessage('buildimage_need_a_node_group\n')
            sys.exit(-1)


if __name__ == '__main__':
    app = BuildImageApp()
    app.run()
