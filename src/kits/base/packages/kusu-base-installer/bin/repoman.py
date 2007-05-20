#!/usr/bin/python
#
# $Id$
#
#   Copyright 2007 Platform Computing Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   The license is also available in the source code under the license
#   directory.
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#

import os
import sys
import string
from optparse import OptionParser
from ocs.ocsapp import OCSapp
from ocs.ocsdb import OCSDB

class RepoMan:
    """This class will provide the repository management functions"""

    def __init__(self):
        """__init__ - initializer for the class"""
        self.db = OCSDB()
        self.db.connect('ocsdb', 'apache')

        
    def snapshotRepo(self, reponame):
        """snapshotRepo - Create a copy of an existing repo.  Symbolic links
        will be copied as synbolic links, and real files will be copied as
        real files.  This is to support patching.  The database will be updated
        with the new snapshot."""
        pass


    def listRepoRevs(self, reponame):
        """listRepoRevs - Generate a list of the different revisons of a
        repository"""
        pass


    def deleteRepo(self, reponame):
        """deleteRepo - Delete the named repository, if it is not in use."""
        pass


    def patchRepo(self, reponame):
        """patchRepo - Patch the named repo."""
        pass


    def makeRepo(self, repomane):
        """makeRepo - Create a new repository"""
        pass


    def __validateRepo(self, reponame):
        """__validateRepo - Test the repository name to make sure it is valid.
        Returns:  True - when the node group exists, otherwise False."""
        pass


class RepomanApp(OCSapp):

    def __init__(self):
        OCSapp.__init__(self)


    def toolVersion(self):
        """toolVersion - provide a version screen for this tool."""
        global version
        self.errorMessage("Version %s\n", version)
        sys.exit(0)


    def toolHelp(self):
        """toolHelp - provide a help screen for this tool."""
        self.errorMessage("repoman_Help")
        sys.stderr.write('\n')
        sys.exit(0)


    def parseargs(self):
        """parseargs - Parse the command line arguments and populate the
        class variables"""
        
        self.parser.add_option("-n", "--newrepo", action="store",
                               type="string", dest="newrepo")
        self.parser.add_option("-p", "--patch", action="store",
                               type="string", dest="patchrepo")
        self.parser.add_option("-s", "--snapshot", action="store",
                               type="string", dest="snaprepo")
        self.parser.add_option("-d", "--delete", action="store",
                               type="string", dest="delrepo")
        self.parser.add_option("-l", "--listrev", action="store",
                               type="string", dest="listrepo")

        (self.options, self.args) = self.parser.parse_args(sys.argv)

            

    def run(self):
        """run - Run the application"""
        print sys.argv
        self.parseargs()

        repofun = RepoMan()
        if self.options.listrepo:
            repofun.listRepoRevs(self.options.listrepo)
        elif self.options.snaprepo:
            repofun.snapshotRepo(self.options.snaprepo)
        elif self.options.newrepo:
            repofun.makeRepo(self.options.newrepo)
        elif self.options.delrepo:
            repofun.deleteRepo(self.options.delrepo)
        elif self.options.patchrepo:
            repofun.patchRepo(self.options.patchrepo)
        else:
            print "What's up!"

        
if __name__ == '__main__':
    app = RepomanApp()
    app.run()
