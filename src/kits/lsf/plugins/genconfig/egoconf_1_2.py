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
import sys
import re

global APPKEY
APPKEY = "LSF7_0_1_ClusterName"

COMP_MASTER = "component-LSF-Master-v7_0_1"

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

	def getEgoConfDir(self, clusterName):
	    query = ('SELECT ngname FROM nodegroups, appglobals, ng_has_comp, components '
			'WHERE appglobals.ngid=nodegroups.ngid AND '
			'nodegroups.ngid=ng_has_comp.ngid AND '
			'ng_has_comp.cid=components.cid AND '
			'components.cname="%s" AND appglobals.kvalue="%s"' % \
			(COMP_MASTER, clusterName))
	    try:
	 	self.db.execute(query)
	    except:
		sys.stderr.write(self.gettext("DB_Query_Error\n"))
		sys.exit(-1)

	    egoConfDir = ''

	    try:
	    	row = self.db.fetchone()

	  	egoConfDir = "/etc/cfm/%s/opt/lsf/ego/kernel/conf" % ( row[0] )
	    except:
		pass

	    return egoConfDir

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

		fp = open('%s/ego.conf' % \
			( self.getEgoConfDir(ci.clusterName) ), 'r')

		while True:
			instr = fp.readline()
			if instr == '':
				break

			if re.compile("^EGO_MASTER_LIST=").search(instr):
				print "EGO_MASTER_LIST=\"%s\"" % masterList
				continue

			print instr,

		if mode == 'slave':
			print """\

# Parameters related to dynamic adding/removing host
EGO_GET_CONF=LIM
EGO_DYNAMIC_HOST_WAIT_TIME=60
"""

		fp.close()

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
