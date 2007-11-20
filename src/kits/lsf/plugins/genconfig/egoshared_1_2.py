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

# Change these lines for newer versions of LSF
APPKEY   = "LSF7_0_1_ClusterName"

COMP_MASTER = "component-LSF-Master-v7_0_1"

from kusu.genconfig import Report
import re

class thisReport(Report):

	def toolHelp(self):
		print self.gettext("genconfig_LSFcluster_Help")

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

	def generateEGOSharedFile(self, clustername):
		egoSharedFile = '%s/ego.shared' % \
			( self.getEgoConfDir(clustername) )

		fp = open(egoSharedFile, 'r')

		inClusterSection = False
		while True:
			instr = fp.readline()
			if instr == "":
				break

			if instr[:1] == '#':
				pass
			else:
				if re.compile("^Begin.*Cluster").search(instr):
					inClusterSection = True
					print instr,
					continue

				if re.compile("^End.*Cluster").search(instr):
					inClusterSection = False
				else:

					if re.compile("^ClusterName").search(instr):
						pass
					else:
						if inClusterSection:
							print clustername
							continue

			print instr,

		fp.close()

	def runPlugin(self, pluginargs):
		if not pluginargs:
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFshared_Help")
			return

		if pluginargs[0] == '':
			print "# ERROR:  No LSF cluster provided!"
			print self.gettext("genconfig_LSFshared_Help")
			return
		
		if not self.validateCluster(pluginargs[0]):
			print "# ERROR:  Invalid LSF clustername: %s" % pluginargs[0]
			return

		self.generateEGOSharedFile(pluginargs[0])
