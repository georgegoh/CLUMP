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
        self.delete = True

    def run(self):
        """Set up MySQL connection and SQLite collection, then migrate."""
             
        from kusu.core import database as db
        import sqlalchemy as sa

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
            
                # Set db.passwd permission correctly
                apache = pwd.getpwnam('apache')
                uid = apache[2]
                gid = apache[3]

                # Write new db.passwd
                import random
                import time
                r = random.Random(time.time())
                chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                password =  ''.join([r.choice(chars) for i in xrange(8)])

                p = path(os.environ.get('KUSU_ROOT', '/opt/kusu')) / 'etc' /  'db.passwd'
                f = open(p, 'w')
                f.write(password)
                f.close()

                p.chmod(0400)
                p.chown(uid, gid)

                # setup permission 
                permission = """
grant select,update,insert,delete,lock tables on kusudb.* to apache@localhost;
grant select,update,insert,delete,lock tables on kusudb.* to apache@'';
update mysql.user set password=password('%s') where user='apache';
grant select on kusudb.* to ''@localhost;
FLUSH PRIVILEGES;""" % password
                import tempfile
                tmpfile = tempfile.mkstemp()[1]
                os.chmod(tmpfile, 0600)
                os.chown(tmpfile, 0, 0)
                
                f = open(tmpfile, 'w')
                f.write(permission)
                f.close()
                self.runCommand('/usr/bin/mysql kusudb < ' + tmpfile)
                os.unlink(tmpfile)

                # chkconfig
                self.runCommand('/sbin/chkconfig mysqld on')

                # Clear all mappers and init them
                for key in sa.orm.mapper_registry.keys():
                    sa.orm.mapper_registry.pop(key)
                self.dbs = db.DB('mysql', 'kusudb', 'apache', password)

        return True
