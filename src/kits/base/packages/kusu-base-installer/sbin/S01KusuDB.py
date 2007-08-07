#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core.plugin import Plugin
from path import path
import os
import pwd

class KusuRC(Plugin):

    def __init__(self):
        Plugin.__init__(self)
        self.name = 'kusu db'
        self.desc = 'Setting up Kusu db'
        self.ngtypes = ['installer']

    def run(self):
        """Set up MySQL connection and SQLite collection, then migrate."""
             
        from kusu.core import database as db
        import sqlalchemy as sa

        # Start mysql server

        retcode = self.runCommand('/etc/init.d/mysqld status')[0]
        if retcode != 0:
            retcode, out, err = self.runCommand('/etc/init.d/mysqld start')
            if retcode != 0:
                return False

            # Migrate db
            if path('/root/kusu.db').exists():
                # Clear all mappers and init them
                for key in sa.orm.mapper_registry.keys():
                    sa.orm.mapper_registry.pop(key)

                sqliteDB = db.DB('sqlite', '/root/kusu.db')
                dbs = db.DB('mysql', 'kusudb', 'root', entity_name='alt')

                sqliteDB.copyTo(dbs)
                os.unlink('/root/kusu.db')
            
                # Clear all mappers and init them
                for key in sa.orm.mapper_registry.keys():
                    sa.orm.mapper_registry.pop(key)
                self.dbs = db.DB('mysql', 'kusudb', 'apache', None)

                # Set db.passwd permission correctly
                apache = pwd.getpwnam('apache')
                uid = apache[2]
                gid = apache[3]

                p = path(os.environ.get('KUSU_ROOT', '/opt/kusu')) / 'etc' /  'db.passwd'
                p.chmod(0400)
                p.chown(uid, gid)

                # setup permission 
                self.runCommand('/usr/bin/mysql kusudb < $KUSU_ROOT/sql/kusu_dbperms.sql')

                # chkconfig
                self.runCommand('/sbin/chkconfig mysqld on')

        return True
