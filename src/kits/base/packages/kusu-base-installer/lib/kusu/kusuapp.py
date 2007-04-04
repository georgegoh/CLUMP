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

import gettext
import os
import sys
from optparse import OptionParser

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
        
        # Locate the Internationalization stuff
        if os.path.exists('../locale'):
            localedir = '../locale'
        else:
            # Try the system path
            if os.path.exists('/usr/share/locale'):
                localedir = '/usr/share/locale'
    
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


    def stdoutMessage(self, message, *args):
        """errorMessage - Output messages to STDERR with Internationalization.
        Additional arguments will be used to substitute variables in the
        message output"""
        if len(args) > 0:
            mesg = self.gettext(message) % args
        else:
            mesg = self.gettext(message)
        sys.stdout.write(mesg)
