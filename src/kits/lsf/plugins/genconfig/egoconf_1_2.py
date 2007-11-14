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

# Generate EGO configuration for LSF installation

from kusu.genconfig import Report

import os
import string

global APPKEY
APPKEY = "LSF7_0_1_ClusterName"

class ClusterInfo:
	pass

class thisReport(Report):

	def toolHelp(self):
		print self.gettext("genconfig_LSFconf_Help")

	def validateCluster(self,clustername):
		global APPKEY
		query = ('select ngid from appglobals where kname="%s" '
			 'and kvalue="%s"' % (APPKEY, clustername)) 
		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		row = self.db.fetchone()
		if not row:
			return None
		if row[0] != '':
			ci = ClusterInfo()
			ci.masterCandidatesNgid = int(row[0])
			return ci
		return None

	def generateEGOConfig(self, ci, mode):

		query = 'SELECT nodes.name FROM nodes, nodegroups WHERE nodes.ngid = %d AND nodes.ngid = nodegroups.ngid' % ( ci.masterCandidatesNgid )

		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		l = []
		for row in self.db.fetchall():
			l.append(row[0])

		if not l:
			print '# No master hosts defined for cluster'
			sys.exit(-1)

		masterList = ' '.join(l)

		print """\
# $Id: TMPL.ego.conf,v 1.3 2006/10/17 00:26:18 gwen Exp $
# EGO kernel parameters configuration file
#

# EGO master candidate host
EGO_MASTER_LIST="%s"

# EGO daemon port number
EGO_LIM_PORT=7869
EGO_KD_PORT=7870
EGO_PEM_PORT=7871

# EGO working and logging directory
EGO_WORKDIR=/opt/lsf/ego/kernel/work
EGO_LOGDIR=/opt/lsf/ego/kernel/log

# EGO log mask
EGO_LOG_MASK=LOG_WARNING

# EGO service directory
EGO_ESRVDIR=/opt/lsf/ego/eservice

# EGO security configuration
EGO_SEC_PLUGIN=sec_ego_default
EGO_SEC_CONF=/opt/lsf/ego/kernel/conf

# EGO event configuration
#EGO_EVENT_MASK=LOG_INFO
#EGO_EVENT_PLUGIN=eventplugin_snmp[SINK=host,MIBDIRS=/opt/lsf/ego/kernel/conf/mibs]

EGO_CONFDIR=/opt/lsf/ego/kernel/conf
EGO_VERSION=1.2.2
EGO_TOP=/opt/lsf/ego
""" % ( masterList )

		if mode == 'slave':
			print """\
# Parameters related to dynamic adding/removing host
EGO_GET_CONF=LIM
EGO_DYNAMIC_HOST_WAIT_TIME=60
"""

	def runPlugin(self, pluginargs):
		if not pluginargs:
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_EGOconf_Help")
			return

		if pluginargs[0] == '':
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_EGOconf_Help")
			return

		ci = self.validateCluster(pluginargs[0])

		if not ci:
			print "# ERROR:  Invalid LSF clustername: %s" % pluginargs[0]
			return

		ci.clusterName = pluginargs[0]

		generate = 'master'
		if len(pluginargs):
			# The second argument is the type of configuration to generate
			if pluginargs[1] == 'master':
				generate = 'master'
			if pluginargs[1] == 'slave':
				generate = 'slave'

		self.generateEGOConfig(ci, mode = generate)
