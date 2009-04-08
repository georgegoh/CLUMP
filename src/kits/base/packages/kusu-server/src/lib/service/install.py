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
from primitive.system.software import probe

class InstallService(object):
    def install(self, conf):
        """ Perform an installation given a path to a config file.
        """
        config = self.parseConfig(conf)
        valid, missing_sections, missing_options = self.verifyConfig(config)
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
        self._bootstrapDB(config)
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


    def verifyConfig(self, config):
        """ Verify a ConfigParser-type object according to rules."""
        valid = True
        missing_sections = []
        missing_options = []
        for section in ['Media', 'Provision', 'Disk', 'Kits']:
            if not config.has_section(section):
                missing_sections.append(section)
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
        failed_checks.extend(check.Disk.getFailures())

        return failed_checks


    def _setupPaths(self, config):
        pass


    def _setupNetwork(self, config):
        pass


    def _bootstrapDB(self, config):
        pass


    def _createRepo(self, config):
        pass


    def _addKits(self, config):
        pass


    def _refreshRepo(self, config):
        pass
