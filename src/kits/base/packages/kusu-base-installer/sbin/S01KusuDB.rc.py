#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin 
from path import path
import os
import pwd

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'kusu db'
        self.desc = 'Setting up Kusu db'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Set up Main DB connection and SQLite collection, then migrate."""
             
        from kusu.core import database as db
        import sqlalchemy as sa
            


        if not path('/root/kusu.db').exists():
            return True
        engine = os.getenv('KUSU_DB_ENGINE')
        if engine == 'mysql':
            self.runCommand('/etc/init.d/mysqld start')
        else: # default this 
            engine = 'postgres'
            self.runCommand('/etc/init.d/postgresql stop') 
            pg_data_path = path('/var/lib/pgsql/data')
            pg_data_path.rmtree()
            self.runCommand("su -l postgres -c \'initdb --pgdata=/var/lib/pgsql/data >> /dev/null  2>&1\'")
            pg_log_path = pg_data_path / 'pg_log'
            pg_log_path.makedirs()
            self.runCommand('chown postgres:postgres %s' % pg_log_path)
            self.runCommand ('chmod go-rwx %s' % pg_log_path)
            self.runCommand('service postgresql start')

        # Clear all mappers and init them
        for key in sa.orm.mapper_registry.keys():
            sa.orm.mapper_registry.pop(key)

        sqliteDB = db.DB('sqlite', '/root/kusu.db')
        if engine == 'mysql':
            dbs = db.DB(engine, 'kusudb', 'root', entity_name='alt')
        else: #postgres only for now 
            dbs = db.DB(engine, 'kusudb', 'postgres', entity_name='alt')
            

        sqliteDB.copyTo(dbs)
        os.unlink('/root/kusu.db')
    
        # Set db.passwd permission correctly
        if self.os_name in ['suse', 'opensuse', 'sles']:
            wwwrun = pwd.getpwnam('wwwrun')
            uid = wwwrun[2]
            gid = wwwrun[3]
        else:
            apache = pwd.getpwnam('apache')
            uid = apache[2]
            gid = apache[3]

        # Write new db.passwd
        import random
        import time
        r = random.Random(time.time())
        chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        password =  ''.join([r.choice(chars) for i in xrange(8)])

        p = path(os.environ.get('KUSU_ROOT', '/opt/kusu')) / 'etc/db.passwd'
        f = open(p, 'w')
        f.write(password)
        f.close()

        p.chmod(0400)
        p.chown(uid, gid)

        # setup permission
        if engine == 'mysql':
            permission = """
grant select,update,insert,delete,lock tables on kusudb.* to apache@localhost;
grant select,update,insert,delete,lock tables on kusudb.* to apache@'';
update mysql.user set password=password('%s') where user='apache';
grant select on kusudb.* to ''@localhost;
FLUSH PRIVILEGES;""" % password
        else: #XXX postgres specific for now.
            permission = """
create role apache with login;
create role nobody with login;"""
            permission += "Grant all on table %s to apache;" \
                % ','.join(dbs.postgres_get_table_list())
            permission += "Grant all on table %s to apache;" \
                % ','.join(dbs.postgres_get_seq_list())
            permission += "Grant select on table %s to nobody;" \
                % ','.join(dbs.postgres_get_table_list())
            permission += "Grant select on table %s to nobody;" \
                % ','.join(dbs.postgres_get_seq_list())

        import tempfile
        tmpfile = tempfile.mkstemp()[1]
        os.chmod(tmpfile, 0600)
        os.chown(tmpfile, 0, 0)
        
        f = open(tmpfile, 'w')
        f.write(permission)
        f.close()
        if engine == 'mysql':
            self.runCommand('/usr/bin/mysql kusudb < ' + tmpfile)
        else:
            self.runCommand('/usr/bin/psql kusudb postgres < ' +tmpfile)
        os.unlink(tmpfile)

        # chkconfig
        if engine == 'mysql':
            self.runCommand('/sbin/chkconfig mysqld on')
        else: # XXX postgres only for now 
            self.runCommand('/sbin/chkconfig postgresql on')

        # Clear all mappers and init them
        for key in sa.orm.mapper_registry.keys():
            sa.orm.mapper_registry.pop(key)
        self.dbs = db.DB(engine, 'kusudb', 'apache', password)

        # Initialize repository for compute and installer nodes
        repoid = self.dbs.Repos.select()[0].repoid

        ngs = self.dbs.NodeGroups.select()
        for ng in ngs:
            if ng.ngname == 'unmanaged':
                continue

            ng.repoid = repoid
            ng.save()
            ng.flush()

        return True
