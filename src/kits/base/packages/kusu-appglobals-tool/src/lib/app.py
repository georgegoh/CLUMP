#!/usr/bin/env python
# $Id: app.py 3517 2010-02-12 09:19:08Z kunalc $
#
# Copyright (c) 2009 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import sys
import os
from kusu.core.app import KusuApp
from optparse import OptionParser, SUPPRESS_USAGE, SUPPRESS_HELP
from kusu.appglobals.metadata import *
from kusu.appglobals.settings import *
from kusu.util.errors import InvalidMetaXMLError, InvalidPathError, UnknownSettingNameError, InvalidAppglobalValueError

class MyOptionParser(OptionParser):
    def __init__(self, usage=''):
        OptionParser.__init__(self, usage)
        self.extra_help_str = """
actions:
  set         Change the value of a database setting
              Requires 2 sub-arguments: <target> <value>

  show        Display the value of one or all database settings
              Takes at most 1 argument: <target>

sub-help: [-h|--help]
  Display contextual help for the specified action.
  Note: For more information about contextual help, please check
        the man page.

target:
  A valid setting name to be operated acted upon (set/show).

value:
  A valid setting for the specified target.
  To be used only with the set action and not with show.
"""

    def print_help(self):
        OptionParser.print_help(self)
        print self.extra_help_str

class AppGlobalsToolApp(KusuApp):
    """Main application class"""

    def __init__(self):
        KusuApp.__init__(self)

        self.parser = MyOptionParser(usage="%prog [options] [action] [-h|--help] [target [value]]")
        self.parser.add_option('-v', '--version', action="store_true", help='Displays version and exits')
        self.parser.disable_interspersed_args()

        self.metafiles = []

        self.action = ''
        self.target = None
        self.value = None

        self.action_dict = {'version': self.printVersion,
                            'set': self.setValue,
                            'show': self.printValue,
                            'show_all': self.printAllValues,
                            'list': self.printNames,
                            'meta': self.printMetadata}


    def printVersion(self):
        print '%s version %s\n' % (sys.argv[0].split('/')[-1], self.version)

    def setValue(self):
        try:
            Settings(self.metafiles).setAppglobal(self.target, self.value)
        except (InvalidMetaXMLError, InvalidPathError, UnknownSettingNameError, InvalidAppglobalValueError), e:
            self._exit_with_msg(msg='Error: Failed to set value. %s' % str(e), showhelp=False)

    def printValue(self):
        try:
            Settings(self.metafiles).displayAppglobalValue(self.target)
        except (InvalidMetaXMLError, InvalidPathError), e:
            self._exit_with_msg(msg='Error: Unable to read metadata file. %s' % str(e), showhelp=False)

    def printAllValues(self):
        try:
            Settings(self.metafiles).displayAllAppglobalValues()
        except (InvalidMetaXMLError, InvalidPathError), e:
            self._exit_with_msg(msg='Error: Unable to read metadata file. %s' % str(e), showhelp=False)

    def printNames(self):
        print 'usage: show <target>'
        print '\tDisplays the current value of the "target" setting\n'
        print 'Target settings:'
        print '='*16
        try:
            Metadata(self.metafiles).displayMetaNames()
        except (InvalidMetaXMLError, InvalidPathError), e:
            self._exit_with_msg(msg='Error: Unable to read metadata file. %s' % str(e), showhelp=False)

    def printMetadata(self):
        print 'usage: set <target> <value>'
        print '\tSets the "target" setting to the given "value"\n'
        print 'Target settings:'
        print '='*16
        try:
            Metadata(self.metafiles).displayMetadata(name=self.target)
        except (InvalidMetaXMLError, InvalidPathError), e:
            self._exit_with_msg(msg='Error: Unable to read metadata file. %s' % str(e), showhelp=False)
        except UnknownSettingNameError, e:
            self._exit_with_msg(msg='Error: %s' % str(e), showhelp=False)

    def _exit_with_msg(self, msg='Error: Please check usage', showhelp=True, exitcode=1):
        '''Helper function to write to error stream and exit with the return code.
        '''

        if msg and not msg.endswith('\n'):
            msg += '\n'

        sys.stderr.write(msg)

        if showhelp:
            print
            self.parser.print_help()

        sys.exit(exitcode)

    def parseArgs(self):
        options, args = self.parser.parse_args()

        if options.version:
            if args:
                self._exit_with_msg(msg='Error: No other options/args can be used with -v/--version option.')

            self.action = 'version'
            return

        if len(args) > 0:
            self.action = args[0]
            if self.action not in ['set', 'show']:
                self._exit_with_msg(msg="Action '%s is not a recognized action.'" % self.action)

            sub_parser = OptionParser(usage=SUPPRESS_USAGE, add_help_option=0)
            sub_parser.add_option('-h', '--help', dest='help', action='store_true', help=SUPPRESS_HELP)
            
            sub_parser.disable_interspersed_args()
            sub_options, sub_args = sub_parser.parse_args(args[1:])

            if len(sub_args) > 2:
                self._exit_with_msg(msg='Error: Too many sub-arguments used. At most 2 sub-arguments are expected.')
            if len(sub_args) > 1:
                if self.action == 'show':
                    self._exit_with_msg(msg='Error: Target is an incompatible argument for show action.')
                self.value = sub_args[1]
            if len(sub_args) > 0:
                self.target = sub_args[0]

            if sub_options.help:
                if self.action == 'set':
                    if self.value:
                        self._exit_with_msg(msg='Error: Too many sub-arguments used with -h/--help option for "set" action. At most 1 sub-argument is expected.')
                    self.action = 'meta'
                    return

                elif self.action == 'show':
                    if self.target:
                        self._exit_with_msg(msg='Error: -h/--help option for "show" action cannot be used with any sub-arguments.')
                    self.action = 'list'
                    return

            if self.action == 'set' and not self.target:
                self._exit_with_msg(msg='Error: Target is a required argument for set action.')
            if self.action == 'set' and self.value == None:
                self._exit_with_msg(msg='Error: Value is a required argument for set action.')

            if self.action == 'show' and not self.target:
                self.action = 'show_all'
        else:
            self._exit_with_msg(msg='', exitcode=0)

    def run(self):
        self.parseArgs()
        func = self.action_dict[self.action]
        func()
