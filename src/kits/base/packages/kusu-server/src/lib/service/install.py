import os
import socket
import tempfile
import subprocess
import sqlalchemy as sa
from path import path
from ConfigParser import ConfigParser
# KUSU imports
from kusu.service import check
from kusu.service import db_helper
from kusu.service.exceptions import ExceptionInfo
from kusu.service.exceptions import InstallConfMissingException
from kusu.service.exceptions import InstallConfParseException
from kusu.service.exceptions import InvalidConfException
from kusu.service.exceptions import PrerequisiteCheckFailedException
from kusu.boot.distro import DistroFactory
import kusu.core.database as kusudb
from primitive.system.software import probe
from primitive.system.software.dispatcher import Dispatcher

DEFAULT_DNS_DOMAIN='kusu'
DEFAULT_NTP_SERVER='pool.ntp.org'


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
        self._setupDB(config)
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
        HOME = path(config.get('Disk', 'home'))
        for p in [self.KUSU_ROOT, self.DEPOT_ROOT, HOME]:
            if not p.exists():
                p.makedirs()


    def _setupNetwork(self, config):
        pass


    def _setupDB(self, config):
        """ Set up the Postgres DB. """
        # stop postgres service.
        db_helper.stopPostgresSvc()

        pg_data_path = path('/var/lib/pgsql/data')
        if pg_data_path.exists():
            pg_data_path.rmtree()

        # self.KUSU_ROOT initialised in _setupPaths()
        pwfile = '%s/etc/pgdb.passwd' % self.KUSU_ROOT
        pg_passwd = db_helper.genPostgresPasswd(pwfile, pg_data_path)

        # create the log directory.
        pg_log_path = pg_data_path / 'pg_log'
        pg_log_path.makedirs()

        # set up the host-based authentication.
        db_helper.modifyHBAConf(pg_data_path / 'pg_hba.conf')

        # set up ownership and permissions for the log directory.
        chown_psql_log_cmd = 'chown postgres:postgres %s' % pg_log_path
        subprocess.call(chown_psql_log_cmd.split())
        chmod_psql_log_cmd = 'chmod go-rwx %s' % pg_log_path
        subprocess.call(chmod_psql_log_cmd.split())

        # start the service again.
        db_helper.startPostgresSvc()

        # clear all mappers and init them.
        sa.orm.mapper_registry.clear()
        dbs = kusudb.DB('postgres', 'kusudb', 'postgres', pg_passwd)

        # This was where migration from sqlite took place.
        self._bootstrapDB(config, dbs)

        # add apache user to password file.
        appuser = Dispatcher.get('webserver_usergroup')[0]
        pwfile = '%s/etc/db.passwd' % self.KUSU_ROOT
        appuser_pw = db_helper.genPasswdToFile(appuser, pwfile)

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
        db_helper.enablePostgresSvc()

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


    def _bootstrapDB(self, config, db_obj):
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
 
        # get provision DNS domain.
        domain = DEFAULT_DNS_DOMAIN
        if config.has_option('Provision', 'domain'):
            domain = config.get('Provision', 'domain')
        
        # get timezone/utc.
        try:
            (tz, utc) = probe.getTimezone()
        except Exception, e:
            failures.append(ExceptionInfo(title='Cannot get timezone/UTC',
                                msg=str(e)))

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


    def _createRepo(self, config):
        pass


    def _addKits(self, config):
        pass


    def _refreshRepo(self, config):
        pass
