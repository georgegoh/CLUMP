import os
import pwd
import time
import random
import subprocess
import sqlalchemy
from path import path
from ConfigParser import ConfigParser
# KUSU imports
from kusu.service import check
from kusu.service.exceptions import ExceptionInfo
from kusu.service.exceptions import InstallConfMissingException
from kusu.service.exceptions import InstallConfParseException
from kusu.service.exceptions import InvalidConfException
from kusu.service.exceptions import PrerequisiteCheckFailedException
from kusu.boot.distro import DistroFactory
import kusu.core.database as kusudb
from primitive.system.software import probe
from primitive.system.software.dispatcher import Dispatcher


def genPasswordToFile(user, passfile):
    """ Generates a file containing a random password, setting it to
        the uid and gid of the specified user. 
        
        Returns the password generated.
    """
    passwd = genRandomStr()
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


def genRandomStr():
    """ Returns a pseudo-random 8-digit string. """
    r = random.Random(time.time())
    chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    password = ''.join([r.choice(chars) for i in xrange(8)])
    return password


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


def createPostgresDb(prime_db_script, pg_passwd):
    """ Create and initialise the postgres database."""
    sqlalchemy.orm.mapper_registry.clear()
    db = kusudb.DB('postgres', 'kusudb', 'postgres')
    db.createDatabase()
    db.createTables()
    db.flush()
    db = None

    # run primedb script.
    cmd = 'psql kusudb postgres'
    env = os.environ
    env['PGPASSWORD'] = pg_passwd
    p = subprocess.Popen(cmd.split(), env=env, shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    f = open(prime_db_script, 'r')
    s = f.read()
    f.close()
    out, err = p.communicate(s)

    # grant permissions.
    db = kusudb.DB('postgres', 'kusudb', 'postgres')
    db.postgres_update_sequences(db.postgres_get_seq_list())


class InstallService(object):
    def verify(self, conf):
        """ Verify a config file given its path.
        """
        config = self.parseConfig(conf)
        valid, missing_sections, missing_options = self.verifyConfigParser(config)
        if not valid:
            msgs = [ExceptionInfo(title='Missing Required Config Settings',
                                  msg='Headers: '+str(missing_sections)+
                                      ', Options: '+str(missing_options))]
            raise InvalidConfException(exception_msgs=msgs)
        failures = self.prerequisiteChecks(config)
        if failures:
            raise PrerequisiteCheckFailedException(failures)


    def install(self, conf):
        """ Perform an installation given a path to a config file.
        """
        config = self.parseConfig(conf)
        valid, missing_sections, missing_options = self.verifyConfigParser(config)
        if not valid:
            msgs = [ExceptionInfo(title='Missing Required Config Settings',
                                  msg='Headers: '+str(missing_sections)+
                                      ', Options: '+str(missing_options))]
            raise InvalidConfException(exception_msgs=msgs)
        # Actual installation starts here
        failures = self.prerequisiteChecks(config)
        if failures:
            raise PrerequisiteCheckFailedException(failures)
        self._setupPaths(config)
        self._setupNetwork(config)
#        self._setupDB(config)
#        self._bootstrapDB(config)
        self._createRepo(config)
        self._addKits(config)
        self._refreshRepo(config)


    def parseConfig(self, conf):
        """ Parses a given path to a config file(.INI format).
            Returns a ConfigParser object.
            Raises InstallConfMissingException, InstallConfParseException
        """
        if not path(conf).exists():
            msgs = [ExceptionInfo(title='Config file missing',
                                  msg='Config file "%s" not found' % str(conf))]
            raise InstallConfMissingException(exception_msgs=msgs)
        try:
            cp = ConfigParser()
            cp.read(conf)
        except Exception, e:
            msgs = [ExceptionInfo(title='Error Parsing Install Config',
                                  msg=str(e))]
            raise InstallConfParseException(exception_msgs=msgs)
        return cp


    def verifyConfigParser(self, config):
        """ Verify a ConfigParser-type object according to rules."""
        required_config = {'Media':['os'],
                           'Provision':['device', 'ip', 'netmask'],
                           'Disk':['kusu', 'depot', 'home'],
                           'Kits':[]}
        valid = True
        missing_sections = []
        missing_options = []
        # ensure that each required section exists in the given config.
        for section in required_config.keys():
            if not config.has_section(section):
                missing_sections.append(section)
                valid = False
            # ensure that each required option exists in the section.
            for option in required_config[section]:
                if not config.has_option(section, option):
                    missing_options.append(section + '::' + option)
                    valid = False
        return (valid, missing_sections, missing_options)


    def prerequisiteChecks(self, config):
        """ Prerequisite checks that must pass before installation
            can proceed.
            A list of ExceptionInfo objects(containing details of
            failed checks) is returned. This list can be empty if
            no checks fail.
        """
        failed_checks = []

        # OS / media matches. Failure if cannot detect distro for media,
        # else if media distro does not match native distro.
        media_loc = config.get('Media', 'os')
        failed_checks.extend(check.Media.getFailures(media_loc))

        # SELinux is off
        if probe.getSelinuxStatus():
            failed_checks.append(ExceptionInfo(title='SELinux enabled',
                                               msg='SELinux should be disabled'))

        # Provision nic available
        provision = {}
        for tup in config.items('Provision'):
            provision[tup[0]] = tup[1]
        failed_checks.extend(check.Provision.getFailures(provision))

        # Disk requirements
        disk = {}
        for tup in config.items('Disk'):
            disk[tup[0]] = tup[1]
        failed_checks.extend(check.Disk.getFailures(disk))

        return failed_checks


    def _setupPaths(self, config):
        """ Set up paths for kusu installation.
        """
        self.KUSU_ROOT = path(config.get('Disk', 'kusu'))
        self.DEPOT_ROOT = path(config.get('Disk', 'depot'))
        for p in [self.KUSU_ROOT, self.DEPOT_ROOT]:
            if not p.exists():
                p.makedirs()


    def _setupNetwork(self, config):
        pass


    def _setupDB(self, config):
        """ Set up the Postgres DB. """
        # stop postgres service.
        psql_name = Dispatcher.get('postgres_server')
        psql_stop_cmd = Dispatcher.get('service_stop') % psql_name
        subprocess.call(psql_stop_cmd.split())

        pg_data_path = path('/var/lib/pgsql/data')
#        if pg_data_path.exists():
#            pg_data_path.rmtree()
#        pg_data_path.makedirs()

        # get the password and write it to a file.
        pwfile = '%s/etc/pgdb.passwd' % self.KUSU_ROOT
        pg_passwd = genPasswordToFile('postgres', pwfile)
        psql_init_cmd = 'su -l postgres -c \'initdb --pgdata=/var/lib/pgsql/data ' + \
                        '--auth=md5 --pwfile=%s\'' % pwfile
        subprocess.call(psql_init_cmd.split())

        # set up the host-based authentication.
        modifyHBAConf(pg_data_path / 'pg_hba.conf')

        # set up permissions for the log file.
        pg_log_path = pg_data_path / 'pg_log'
        if not pg_log_path.exists():
            pg_log_path.makedirs()
        chown_psql_log_cmd = 'chown postgres:postgres %s' % pg_log_path
        subprocess.call(chown_psql_log_cmd.split())
        chmod_psql_log_cmd = 'chown go-rwx %s' % pg_log_path
        subprocess.call(chmod_psql_log_cmd.split())

        # start the service again.
        psql_start_cmd = Dispatcher.get('service_start') % psql_name
        subprocess.call(psql_stop_cmd.split())
        createPostgresDb('/opt/kusu/sql/psql_kusu_primedb.sql', pg_passwd)


    def _bootstrapDB(self, config):
        pass


    def _createRepo(self, config):
        pass


    def _addKits(self, config):
        pass


    def _refreshRepo(self, config):
        pass
