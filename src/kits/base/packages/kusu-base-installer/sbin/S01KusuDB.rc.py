#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin
from kusu.util.errors import CommandFailedToRunError
from path import path
from primitive.system.software.dispatcher import Dispatcher
import os
import pwd
import time
try:
    import subprocess
except:
    from popen5 import subprocess

DB_CONNECTION_TIMEOUT = 60 # seconds to wait for valid DB connection

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'kusu db'
        self.desc = 'Setting up Kusu db'
        self.ngtypes = ['installer']
        self.delete = True
        self.__postgres_passfile = '/opt/kusu/etc/pgdb.passwd'

    def __genpasswd(self):
        import random
        r = random.Random(time.time())
        chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        password = ''.join([r.choice(chars) for i in xrange(8)])
        return password

    def __writePassword(self,user,passfile):
        """get the password and write it to a file."""
        passwd = self.__genpasswd()
        # obtain security details of the file.
        userinfo = pwd.getpwnam(user)
        if not userinfo:
            return None
        uid = userinfo[2]
        gid = userinfo[3]
        f = open(passfile, 'w')
        f.write(passwd)
        f.close()
        os.chmod(passfile, 0400)
        os.chown(passfile, uid, gid)
        return passwd

    def __modifyHBAConf(self):
        """ Places modifications to HBA.conf and saves the settings """
        pg_hba = path ('/var/lib/pgsql/data/pg_hba.conf')
        token_str='%s\t%s\t%s\t%s\t%s\n'
        f = open(pg_hba,'r')
        hba_lines = f.readlines()
        f.close()
        kusu_lines = []
        kusu_lines.append("#Appended by Kusu\n")
        kusu_lines.append(token_str % ('local','kusudb','nobody','','trust'))
        kusu_lines.append(token_str % ('host','kusudb','nobody','127.0.0.1/32','trust'))
        kusu_lines.append(token_str % ('host','kusudb','nobody','::1/128','trust'))
        kusu_lines.append("#End of Kusu Edit\n")
        kusu_lines.extend(hba_lines)
        f = open(pg_hba,'w')
        f.writelines(kusu_lines)
        f.close()

    def __tuneParameters(self):
        """ PostgreSQL server tuning for postgreSQL server scalability."""
        # increase max_connections and shared_buffer.
        self.runCommand("/bin/sed -i -e '/max_connections \= /c\max_connections \= 2000' /var/lib/pgsql/data/postgresql.conf")
        self.runCommand("/bin/sed -i -e '/shared_buffers \= /c\shared_buffers \= 32768' /var/lib/pgsql/data/postgresql.conf")
        # change kernel parameters accordingly.
        self.runCommand("/bin/echo \"kernel.sem = 250 400000 32 2000\" >> /etc/sysctl.conf")
        self.runCommand("/sbin/sysctl -p /etc/sysctl.conf")
        

    def run(self):
        """Set up Main DB connection and SQLite collection, then migrate."""

        from kusu.core import database as db
        import sqlalchemy as sa

        if not path('/root/kusu.db').exists():
            return True
        engine = os.getenv('KUSU_DB_ENGINE')

        mysql_svc = Dispatcher.get('mysql_server')
        postgresql_svc = Dispatcher.get('postgres_server')

        if engine == 'mysql':


            success, (out,retcode,err) = self.service(mysql_svc, 'start')
            if not success:
                raise Exception, err

        else: # default this

            engine = 'postgres'
            success, (out,retcode,err) = self.service(postgresql_svc, 'status')
            # retcode will be 0 if postgresql service is already running.
            if retcode == 0:
                success, (out,retcode,err) = self.service(postgresql_svc, 'stop')
                if not success:
                    raise Exception, err
            pg_data_path = path('/var/lib/pgsql/data')

            if pg_data_path.exists():
                pg_data_path.rmtree()
            # get the password and write it to a file.
            pwfile = "%s/etc/pgdb.passwd" % (os.environ.get('KUSU_ROOT', '/opt/kusu'))
            pg_passwd = self.__writePassword('postgres', pwfile)

            self.runCommand("su -l postgres -c \'initdb --pgdata=/var/lib/pgsql/data --auth=md5 --pwfile=%s>> /dev/null  2>&1\'" % pwfile)

            pg_log_path = pg_data_path / 'pg_log'
            pg_log_path.makedirs()
            self.__modifyHBAConf()
            self.__tuneParameters()
            self.runCommand('chown postgres:postgres %s' % pg_log_path)
            self.runCommand ('chmod go-rwx %s' % pg_log_path)
            success, (out,retcode,err) = self.service(postgresql_svc, 'start')
            if not success:
                raise Exception, err

        # Clear all mappers and init them
        for key in sa.orm.mapper_registry.keys():
            sa.orm.mapper_registry.pop(key)

        sqliteDB = db.DB('sqlite', '/root/kusu.db')
        if engine == 'mysql':
            dbs = db.DB(engine, 'kusudb', 'root', entity_name='alt')
        else: #postgres only for now
            dbs = db.DB(engine, 'kusudb', 'postgres', entity_name='alt')

        # Let's make sure the DB is ready for us
        if not wait_for_DB_connection(dbs, DB_CONNECTION_TIMEOUT):
            print "FATAL: DB unavailable! After DB issues are resolved,"
            print "run `service kusu start` to complete installation and configuration"
            raise CommandFailedToRunError, "DB unavailable, do not run further KUSU RC scripts"

        sqliteDB.copyTo(dbs)
        # Keep orig kusu.db for debugging purpose but rename
        # it so that it does not confuse kusurc scripts.
        path('/root/kusu.db').rename('/root/kusu-orig.db')

        appuser = Dispatcher.get('webserver_usergroup')[0]
        # Set db.passwd permission correctly


        pwfile = "%s/etc/db.passwd" % (os.environ.get('KUSU_ROOT', '/opt/kusu'))
        password = self.__writePassword(appuser, pwfile)

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
create role apache with login PASSWORD '%s';
create role nobody with login;"""
            permission = permission % password
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
            cmd = '/usr/bin/psql kusudb postgres < ' +tmpfile
            env = os.environ.copy()
            env['PGPASSWORD'] = pg_passwd
            p = subprocess.Popen(cmd,
                                 env=env,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()

        os.unlink(tmpfile)

        # chkconfig
        if engine == 'mysql':
            success, (out,retcode,err) = self.service(mysql_svc, 'enable')
            if not success:
                raise Exception, err
        else: # XXX postgres only for now
            success, (out,retcode,err) = self.service(postgresql_svc, 'enable')
            if not success:
                raise Exception, err


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

def wait_for_DB_connection(db, timeout):
    """Check the DB connection every 2 seconds for max timeout seconds.

    Returns True if the connection is OK, False if the timeout has expired."""

    for x in range(timeout / 2):
        if db.is_connection_valid():
            return True
        time.sleep(2)

    # Timeout
    return False
