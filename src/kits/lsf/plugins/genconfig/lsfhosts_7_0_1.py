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

from kusu.genconfig import Report

#
# This will generate the contents of the LSF hosts file.
# It reads the existing file and adds any new hosts.
#
#

# Change these lines for newer versions of LSF
APPKEY   = "LSF7_0_1_ClusterName"
COMP_MASTER = "component-LSF-Master-v7_0_1"
COMP_COMPUTE = "component-LSF-Compute-v7_0_1"

import os
import sys
import string

class thisReport(Report):

	def toolHelp(self):
		print self.gettext("genconfig_LSFHosts_Help")


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


	def locateHosts(self, clustername):
		'''locateHosts - Locate the /opt/lsf/conf/hosts for this cluster
		within the CFM then read in its contents.'''
		query = ('SELECT ngname FROM nodegroups, appglobals, ng_has_comp, components '
			 'WHERE appglobals.ngid=nodegroups.ngid AND '
			 'nodegroups.ngid=ng_has_comp.ngid AND '
			 'ng_has_comp.cid=components.cid AND '
			 'components.cname="%s" AND appglobals.kvalue="%s"' % (COMP_MASTER, clustername))
		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		for row in self.db.fetchall():
			ngname = row[0]
			fqfn = "/etc/cfm/%s/opt/lsf/conf/hosts" % ngname
			return fqfn

		return ""
		

	def getHost(self, filename):
		'''getHost  - Locate the /opt/lsf/conf/hosts for this cluster
		within the CFM then read in its contents.'''

		data = []

		try:
			fp = file(filename, 'r')
			while True:
				line = fp.readline().strip()
				if len(line) == 0:
					break
			
				if line[:1] == '#':
					continue
			
				longhost = string.split(line)[1]
				shorthost = string.split(longhost, '.')[0]
				data.append(shorthost)
				#print "Found %s\n" % shorthost
			
			fp.close()
		except:
			# Error reading hosts file
			pass

		return data

	def newLines(self, filename, currenthosts, clustername):
		''' newLines - Output all the hosts not found in the original file'''
		global COMP_MASTER

		# Get a list os ip/nodes that are using the component
		# and are part of the same cluster
		query = ('SELECT nics.ip, nodes.name '
			 'FROM nics, nodes, appglobals, ng_has_comp, components '
			 'WHERE nics.nid = nodes.nid AND appglobals.ngid=nodes.ngid '
			 'AND ng_has_comp.ngid=nodes.ngid AND ng_has_comp.cid=components.cid ' 
			 'AND appglobals.kvalue="%s" AND (components.cname = "%s" OR components.cname = "%s")' % (clustername, COMP_MASTER, COMP_COMPUTE))

		try:
			self.db.execute(query)
		except:
			sys.stderr.write(self.gettext("DB_Query_Error\n"))
			sys.exit(-1)

		for row in self.db.fetchall():
			ip, name = row

			# The LSF hosts file format is DIFFERENT from
			# /etc/hosts.
			print "%s %s" % (ip, name)

	def runPlugin(self, pluginargs):
		if not pluginargs:
			print "# ERROR:  No LSF cluster provided!"
			return

		if pluginargs[0] == '':
			print "# ERROR:  No LSF cluster provided!"
			return
		
		if not self.validateCluster(pluginargs[0]):
			print "# ERROR:  Invalid LSF clustername: %s" % pluginargs[0]
			return

		chosts = []

		# Determine hosts file name for this cluster
		filename = self.locateHosts(pluginargs[0])
		if not filename:
			print 'ERROR: unable to determine location of hosts file for this cluster'
			sys.exit(-1)

		# Read any existing entries (if any)
		chosts = self.getHost(filename)

		# Append any new entries.
		self.newLines(filename, chosts, pluginargs[0])
