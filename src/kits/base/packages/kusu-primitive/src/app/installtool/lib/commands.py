#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
''' InstallTool is used to generate output based on SLES autoinst.xml or 
    RHEL kickstart-ks.cfg formats based on inputs as specified in UBI-7.
'''
import os
import urlparse
from Cheetah.Template import Template
from primitive.core.command import Command
from primitive.core.command import CommandFailException
from primitive.core.errors import CommandMissingArgsError
from primitive.core.errors import AutoInstallConfigNotCompleteException
from primitive.fetchtool.helper import checkForRequiredArgs
from primitive.autoinstall.yast import SLES102AutoyastFactory
from primitive.autoinstall.yast import Opensuse103AutoyastFactory
from primitive.autoinstall.kickstart import KickstartFactory, RHEL5KickstartFactory

class InstallCommand(Command):
    ''' InstallCommand, and its children, coupled together with an
        XML parsing wrapper, are built to be compliant with UBI-7.
    '''
    SUPPORTED_BACKENDS = { 'sles': {'10': SLES102AutoyastFactory},
                           'opensuse': {'10.3': Opensuse103AutoyastFactory},
                           'rhel': {'5': RHEL5KickstartFactory,
                                    '4': KickstartFactory},
                           'centos': {'5': KickstartFactory,
                                      '4': KickstartFactory},
                           'scientificlinux': {'5': KickstartFactory,
                                               '4': KickstartFactory}
                         }

    def __init__(self, **kwargs):
        ''' Note that full input validation is not performed here. This is
            because we intend to have subclasses add their own required
            arguments to the input validation list(required_args).
            
            If we do full validation here, we only check this class' list,
            so full input validation is performed at execute stage.
        '''
        Command.__init__(self, name='installtool', logged=True, locked=True, lockdir=os.getenv('PRIMITIVE_LOCKDIR', '/var/lock/subsys/primitive'))

        self.os, self.os_version = self.validateOSVer(kwargs['os'])

        try:
            self.factory = self.SUPPORTED_BACKENDS[self.os][self.os_version](**kwargs)
        except AutoInstallConfigNotCompleteException, e:
            raise CommandMissingArgsError, str(e)

        self.kwargs = kwargs
        # List of required arguments that must be supplied for this command
        # to work successfully. Subclasses should add their own required
        # arguments to this list.
        self.required_args = ['template_uri',
                              'outfile']
        self.required_args += self.factory.keys
        self.registerPreCallback(self.validateInputRaisesException)

    def validateOSVer(self, os):
        ''' Check that OS name and version is supported by InstallCommand.
            If not, then raise CommandFailException.
            Input:
            * os is a dictionary containing at least the keys
              ['name', 'version']
        '''
        if not os.has_key('name') or not os.has_key('version'):
            raise CommandMissingArgsError, \
                  'Incomplete OS definition, supply name AND version'

        if os['name'] in self.SUPPORTED_BACKENDS.keys() and \
           os['version'] in self.SUPPORTED_BACKENDS[os['name']]:
               # OS and version supported.
               return os['name'], os['version']
        else:
            raise CommandFailException, \
                  '%s %s is not supported in InstallTool' % \
                  (os['name'], os['version'])

    def validateInput(self):
        ''' Ensure that required arguments are present in the kwargs. The
            list of required arguments is created during the initialisation
            of a InstallCommand instance(self.required_args). Derived classes
            append their specific list of required arguments during their
            own initialisation.
        '''
        return checkForRequiredArgs(self.kwargs, self.required_args)

    def validateInputRaisesException(self):
        ''' Ensure that required arguments are present, otherwise
            raise a CommandMissingArgsError.
        '''
        valid_input, missing = self.validateInput()
        if not valid_input:
            raise CommandMissingArgsError, \
                  '%s %s autoinstall generation requires the following missing arguments: %s' % \
                  (self.os, self.os_version, missing)


class GenerateAutoInstallScriptCommand(InstallCommand):
    ''' GenerateAutoInstallScriptCommand is a subclass of
        InstallCommand that generates as autoinstall script
        file from the input parameters.
    '''
    def __init__(self, **kwargs):
        InstallCommand.__init__(self, **kwargs)

    def execImpl(self):
        ''' Generate autoinstall script based on the factory.
        '''
        t = Template(file=str(self.factory.template),
                     searchList=[self.factory.getNameSpace()])
        of = file(self.kwargs['outfile'], 'w')
        of.write(str(t))
