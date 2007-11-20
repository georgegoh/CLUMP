#! /usr/bin/env python

# Copyright 2007 Platform Computing Inc
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

# Generate cluster file, batch resource files

# Change these lines for newer versions of LSF
APPKEY   = "LSF7_0_1_ClusterName"
COMP_MASTER = "component-LSF-Master-v7_0_1"
COMP_COMPUTE = "component-LSF-Compute-v7_0_1"

from kusu.genconfig import Report

import sys
import string
import os.path
import re

class ClusterInfo:
	def __init__(self, clusterName):
		self.clusterName = clusterName

class ClusterNode:
	def __init__(self, name, bIsMasterCandidate = False):
		self.name = name
		self.bIsMasterCandidate = bIsMasterCandidate

class thisReport(Report):

	
	def toolHelp(self):
		print self.gettext("genconfig_LSFcluster_Help")

	def validateCluster(self, clusterName):
		global APPKEY

		ci = ClusterInfo(clusterName)

		query = "SELECT nodegroups.ngid, nodegroups.ngname FROM nodegroups, appglobals WHERE appglobals.ngid = nodegroups.ngid AND appglobals.kname = \"%s\" AND appglobals.kvalue = \"%s\"" % ( APPKEY, ci.clusterName )

		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		row = self.db.fetchone()

		if not row:
			# Unable to determine nodegroup for specified cluster
			# name
			return None

		ci.masterCandidateNGID = row[0]
		ci.masterNodegroupName = row[1]

		return ci


	def getHostsInCluster(self, ci):
		hosts = []

		query = "SELECT nodes.name, nodes.ngid FROM nodes,appglobals WHERE appglobals.kname = \"%s\" and appglobals.kvalue = \"%s\" and nodes.ngid = appglobals.ngid" % ( APPKEY, ci.clusterName )

		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		for row in self.db.fetchall():
			bIsMasterCandidate = (row[1] == ci.masterCandidateNGID)
			hosts.append(ClusterNode(row[0], bIsMasterCandidate))

		return hosts

	def updateEgoClusterFile(self, ci):
		"""As the name implies, this function updates an existing
		ego.cluster.<clustername> file based on the database.
		"""

		# Set this to False to ignore any hosts found in the cluster
		# file that do not exist in the database
		bRemoveUnknownHosts = True

		res = ''

		clusFileName = "%s/ego.cluster.%s" % \
			( ci.egoConfDir, ci.clusterName )

		if not os.path.exists(clusFileName):
			print "# ERROR: Cluster file not found"
			return

		hosts = self.getHostsInCluster(ci)

		bInHostSection = False

		fp = open(clusFileName, 'r')

		while True:
			s = fp.readline()
			if s == '':
				break

			s = s.rstrip()

			if s == '' or s[:1] == "#":
				# Comments and newlines go verbatim
				print s
				continue

			if re.compile("^Begin.*Host$").search(s):
				bInHostSection = True
				print s
				continue
			else:
				if re.compile("^End.*Host$").search(s):
					bInHostSection = False

					# Append entries for hosts not
					# previously found in the existing
					# cluster file.
					for node in hosts:
						if node.bIsMasterCandidate:
							res = 'mg'
						else:
							res = ''

						print '%s\t!\t!\t1     3.5 ()    ()    (%s)' % \
							(node.name, res)


			if bInHostSection and re.compile("^HOSTNAME .*").search(s):
				print s
				continue

			if not bInHostSection:
				print s
				continue

			try:
				node  = string.split(s)[0]
			except:
				continue

			if bRemoveUnknownHosts and not node in hosts:
				# Host in cluster file is not found in the
				# cluster DB; ignore it.
				continue
			else:
				# Output the current entry
				print s

				# Remove from list
				try:
					hosts.remove(node)
				except ValueError:
					pass

		fp.close()

	def runPlugin(self, pluginargs):
		if not pluginargs:
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFcluster_Help")
			return

		if pluginargs[0] == '':
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFcluster_Help")
			return

		ci = self.validateCluster(pluginargs[0])
		if not ci:
			print "# ERROR:  Invalid LSF clustername: %s" % \
				( clusterName )
			sys.exit(-1)

		ci.egoConfDir = "/etc/cfm/%s/opt/lsf/ego/kernel/conf" % \
			( ci.masterNodegroupName )

		self.updateEgoClusterFile(ci)
