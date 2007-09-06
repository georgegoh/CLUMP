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

	def haveLsf(self):
		path = "/opt/lava/conf"
		if os.path.exists(path):
			return 1
		return 0

        def readLavaConf(self):
            if os.path.exists("/opt/lava/conf/lsf.conf"):
               return open("/opt/lava/conf/lsf.conf").readlines().close()


	def appendConf(self, filedata):
	    filedata.append("LSF_MASTER_LIST=%s\n" % self.db.getAppglobals('PrimaryInstaller'))
            filedata.append("LSF_STRIP_DOMAIN=.%s\n" % self.db.getAppglobals('DNSZone'))
            filedata.append("LSB_MAILSERVER=SMTP:%s.%s\n" % (self.db.getAppglobals('PrimaryInstaller'), self.db.getAppglobals('DNSZone'))
            filedata.append("LSB_MAILTO=!U@%s.%s\n" % (self.db.getAppglobals('PrimaryInstaller'), self.db.getAppglobals('DNSZone'))
            filedata.append("LSF_RSH=ssh\n")
	
	def runPlugin(self, pluginargs):
		if self.haveLsf() != 1:
			print "# Error:  Not an Lava machine"
			return

		fileData = readLavaConf()
		appendConf(fileData)

