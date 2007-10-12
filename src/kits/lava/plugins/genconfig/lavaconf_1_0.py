#! /usr/bin/env python
#   Copyright 2007 Platform Computing Inc
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
#

# Generate node and master configs, don't check if the file exists.

from kusu.genconfig import Report

import os
import string

class thisReport(Report):

    	def toolHelp(self):
        	print self.gettext("genconfig_Hosts_Help")

	def haveLava(self):
		path = "/opt/lava/conf"
		if os.path.exists(path):
			return 1
		return 0

	def generateLavaConfig(self, mode):
            installerName = self.db.getAppglobals('PrimaryInstaller')
            dnsZone = self.db.getAppglobals('DNSZone')
            if mode == 'slave':
               print """
LSB_SHAREDIR=/opt/lava/work

# Configuration directives
LSF_CONFDIR=/opt/lava/conf
#LSB_CONFDIR=/opt/lava/conf/lsbatch

LSF_MASTER_LIST=%s

# Daemon log messages
LSF_LOGDIR=/opt/lava/log
LSF_LOG_MASK=LOG_WARNING

LSF_STRIP_DOMAIN=.%s
LSB_MAILTO=!U@%s.%s
LSB_MAILSERVER=SMTP:%s.%s

LSF_AUTH=eauth

# General variables
LSF_ENVDIR=/opt/lava/conf

# Internal variable to distinguish Default Install
LSF_DEFAULT_INSTALL=y

# Internal variable indicating operation mode
LSB_MODE=batch

# WARNING: Please do not delete/modify next line!!
LSF_LINK_PATH=n

LSF_TOP=/opt/lava
""" % (installerName, dnsZone, installerName, dnsZone, installerName, dnsZone)

            if mode == 'master':
               print """
# Refer to the Inside Platform Lava documentation
# before changing any parameters in this file.
# Any changes to the path names of Lava files must be reflected
# in this file. Make these changes with caution.

LSB_SHAREDIR=/opt/lava/work

# Configuration directories
LSF_CONFDIR=/opt/lava/conf
LSB_CONFDIR=/opt/lava/conf/lsbatch

# Daemon log messages
LSF_LOGDIR=/opt/lava/log
LSF_LOG_MASK=LOG_WARNING

# Miscellaneous
LSF_AUTH=eauth

# General cwinstall variables
LSF_MANDIR=/opt/lava/1.0/man
LSF_INCLUDEDIR=/opt/lava/1.0/include
LSF_MISC=/opt/lava/1.0/misc
XLSF_APPDIR=/opt/lava/1.0/misc
LSF_ENVDIR=/opt/lava/conf

# Internal variable to distinguish Default Install
LSF_DEFAULT_INSTALL=y

# Internal variable indicating operation mode
LSB_MODE=batch

# WARNING: Please do not delete/modify next line!!
LSF_LINK_PATH=n

# LSF_MACHDEP and LSF_INDEP are reserved to maintain
# backward compatibility with legacy lsfsetup.
# They are not used in the new cwinstall.
LSF_INDEP=/opt/lava
LSF_MACHDEP=/opt/lava/1.0

LSF_TOP=/opt/lava
LSF_VERSION=1.0
LSF_MASTER_LIST=%s
LSF_STRIP_DOMAIN=.%s
LSB_MAILSERVER=SMTP:%s.%s
LSB_MAILTO=!U@%s.%s
LSF_RSH=ssh
""" % (installerName, dnsZone, installerName, dnsZone, installerName, dnsZone)

	def runPlugin(self, pluginargs):
		if self.haveLava() != 1:
			print "# Error:  Not an Lava machine"
			return

                if not pluginargs:
                   self.generateLavaConfig(mode='slave')

                if len(pluginargs) > 0:
                   if pluginargs[0] == 'slave':
                      self.generateLavaConfig(mode='slave')
                   if pluginargs[0] == 'master':
                      self.generateLavaConfig(mode='master')

