#!/usr/bin/env python
# $Id: commands.py 3549 2010-02-24 09:51:53Z mkchew $
#
# Copyright 2008 Platform Computing Inc.
#
''' SvcTool is a primitive app to manage and configure services.
    This module is intended to be UBI-11 compliant.
'''

from primitive.system.software.dispatcher_dict import dispatcher_dict
from primitive.svctool.helper import dispatcherNameVerArch
from primitive.svctool.helper import checkForRequiredArgs
from primitive.svctool.helper import runServiceCommand, runServiceCommandDiscardOutput
from primitive.svctool.helper import printOutErr
from primitive.system.software.probe import OS
import os

from primitive.core.command import Command, CommandFailException
from primitive.core.errors import CommandMissingArgsException

class ActionNotImplementedException(CommandFailException): pass
class ActionNotSupportedException(CommandFailException): pass
class PlatformNotSupportedException(CommandFailException): pass

class SvcCommand(Command):
    ''' Command to manage a service.'''

    def __init__(self, **kwargs):
        Command.__init__(self, name='svctool', logged=True,
                                  locked=True, **kwargs)
        self.kwargs = kwargs
        if not hasattr(self, 'required_args'):
            self.required_args = []
        self.required_args.extend(['action'])
        valid, missing = checkForRequiredArgs(self.kwargs, self.required_args)
        if not valid:
            try:
                raise CommandMissingArgsException, \
                      "The %s action requires the following missing arguments: %s" % \
                      (self.kwargs['action'], missing)
            except KeyError:
                raise CommandMissingArgsException, "Command requires an action argument"
        self.action = self.kwargs['action']
        self.dispatcher_dict = dispatcher_dict
        self.os = OS()

    def execImpl(self):
        '''Perform command duties.
        '''
        pass

    def getWithService(self, action=None):
        if action:
            self.action = action
        os_tuple = dispatcherNameVerArch(self.os)
        action_dict = {}
        try:
            action_dict = self.dispatcher_dict[self.service + '_' + self.action]
        except KeyError:
            try:
                action_dict = self.dispatcher_dict['service_' + self.action]
            except KeyError:
                raise ActionNotSupportedException, "The '%s' action is not supported by SvcTool" % self.action

        command = None
        try:
            command = action_dict[os_tuple]
        except KeyError:
            try:
                command = action_dict[(os_tuple[0], os_tuple[1].split('.')[0], os_tuple[2])]
            except KeyError:
                raise PlatformNotSupportedException, "The %s-%s-%s platform is not supported for the '%s' action" % (os_tuple + (self.action,))
        
        self.command = command
        return command

class SvcStartCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = ['service']
        kwargs['action'] = 'start'
        SvcCommand.__init__(self, **kwargs)
        self.service = kwargs['service']
    
    def execImpl(self):
        command = self.getWithService()
        if 1 == command.count('%'):
            self.command = command % self.service
        return runServiceCommandDiscardOutput(self.command)

class SvcStopCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = ['service']
        kwargs['action'] = 'stop'
        SvcCommand.__init__(self, **kwargs)
        self.service = kwargs['service']
    
    def execImpl(self):
        command = self.getWithService()
        if 1 == command.count('%'):
            self.command = command % self.service
        return runServiceCommand(self.command)

class SvcStatusCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = ['service']
        kwargs['action'] = 'status'
        SvcCommand.__init__(self, **kwargs)
        self.service = kwargs['service']
    
    def execImpl(self):
        command = self.getWithService()
        if 1 == command.count('%'):
            self.command = command % self.service
        return runServiceCommand(self.command)

class SvcRestartCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = ['service']
        kwargs['action'] = 'restart'
        SvcCommand.__init__(self, **kwargs)
        self.service = kwargs['service']

    def execImpl(self):
        command = self.getWithService()
        if 1 == command.count('%'):
            self.command = command % self.service
        return runServiceCommandDiscardOutput(self.command)

class SvcReloadCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = ['service']
        kwargs['action'] = 'reload'
        SvcCommand.__init__(self, **kwargs)
        self.service = kwargs['service']
    
    def execImpl(self):
        raise ActionNotImplementedException

class SvcEnableCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = ['service']
        kwargs['action'] = 'enable'
        SvcCommand.__init__(self, **kwargs)
        self.service = kwargs['service']
    
    def execImpl(self):
        command = self.getWithService()
        if 1 == command.count('%'):
            self.command = command % self.service
        return runServiceCommand(self.command)

class SvcDisableCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = ['service']
        kwargs['action'] = 'disable'
        SvcCommand.__init__(self, **kwargs)
        self.service = kwargs['service']
    
    def execImpl(self):
        command = self.getWithService()
        if 1 == command.count('%'):
            self.command = command % self.service
        return runServiceCommand(self.command)

class SvcListCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = []
        kwargs['action'] = 'list'
        SvcCommand.__init__(self, **kwargs)
    
    def execImpl(self):
        raise ActionNotImplementedException

class SvcExistsCommand(SvcCommand):
    def __init__(self, **kwargs):
        self.required_args = ['service']
        kwargs['action'] = 'exists'
        SvcCommand.__init__(self, **kwargs)
        self.service = kwargs['service']
    
    def execImpl(self):
        command = self.getWithService()
        if 1 == command.count('%'):
            self.command = command % self.service
        return os.path.exists(self.command), ('Service %s is installed' % self.service, 0, 'Service %s is not installed' % self.service)
