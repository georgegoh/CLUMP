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
import sys
import re

global APPKEY
APPKEY   = "LSF7_0_1_ClusterName"

COMP_MASTER = "component-LSF-Master-v7_0_1"

class ClusterInfo:
	pass

class thisReport(Report):

    	def toolHelp(self):
        	print self.gettext("genconfig_LSFconf_Help")


	def validateCluster(self, clustername):
		global APPKEY

		ci = ClusterInfo()

		ci.clusterName = clustername

		query = ('select ngid from appglobals where kname="%s" '
			 'and kvalue="%s"' % (APPKEY, ci.clusterName)) 
		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		row = self.db.fetchone()

		if not row:
			return None

		if row[0] != '':
			ci.masterCandidateNGID = int(row[0])
			return ci

		return None

	def getMasterCandidateList(self, ci):
		query = 'SELECT name FROM nodes, nodegroups WHERE nodes.ngid = %d AND nodes.ngid = nodegroups.ngid' % ( ci.masterCandidateNGID )

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

		return ' '.join(l)

	def getLsfConfDir(self, clusterName):
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

	    lsfConfDir = ''

	    try:
	    	row = self.db.fetchone()

	  	lsfConfDir = "/etc/cfm/%s/opt/lsf/conf" % ( row[0] )
	    except:
		pass

	    return lsfConfDir

	def generateLsfConfig(self, ci, mode):
	    # Determine location of the configuration file based on the
	    # nodegroup.
	    #
	    lsfConfFileName = "%s/lsf.conf" % \
		( self.getLsfConfDir(ci.clusterName) )

	    if not os.path.exists(lsfConfFileName):
		return

	    mcList = self.getMasterCandidateList(ci)

	    fin = open(lsfConfFileName, "r")

	    while True:
		instr = fin.readline()
		if instr == '':
		    break

		if re.compile("^LSF_MASTER_LIST=").search(instr):
			print "LSF_MASTER_LIST=\"%s\"" % mcList
			continue

		print instr,

	    fin.close()

	def runPlugin(self, pluginargs):
		if not pluginargs:
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFconf_Help")
			return

		if pluginargs[0] == '':
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFconf_Help")
			return
		
		ci = self.validateCluster(pluginargs[0])
		if not ci:
			print "# ERROR:  Invalid LSF clustername: %s" % pluginargs[0]
			return

		generate = 'master'
		if len(pluginargs) > 1:
			if pluginargs[1] == 'master':
				generate = 'master'
			if pluginargs[1] == 'slave':
				generate = 'slave'

		self.generateLsfConfig(ci, mode = generate)
