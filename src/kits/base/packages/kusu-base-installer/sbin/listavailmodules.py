#!/usr/bin/env python
#
# $Id: listavailmodules.py 3135 2009-10-23 05:42:58Z ltsai $
#
# List available packages to select for a node group
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import sys
import os
import string
from xml.dom import minidom

from kusu.ngedit.ngedit import *


class ListModuleApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)
        if os.getuid() != 0:
            self.errorMessage("nonroot_execution\n")
            sys.exit(-1)

        self.__db = KusuDB()
        self.ngname = None
        
        try:
            self.__db.connect(user='apache', dbname='kusudb')
        except Exception,msg:
            sys.stderr.write('Problems establishing database connection. Error: %s' %msg)
            sys.exit(1)

        # setup the CL parser
        
        self.parser.add_option('-n', '--nodegroup', action="store", type="string", 
                               dest='ngname',  help="Node Group Name")
        
    def printHelp(self):
        self.parser.print_help()

    def parse(self):
        
        (options, args) = self.parser.parse_args()

        if not options.ngname:
            self.stderrMessage('listavailmodules: Node Group name must be specified.\n')
            sys.exit(1)
        else:
            self.ngname = options.ngname
            
    def run(self):
        query = "select ngid from nodegroups where ngname = '%s'" % self.ngname
        self.__db.execute(query)
        ngid = self.__db.fetchone()

        if not ngid:
            self.errorMessage(self._("boothost_no_such_nodegroup") % (self.ngname) + "\n")
            sys.exit(1)

        try:
            modDict = getAvailModules(self.__db, ngid[0])
        except NodeGroupError,e:
            self.stderrMessage(str(e) + "\n")
            sys.exit(1)
            
        self.stdoutMessage(self.__moduleList2XML(modDict))
            
    def __moduleList2XML(self, modDict):
        doc = minidom.Document()
        root = doc.createElement("modules")
        
        for letter in sorted(modDict.keys()):
            for mod in modDict[letter]:
                modEl = doc.createElement("module")
                
                nameEl = doc.createElement("name")
                nameText = doc.createTextNode(mod['name'])
                nameEl.appendChild(nameText)
                
                descEl = doc.createElement("desc")
                descText = doc.createTextNode(mod['desc'])
                descEl.appendChild(descText)
                
                modEl.appendChild(nameEl)
                modEl.appendChild(descEl)
                
                root.appendChild(modEl)
        
        doc.appendChild(root)
        return doc.toprettyxml()            


if __name__ == '__main__':
    app = ListModuleApp()
    app.parse()
    app.run()
