#!/usr/bin/python -u
#
# $Id$
#
# List components, or list components with interactive plug-ins
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import sys
import os
import string
import glob
from kusu.core.app import KusuApp
from kusu.core.db import KusuDB
from kusu.ngedit.ngedit import NGEPluginBase

PluginsDir = "/opt/kusu/lib/plugins/ngedit"

class ListComps(KusuApp):

    def __init__(self):
        KusuApp.__init__(self)

        self.__db = KusuDB()
        self.reponame = None
        self.interactive = False
        
        try:
            self.__db.connect(user='apache', dbname='kusudb')
        except Exception,msg:
            sys.stderr.write('Problems establishing database connection. Error: %s' %msg)
            sys.exit(1)

        # setup the CL parser
        
        self.parser.add_option('-r', '--reponame',  action="store", type="string", dest='reponame',
                               help="Repository to retrieve components from")
        self.parser.add_option('-i', '--interactive',  action="store_true", dest='interactive',
                               help="Retrieve list of components with interactive plugins")
        
    def printHelp(self):
        self.parser.print_help()

    def parse(self):
        
        (options, args) = self.parser.parse_args()

        if options.reponame:
            self.reponame = options.reponame

        if options.interactive:
            self.interactive = True

        if self.reponame == None:
            sys.stderr.write("Repository name is required.\n")
            sys.exit(1)
            
    def run(self):
        self.__printComps(self.__db, self.reponame, self.interactive)
    
        
    def __printComps(self, db, reponame, interactive=False):

        query = "select c.cname" + \
                " from repos r, repos_have_kits rhk, kits k, components c" + \
                " where r.reponame='%s' and r.repoid=rhk.repoid" % reponame + \
                      " and rhk.kid=k.kid and k.kid=c.kid and r.ostype=c.os;"

        db.execute(query)
        rv = db.fetchall()
        CompNameList = [x for x, in rv]
        CompNameList.sort()

        for comp in CompNameList:
            if interactive:
               if self.__compHasInteractivePlugin(db, comp):
                  print comp
            else:
               print comp

    def __compHasInteractivePlugin(self, db, comp):

        plugdir = PluginsDir

        if plugdir not in sys.path:
            sys.path.append(plugdir)

        flist = glob.glob('%s/*-%s.py' % (PluginsDir, comp))
        for plugfile in flist:
            
            plugmname = os.path.splitext(os.path.basename(plugfile))[0]
            plugminst = __import__(plugmname)
            plugcname = getattr(plugminst, 'NGPlugin')
            if not issubclass(plugcname, NGEPluginBase):
                raise NGECommitError, 'Invalid NG Plugin Screen class encountered: %s' %plugcname

            plugcinst = plugcname(db, KusuApp())
            if plugcinst.isInteractive():
                return True


if __name__ == '__main__':
    if os.geteuid() != 0:
        print "listcomps: only root can run this administrative tool."
        sys.exit(1)

    app = ListComps()
    app.parse()
    app.run()
