#!/usr/bin/python
#
# $Id$
#
#  Copyright (C) 2007 Platform Computing
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#

__version__ = "5.0"

CFMSYNC    = '/opt/kusu/sbin/cfmsync'
CFMCLIENT  = '/opt/kusu/sbin/cfmclient'

import gettext
import os
import sys
import atexit
from optparse import OptionParser
from path import path
from kusu.util import compat

class KusuApp:
    """ This is the class for all OCS applications to inherit from """

    def __init__(self):
        """ Initialize Class variables.  Extend as needed (if needed) """
        self.args       = sys.argv
        self.version    = __version__
        self.name       = ''            # This is the name of the application
                                        # This will be derived from the name
        self.name = os.path.splitext(os.path.basename(self.args[0]))[0]

        tmpstr = '%s_Help' % self.name
        self._ = self.langinit()
        usage = self._(tmpstr)
        self.parser = OptionParser(usage)
        
    def langinit(self):
        """langinit - Initialize the Internationalization """
        langdomain = 'kusuapps'
        localedir  = ''

        # check if KUSU_ROOT environment exists
        kusuroot = os.environ.get('KUSU_ROOT',None)

        # Locate the Internationalization stuff
        if kusuroot and \
            os.path.exists('%s/share/locale' % kusuroot):
            localedir = '%s/share/locale' % kusuroot
        elif os.path.exists('../share/locale'):
            localedir = '../share/locale'
        else:
            # Try the system path
            if os.path.exists('/opt/kusu/share/locale'):
                localedir = '/opt/kusu/share/locale'

        gettext.bindtextdomain(langdomain, localedir)
        gettext.textdomain(langdomain)
        self.gettext = gettext.gettext
        return self.gettext

    def errorMessage(self, message, *args):
        """errorMessage - Output messages to STDERR with Internationalization.
        Additional arguments will be used to substitute variables in the
        message output"""
        if len(args) > 0:
            mesg = self.gettext(message) % args
        else:
            mesg = self.gettext(message)
        sys.stderr.write(mesg)

    def stderrMessage(self, message, *args):
        """errorMessage - Output messages to STDERR with Internationalization.
        Additional arguments will be used to substitute variables in the
        message output"""
        if len(args) > 0:
            mesg = self.gettext(message) % args
        else:
            mesg = self.gettext(message)
        sys.stderr.write(mesg)

    def stdoutMessage(self, message, *args):
        """errorMessage - Output messages to STDOUT with Internationalization.
        Additional arguments will be used to substitute variables in the
        message output"""
        if len(args) > 0:
            mesg = self.gettext(message) % args
        else:
            mesg = self.gettext(message)
        sys.stdout.write(mesg)

    def optargs(self, option, opt_str, value, parser):
        ''' optargs - a callback function that allows parsing CL keys with
        an optional argument. In RE terms, we can parse --foo [arg]?'''
        value = ''
        if parser.rargs:
            arg = parser.rargs[0]
            if not ((arg[:2] == '--' and len(arg)>2) or
                    (arg[:1] == '-'  and len(arg)>1 and arg[1] != '-')):
                    value = arg
                    del parser.rargs[0]
        setattr(parser.values, option.dest, value)


    def varargs(self, option, opt_str, value, parser):
        ''' varargs - a callback function that allows parsing CL keys with
        arbitrary # of args. In RE terms, we can parse --foo [arg]*'''

        # 3-liner below allows for mult. instances of the CL option
        # value = getattr(parser.values, option.dest)
        # if not value:
        #     value = []

        value = []
        rargs = parser.rargs # CL args trailing this option
        while rargs:
            arg = rargs[0]
            if ((arg[:2] == '--' and len(arg)>2) or
                (arg[:1] == '-'  and len(arg)>1 and arg[1] != '-')):
                break
            else:
                value.append(arg)
                del rargs[0]
        setattr(parser.values, option.dest, value)

    def force_single_instance(self):
        if len(sys.argv) >= 1:
            prog = path(sys.argv[0]).stripext().basename()

            if self.islock():
                sys.stderr.write('An instance of %s is already running ' % prog)
                sys.stderr.write('(lock file: %s).\n' % self.getlockfile())
                sys.exit(1)

            atexit.register(self.unlock)
            self.lock()

    def lock(self):
        if len(sys.argv) >= 1:
            prog = path(sys.argv[0]).stripext().basename()
            lock = path('/var/lock/subsys/') / prog
            lock.touch()

    def unlock(self):
        if len(sys.argv) >= 1:
            prog = path(sys.argv[0]).stripext().basename()
            lock = path('/var/lock/subsys/') / prog
            if lock.exists(): lock.remove()
            
    def islock(self):
        if len(sys.argv) >= 1:
            prog = path(sys.argv[0]).stripext().basename()
            lock = path('/var/lock/subsys/') / prog
            return lock.exists() 
        else:
            return None

    def getlockfile(self):
        if len(sys.argv) >= 1:
            prog = path(sys.argv[0]).stripext().basename()
            lock = path('/var/lock/subsys/') / prog
            return lock
        else:
            return None

