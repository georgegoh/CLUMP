import os
import pwd
import time
import random
import subprocess
from path import path
from kusu.service.exceptions import ExceptionInfo
from kusu.service.exceptions import DBSetupFailedException
import primitive.svctool.commands as svctool
from primitive.system.software.dispatcher import Dispatcher


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
