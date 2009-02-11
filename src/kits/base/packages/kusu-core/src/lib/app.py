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

__version__ = "1.2"

CFMSYNC    = '/opt/kusu/sbin/cfmsync'
CFMCLIENT  = '/opt/kusu/sbin/cfmclient'

import gettext
import os
import sys
import atexit
from optparse import OptionParser
from path import path
import kusu.util.log as kusulog
import errno

sys.path.append("/opt/kusu/lib")
import platform
if platform.machine() == "x86_64":
    sys.path.append("/opt/kusu/lib64/python")
sys.path.append("/opt/kusu/lib/python")
sys.path.append('/opt/primitive/lib/python2.4/site-packages')

from primitive.system.software.probe import OS

class KusuApp:
    """ This is the class for all Kusu applications to inherit from """

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
        
        self.kel = kusulog.getKusuEventLog()

        # gettext Translations instance
        self.trans = None
        
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

        def _any(iterable):
            for element in iterable:
                if element:
                    return True
            return False

        # If the language is not defined within the environment, use
        # sane default.  This fixes the problem with calling a KusuApp
        # derivative from a CGI script (ie. nodeboot.cgi)
        lenv = ['LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG', 'LC_CTYPE']

        # In a SLES console, LANG is always set to 'POSIX'. However,
        # it will set LC_CTYPE when you subsequently change the language
        # settings using yast. For instance,
        #   LANG="POSIX"
        #   LC_CTYPE="zh_CN.UTF-8"
        # Hence we remove LANG="POSIX" and keep LC_CTYPE for SLES.
        if OS()[0].lower() in ['sles', 'opensuse', 'suse'] and \
                os.environ.get('LANG') == 'POSIX':
            lenv.remove('LANG')

        envfound = [ x in os.environ for x in lenv ]

        langs = []
        if _any(envfound):
            # Add the languages found in environment to langs
            env = zip(lenv, envfound)
            for key, val in env:
                if val:
                    langs.append(os.environ.get(key))

        # Add sane default as fallback if we do not have the translation
        # files for the languages found in the environment.
        if not 'en_US.UTF-8' in langs:
            langs.append('en_US.UTF-8')

        try:
            self.trans = gettext.translation(langdomain, localedir, langs)
            self.gettext = self.trans.gettext
        except IOError, e:
            (retval, errmsg) = e
            if retval == errno.ENOENT:
                # No translation found for this domain.
                self.gettext = gettext.gettext
            else:
                # Re-raise the exception
                raise

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
                msg = 'An instance of %s is already running ' % prog + \
                      '(lock file: %s).' % self.getlockfile()
                self.logErrorEvent(msg)
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

    def exitSuccessAndUnlock(self):
        if self.islock():
            self.unlock()
        sys.exit(0)
        
    def exitFailedAndUnlock(self, exitCode=-1):
        if self.islock():
            self.unlock()
        sys.exit(exitCode)

    def getActionDesc(self):
        """Returns description for current action performed. 
           Subclasses should override this method."""
        return self.name + " operation"

    def logEvent(self, msg, toStdout=True):
        """Log events and optionally output them to stdout."""
        if toStdout:
            sys.stdout.write(str(msg) + "\n")
        self.kel.info(str(msg))

    def logWarnEvent(self, warnMsg, toStdout=True):
        """Log warnings as events and optionally output them to stdout."""
        if toStdout:
            sys.stdout.write(str(warnMsg) + "\n")
        actionDesc = self.getActionDesc()
        self.kel.warn(actionDesc + ": " + str(warnMsg))
    
    def logErrorEvent(self, errMsg, toStderr=True):
        """Log errors as events and optionally output them to stderr."""
        if toStderr:
            sys.stderr.write(str(errMsg) + "\n")
        actionDesc = self.getActionDesc()
        self.kel.error(actionDesc + ": " + str(errMsg))
