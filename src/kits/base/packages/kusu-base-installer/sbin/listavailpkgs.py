#!/usr/bin/env python
#
# $Id$
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


class ListPkgApp(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)
        if os.getuid() != 0:
            self.errorMessage("nonroot_execution\n")
            sys.exit(-1)
            
        self.__db = KusuDB()
        self.ngname = None
        self.categorized = False
        
        try:
            self.__db.connect(user='apache', dbname='kusudb')
        except Exception,msg:
            sys.stderr.write('Problems establishing database connection. Error: %s' %msg)
            sys.exit(1)

        # setup the CL parser
        
        self.parser.add_option('-n', '--nodegroup', action="store", type="string", 
                               dest='ngname',  help="Node Group Name")
        self.parser.add_option('-c', '--categorized',  action="store_true", dest='categorized',
                               help="Retrieve categories/group info for packages")
        
    def printHelp(self):
        self.parser.print_help()

    def parse(self):
        
        (options, args) = self.parser.parse_args()

        if not options.ngname:
            self.stderrMessage('listavailpkgs: Node Group name must be specified.\n')
            sys.exit(1)
        else:
            self.ngname = options.ngname
                        
        if options.categorized:
            self.categorized = True
            
    def run(self):
        query = "select ngid from nodegroups where ngname = '%s'" % self.ngname
        self.__db.execute(query)
        ngid = self.__db.fetchone()
        
        try:
            pkgDict = getAvailPkgs(self.__db, ngid, self.categorized)
        except NodeGroupError,e:
            self.stderrMessage(str(e) + "\n")
            sys.exit(1)
        
        if not self.categorized:
            # pkgDict[letter] => package name
            self.stdoutMessage(self.__simplePkgList2XML(pkgDict))
        else:
            # pkgDict[category][group] => [package,package,...]         
            self.stdoutMessage(self.__categorizedPkgList2XML(pkgDict))
    
    
    def __simplePkgList2XML(self, pkgDict):
        doc = minidom.Document()
        root = doc.createElement("packages")
        
        for letter in sorted(pkgDict.keys()):
            for pkg in pkgDict[letter]:
                pkgEl = doc.createElement("package")
                pkgText = doc.createTextNode(pkg)
                pkgEl.appendChild(pkgText) 
                root.appendChild(pkgEl)
        
        doc.appendChild(root)
        return doc.toprettyxml()
    
    def __categorizedPkgList2XML(self, pkgDict):
        doc = minidom.Document()
        root = doc.createElement("categories")
        
        for category in sorted(pkgDict.keys()):
            catEl = doc.createElement("category")
            catEl.setAttribute("name", category)
            
            for group in sorted(pkgDict[category]):
                grpEl = doc.createElement("group")
                grpEl.setAttribute("name", group)
                
                for pkg in sorted(pkgDict[category][group]):
                    pkgEl = doc.createElement("package")
                    pkgText = doc.createTextNode(pkg)
                    pkgEl.appendChild(pkgText)
                    grpEl.appendChild(pkgEl)
                    
                catEl.appendChild(grpEl)
                
            root.appendChild(catEl)
            
        doc.appendChild(root)
        return doc.toprettyxml()
            


if __name__ == '__main__':
    app = ListPkgApp()
    app.parse()
    app.run()
