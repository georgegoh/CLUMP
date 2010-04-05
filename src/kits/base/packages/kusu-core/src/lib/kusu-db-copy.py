#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: kusu-db-copy.py 3528 2010-02-19 11:27:24Z ankit $
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import sys

try:
    import subprocess
except:
    from popen5 import subprocess

from path import path
from kusu.core.app import KusuApp
from kusu.core.database import DB
from optparse import OptionParser

class DbCopyApp(KusuApp):
    
    def __init__(self):

        KusuApp.__init__(self)
        usage = """kusu-db-copy [-h | --help]
                           [-v | --version]
                           [-d | --database] <path-to-database-file>

        for example:
            kusu-db-copy -d /root/sqlite.db
        """
        usage = self._(usage)
        self.parser = OptionParser(usage)
        self.parser.add_option('-v', '--version', dest='version', action="store_true", help=self._('Display version of tool')) 
        self.parser.add_option('-d', '--database', dest='database', help="Target database file")
        engine = os.getenv('KUSU_DB_ENGINE')
        if engine == 'mysql':
            dbdriver = 'mysql'
        else:
            dbdriver = 'postgres'
        
        try: 
            self.db = DB(dbdriver, db='kusudb', username='apache')
        except:
            # Crude assumption, can't setup DB means not installer node
            self.stdoutMessage('You can only run this tool on installer node')
            sys.exit(1)
         

    def getVersion(self):
        self.stdoutMessage('kusu-db-copy version %s\n', self.version)
        sys.exit(0)

    def run(self):
       
        (options, args)= self.parser.parse_args()

        if options.version:
            self.getVersion()

        if options.database:
            dirname = path(options.database).dirname()
            if dirname and not path(dirname).exists():
                path(dirname).makedirs()
                
            ##sqlite_db = DB('postgres', options.database, username='postgres', entity_name='alt')
            sqlite_db = DB('sqlite', options.database, entity_name='alt')
            self.db.copyTo(sqlite_db)
        
        return 0           

if __name__ == "__main__":
    if os.getuid() != 0:
        print 'You must be root to run this tool'
        sys.exit(1)

    sys.exit(DbCopyApp().run())
