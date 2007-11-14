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

global APPKEY
APPKEY   = "LSF7_0_1_ClusterName"

class thisReport(Report):

    	def toolHelp(self):
        	print self.gettext("genconfig_LSFconf_Help")


	def validateCluster(self,clustername):
		global APPKEY
		query = ('select agid from appglobals where kname="%s" '
			 'and kvalue="%s"' % (APPKEY, clustername)) 
		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		row = self.db.fetchone()
		if not row:
			return False
		if row[0] != '':
			return True
		return False

	
	def generateLsfConfig(self, mode):
            installerName = self.db.getAppglobals('PrimaryInstaller')
            if mode == 'slave':
               print """\
# Refer to the "Administration Platform LSF" before changing any parameters in
# this file.
# Any changes to the path names of LSF files must be reflected
# in this file. Make these changes with caution.

LSB_SHAREDIR=/opt/lsf/work

# Configuration directories
LSF_CONFDIR=/opt/lsf/conf

# Daemon log messages
LSF_LOGDIR=/opt/lsf/log
LSF_LOG_MASK=LOG_WARNING

# Batch mail message handling
LSB_MAILTO=!U

# Miscellaneous
LSF_AUTH=eauth

# General lsfinstall variables
LSF_MISC=/opt/lsf/7.0/misc
XLSF_APPDIR=/opt/lsf/7.0/misc
LSF_ENVDIR=/opt/lsf/conf

# Internal variable to distinguish Default Install
LSF_DEFAULT_INSTALL=y

# Internal variable indicating operation mode
LSB_MODE=batch

# WARNING: Please do not delete/modify next line!!
LSF_LINK_PATH=n

LSF_TOP=/opt/lsf
LSF_VERSION=7.0
LSF_EGO_ENVDIR=/opt/lsf/ego/kernel/conf
LSB_SHORT_HOSTLIST=1
LSF_HPC_EXTENSIONS="CUMULATIVE_RUSAGE"
LSB_SUB_COMMANDNAME=Y
LSF_MASTER_LIST="%s"
LSF_EGO_DAEMON_CONTROL="N"
LSF_LICENSE_FILE=/opt/lsf/conf/license.dat
""" % ( installerName )

            if mode == 'master':
               print """\
# Refer to the "Administration Platform LSF" before changing any parameters in
# this file.
# Any changes to the path names of LSF files must be reflected
# in this file. Make these changes with caution.

LSB_SHAREDIR=/opt/lsf/work

# Configuration directories
LSF_CONFDIR=/opt/lsf/conf
LSB_CONFDIR=/opt/lsf/conf/lsbatch

# Daemon log messages
LSF_LOGDIR=/opt/lsf/log
LSF_LOG_MASK=LOG_WARNING

# Batch mail message handling
LSB_MAILTO=!U

# Miscellaneous
LSF_AUTH=eauth

# General lsfinstall variables
LSF_MANDIR=/opt/lsf/7.0/man
LSF_INCLUDEDIR=/opt/lsf/7.0/include
LSF_MISC=/opt/lsf/7.0/misc
XLSF_APPDIR=/opt/lsf/7.0/misc
LSF_ENVDIR=/opt/lsf/conf

# Internal variable to distinguish Default Install
LSF_DEFAULT_INSTALL=y

# Internal variable indicating operation mode
LSB_MODE=batch

# WARNING: Please do not delete/modify next line!!
LSF_LINK_PATH=n

LSF_TOP=/opt/lsf
LSF_VERSION=7.0
LSF_EGO_ENVDIR=/opt/lsf/ego/kernel/conf
LSB_SHORT_HOSTLIST=1
LSF_HPC_EXTENSIONS="CUMULATIVE_RUSAGE"
LSB_SUB_COMMANDNAME=Y
LSF_MASTER_LIST="%s"
LSF_EGO_DAEMON_CONTROL="N"
LSF_LICENSE_FILE=/opt/lsf/conf/license.dat
""" % ( installerName )

	def runPlugin(self, pluginargs):
		if not pluginargs:
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFconf_Help")
			return

		if pluginargs[0] == '':
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFconf_Help")
			return
		
		if not self.validateCluster(pluginargs[0]):
			print "# ERROR:  Invalid LSF clustername: %s" % pluginargs[0]
			return

		generate = 'master'
		if len(pluginargs) > 1:
			# The second argument is the name of the file to generate
			if pluginargs[1] == 'master':
				generate = 'master'
			if pluginargs[1] == 'slave':
				generate = 'slave'

		self.generateLsfConfig(mode=generate)

