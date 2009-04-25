import os
import pwd
import time
import random
import socket
import subprocess
from path import path
import sqlalchemy as sa
import kusu.core.database as kusudb
from kusu.service.exceptions import ExceptionInfo
from kusu.service.exceptions import DBSetupFailedException
import primitive.svctool.commands as svctool
from primitive.system.software import probe
from primitive.system.software.dispatcher import Dispatcher

DEFAULT_DNS_DOMAIN='kusu'
DEFAULT_NTP_SERVER='pool.ntp.org'

def modifyHBAConf(conf):
    pg_hba = path(conf)
    token_str = '%s\t%s\t%s\t%s\t%s\n'
    hba_lines = []
    if pg_hba.exists():
        f = pg_hba.open('r')
        hba_lines = f.readlines()
        f.close()

    kusu_lines = []
    kusu_lines.append('# Start of Kusu config\n')
    kusu_lines.append(token_str % ('local','kusudb','nobody','','trust'))
    kusu_lines.append(token_str % ('host','kusudb','nobody','127.0.0.1/32','trust'))
    kusu_lines.append(token_str % ('host','kusudb','nobody','::1/128','trust'))
    kusu_lines.append('# End of Kusu config\n')
    kusu_lines.extend(hba_lines)
    f = pg_hba.open('w')
    f.writelines(kusu_lines)
    f.close()


############
### Services
############
def startPostgresSvc():
    """ Start the postgres service. """
    try:
        psql_name = Dispatcher.get('postgres_server')
        success, (out,retcode,err) = svctool.SvcStartCommand(service=psql_name).execute()
    except Exception, e:
        raise DBSetupFailedException(e
                [ExceptionInfo(title='Failed to start Postgres server', msg=str(e))])
    if not success:
        raise DBSetupFailedException( 
            [ExceptionInfo(title='Failed to start Postgres server', msg=err)])


def stopPostgresSvc():
    """ Stop the postgres service. """
    try:
        psql_name = Dispatcher.get('postgres_server')
        success, (out,retcode,err) = svctool.SvcStatusCommand(service=psql_name).execute()
        # retcode will be 0 if postgres service is already running.
        if not retcode:
            success, (out,retcode,err) = svctool.SvcStopCommand(service=psql_name).execute()
    except Exception, e:
        raise DBSetupFailedException(
            [ExceptionInfo(title='Failed to stop Postgres server', msg=str(e))])
    if not success:
        raise DBSetupFailedException(
            [ExceptionInfo(title='Failed to stop Postgres server', msg=err)])


def enablePostgresSvc():
    """ Enable the postgres service to run on boot up(chkconfig on). """
    try:
        psql_name = Dispatcher.get('postgres_server')
        success, (out,retcode,err) = svctool.SvcEnableCommand(service=psql_name).execute()
    except Exception, e:
            raise DBSetupFailedException(
                [ExceptionInfo(title='Failed to enable Postgres server on boot', msg=str(e))])
    if not success:
        raise DBSetupFailedException(
            [ExceptionInfo(title='Failed to enable Postgres server on boot', msg=err)])


######################
### Password functions
######################

def genRandomStr():
    """ Returns a pseudo-random 8-digit string. """
    r = random.Random(time.time())
    chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    password = ''.join([r.choice(chars) for i in xrange(8)])
    return password


def genPasswdToFile(user, passfile, randomStrGen=genRandomStr):
    """ Generates a file containing a random password, setting it to
        the uid and gid of the specified user. 
        
        Returns the password generated.
    """
    passwd = randomStrGen()
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


def genPostgresPasswd(pwfile, pgdata):
    """ Get the postgres password and write it to a file(%kusu_root%/etc/pgdb.passwd).
        The postgres authentication is decoupled from unix auth. 
        There are directives in hba conf that let you say , if its a local access, 
        on all db, trust a user . The user in this context is the postgres user, 
        so you can say "all local users are allowed to login using the account nobody". 
        conversly you can say "all local users are authenticated by some auth 
        mechanism". The md5 mechanism is more secure than the password mechanism 
        in this way because password sends the password unencrypted. 
        The reason the postgres user needs a password is because I dont think 
        there is (or I dont know) how to tie local user credentials with postgres access 
        credentials. IE , There is no straightforward mechanism to say, local 
        root user can login as user postgres to all db without password. Or Local postgres user.
        So we need the postgres password 
    """
    pg_passwd = genPasswdToFile('postgres', pwfile, genRandomStr)
    psql_init_cmd = ['su', '-l', 'postgres', '-c', 'initdb --pgdata=%s --auth=md5 --pwfile=%s' % (pgdata, pwfile)]
    subprocess.call(psql_init_cmd)
    return pg_passwd


############################
### Database setup functions
############################

def bootstrapDB(config, db_obj):
    """ Bootstrap the DB with initial values. Assumes clean install. """
    db_obj.createDatabase()
    db_obj.bootstrap()

    # get public DNS zone.
    fqhname = socket.gethostname()
    try:
        hostname, public_zone = fqhname.split('.', 1)
    except ValueError:
        # nothing to split.
        hostname = fqhname
        public_zone = ''

    # bootstrap defaults the master node name to 'master'. Use the
    # existing hostname.
    master = db_obj.Nodes.selectfirst_by(name='master')
    master.name = hostname
    master.save()
    master.flush()

    # get provision DNS domain.
    domain = DEFAULT_DNS_DOMAIN
    if config.has_option('Provision', 'domain'):
        domain = config.get('Provision', 'domain')
        
    # get timezone/utc.
    try:
        (tz, utc) = probe.getTimezone()
        if utc:
            utc = '1'
        else:
            utc = '0'
    except Exception, e:
        utc = '0'

    # get keyboard.
    try:
        keyb = probe.getKeyboard()
    except:
        # default to us.
        keyb = 'us'

    # get language.
    try:
        lang = os.environ['LANG']
    except:
        # default to en_US.
        lang = 'en_US.UTF-8'

    # get NTP server.
    ntp_server = DEFAULT_NTP_SERVER
    if config.has_option('Provision', 'ntp_server'):
        domain = config.get('Provision', 'ntp_server')

    db_obj.AppGlobals(kname='DNSZone', kvalue=domain).save()
    db_obj.AppGlobals(kname='PublicDNSZone', kvalue=public_zone).save()
    db_obj.AppGlobals(kname='Language', kvalue=lang).save()
    db_obj.AppGlobals(kname='Keyboard', kvalue=keyb).save()
    db_obj.AppGlobals(kname='PrimaryInstaller', kvalue=hostname).save()
    db_obj.AppGlobals(kname='Timezone_zone', kvalue=tz).save()
    db_obj.AppGlobals(kname='Timezone_utc', kvalue=utc).save()
    db_obj.AppGlobals(kname='Timezone_ntp_server', kvalue=ntp_server).save()
    db_obj.flush()


def setupDB(config, kusu_root):
    """ Set up the Postgres DB. """
    # stop postgres service.
    stopPostgresSvc()

    pg_data_path = path('/var/lib/pgsql/data')
    if pg_data_path.exists():
        pg_data_path.rmtree()

    # generate password for postgres user.
    pwfile = '%s/etc/pgdb.passwd' % kusu_root
    pg_passwd = genPostgresPasswd(pwfile, pg_data_path)

    # create the log directory.
    pg_log_path = pg_data_path / 'pg_log'
    pg_log_path.makedirs()

    # set up the host-based authentication.
    modifyHBAConf(pg_data_path / 'pg_hba.conf')

    # set up ownership and permissions for the log directory.
    chown_psql_log_cmd = 'chown postgres:postgres %s' % pg_log_path
    subprocess.call(chown_psql_log_cmd.split())
    chmod_psql_log_cmd = 'chmod go-rwx %s' % pg_log_path
    subprocess.call(chmod_psql_log_cmd.split())

    # start the service again.
    startPostgresSvc()

    # clear all mappers and init them.
    sa.orm.mapper_registry.clear()
    dbs = kusudb.DB('postgres', 'kusudb', 'postgres', pg_passwd)

    # This was where migration from sqlite took place.
    bootstrapDB(config, dbs)

    # add apache user to password file.
    appuser = Dispatcher.get('webserver_usergroup')[0]
    pwfile = '%s/etc/db.passwd' % kusu_root
    appuser_pw = genPasswdToFile(appuser, pwfile)

    # set up permissions.
    permission = """
create role apache with login PASSWORD '%s';
create role nobody with login;"""
    permission = permission % appuser_pw
    permission += "Grant all on table %s to apache;" % \
                  ','.join(dbs.postgres_get_table_list())
    permission += "Grant all on table %s to apache;" % \
                  ','.join(dbs.postgres_get_seq_list())
    permission += "Grant select on table %s to nobody;" % \
                  ','.join(dbs.postgres_get_table_list())
    permission += "Grant select on table %s to nobody;" % \
                  ','.join(dbs.postgres_get_seq_list())
    env = os.environ.copy()
    env['PGPASSWORD'] = pg_passwd
    p = subprocess.Popen(['/usr/bin/psql', 'kusudb', 'postgres'],
                         env=env,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (out,err) = p.communicate(permission)

    # chkconfig on postgres.
    enablePostgresSvc()

    # clear all mappers and init them.
    sa.orm.mapper_registry.clear()
    dbs = kusudb.DB('postgres', 'kusudb', 'apache', appuser_pw)

    # initialise repository for compute and installer nodes.
    repoid = dbs.Repos.select()[0].repoid
    ngs = [ng for ng in dbs.NodeGroups.select() if ng.ngname != 'unmanaged']
    for ng in ngs:
        ng.repoid = repoid
        ng.save()
        ng.flush()            
    dbs.flush()
    return dbs
