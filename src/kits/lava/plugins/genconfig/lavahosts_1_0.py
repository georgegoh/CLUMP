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
# This will generate the contents of the Lava hosts file.
# It reads the existing file and adds any new hosts.
#
#

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

	def getHost(self):
		filename = "/opt/lava/conf/hosts"
		if os.path.exists(filename) == 0:
			return
	
		fp = file(filename, 'r')
                data = []
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
                return data


	def listHosts(self):
		# List the contents of the lava hosts file
		filename = "/opt/lava/conf/hosts"
		if os.path.exists(filename) == 0:
			return
		
		fp = file(filename, 'r')
                data = []
                while True:
                        line = fp.readline()
			if len(line) == 0:
                                break
			print line,
			
                fp.close()
                return data


	def newLines(self, currenthosts):
		domain = self.db.getAppglobals('DNSZone')
	        query = ('select nics.ip,nodes.name,networks.suffix '
       	        	'from nics,nodes,networks where nics.nid = nodes.nid '
       	          	'and nics.netid = networks.netid order by nics.ip')

		try:
		     self.db.execute(query)
		except:
		     sys.stderr.write(self.gettext("DB_Query_Error\n"))
		     sys.exit(-1)

		for row in self.db.fetchall():
		    ip, name, suffix = row
		    if suffix and suffix != '':
			compname = "%s%s" % (name, suffix)
		    else:
			compname = name

		    if not compname in currenthosts:
		        if suffix and suffix != '':
		            print "%s %s%s.%s %s%s" % (ip, name, suffix, domain, name, suffix)
		        else:
		            print "%s %s.%s %s" % (ip, name, domain, name)

	def runPlugin(self, pluginargs):
		if self.haveLsf() != 1:
			print "# Error:  Not an Lava machine"
			return

		chosts = []
		chosts = self.getHost()
		self.listHosts()
		self.newLines(chosts)
