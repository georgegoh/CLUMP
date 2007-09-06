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

from kusu.genconfig import Report

import os
import sys
import string

global COMPONENT_NAME
COMPONENT_NAME = 'component-lava-compute'

class thisReport(Report):

	def haveLsf(self):
		path = "/opt/lava/conf"
		if os.path.exists(path):
			return 1
		return 0

	def getClusterHosts(self):
		filename = "/opt/lava/conf/lsf.cluster.lava"
		if os.path.exists(filename) == 0:
			return
		
		fp = file(filename, 'r')
                data = []
		state = 0
                while True:
                        line = fp.readline()
                        if len(line) == 0:
                                break

                        if line[:1] == '#':
				continue

			if line[:5] == 'Begin':
				what = string.split(line)[1]
				if what == 'Host':
					state = 1

			if line[:3] == 'End':
				what = string.split(line)[1]
				if what == 'Host':
					break		

			if state == 0:
				continue

			if line[:8] == 'HOSTNAME':
				continue

			host = string.split(line)[0]
                        data.append(host)
			# print "Found %s\n" % host
			
                fp.close()
                return data


	def preHostEndList(self):
		# List the contents of the lsf cluster file up to the "End Host"
		# Note this is to be used in conjunction with "postHostEndList"
		
		filename = "/opt/lava/conf/lsf.cluster.lava" 
		if os.path.exists(filename) == 0:
			return
		
		fp = file(filename, 'r')
                while True:
                        line = fp.readline()
			if len(line) == 0:
                                break

			if line[:3] == 'End':
				what = string.split(line)[1]
				if what == 'Host':
					break

			print line,

                return fp

	
	def postHostEndList(self, fp):
		# List the contents of the lsf cluster file from the "End Host" section
		print "End     Host"
                while True:
                        line = fp.readline()
			if len(line) == 0:
                                break
			print line,
			
                fp.close()


	def newLines(self, currenthosts):
		# Add Compute nodes first

		global COMPONENT_NAME

                # Print out the data
                try:
                        res = self.db.getAppsglobals('DefaultLavaHostResource')
                except:
                        res = ""

		query = ('select nodes.name from nodes, nodegroups, ng_has_comp, components where '
			 'nodes.ngid = ng_has_comp.ngid and ng_has_comp.cid = components.cid and '
			 'components.cname = "%s"' % COMPONENT_NAME)

		try:	
    	             self.db.execute(query)
		except:
                     sys.stderr.write(self.gettext("DB_Query_Error\n"))
                     sys.exit(-1)

		nodes = []	
		for name in self.db.fetchall():
			nodes.append(name)
			print "Got %s, %s, %d \n" % name

		# Add nodes
		for node in nodes:
			if node in currenthosts:
				continue
			print '%s\t!\t!\t1     3.5 ()    ()    (%s)' % (node, res)
      
	def runPlugin(self, pluginargs):
		if self.haveLsf() != 1:
			print "# Error:  Not an Lava machine OR Lava not ready"
			return

		chosts = []
		chosts = self.getClusterHosts()
		fp = self.preHostEndList()
		self.newLines(chosts)
		self.postHostEndList(fp)
