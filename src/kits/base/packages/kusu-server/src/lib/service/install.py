import os
import tempfile
import subprocess
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
from kusu.kitops.kitops import KitOps
from primitive.system.software import probe


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
        db = db_helper.setupDB(config, self.KUSU_ROOT)
        self._addBaseKit(config, db)
        oskid = self._addOSKit(config, db)
        self._addKits(config, db)
        self._createRepo(config)
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



    def _createRepo(self, config):
        pass


    def _addBaseKit(self, config, db):
        pass


    def _addOSKit(self, config, db):
        """ Add the OS kit that corresponds to the master's OS. """
        ko = KitOps(db=db)
        media_loc = config.get('Media', 'os')
        ko.setKitMedia(media_loc)
        kits = ko.addKitPrepare()
        kit = ko.prepareOSKit(kits)
        kitpath = ko.copyOSKitMedia(kit)
        ko.setKitMedia('')
        ko.makeContribDir(kit)
        ko.finalizeOSKit(kit)
        return kit['kid']


    def _addKits(self, config, db):
        pass


    def _refreshRepo(self, config):
        pass
