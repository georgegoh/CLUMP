# Copyright (C) 2007 Platform Computing Inc.

# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

#
# Update the Lava clusters file on demand.
#

import re
import os
from syslog import syslog
from kusu.addhost import *

global COMPONENT_NAME
COMPONENT_NAME = "component-lava-master-v1.0"

class AddHostPlugin(AddHostPluginBase):
	"Lava cluster file updater plugin"

        def enabled(self):
            return True

	def removed(self, nodename, info):
		self.clusterName='lava'

		# Remove host from the lsf.cluster file
		self.updateFile("/opt/lava/conf/lsf.cluster.%s" % self.clusterName,
		     self.parseLsfClusterLine, nodename)

		# Remove host from LSF_MASTER_LIST in lsf.conf if
		# it is a master candidate host
		self.updateFile("/opt/lava/conf/lsf.conf", 
		     self.parseLsfConfLine, nodename)

		# Remove host from the lava host file
		os.system("grep -v %s /opt/lava/conf/hosts > /opt/lava/conf/hosts.OLD" % (nodename + "."))
		os.rename("/opt/lava/conf/hosts.OLD", "/opt/lava/conf/hosts")

	def finished(self, nodelist):
		nodelist = self.checkAvailableComponent()
		if not nodelist:
		   return

		self.updateLavaConfig()
		self.fixSymlinks(nodelist)
		self.reconfigLava()
		self.printLsfHpcRestartMsg()

	def checkAvailableComponent(self):
	    """ Return a list of all nodegroups that have the Lava components in use """
	    query = ('select nodegroups.ngname from nodegroups, ng_has_comp, component where '
		     'nodegroups.ngid = ng_has_comp.ngid and ng_has_comp.cid = components.cid and '
		     'components.cname = "%s"' % COMPONENT_NAME)

	    try:
	        self.dbconn.execute(query)
                return list(self.dbconn.fetchall())
            except:
                return []

	def parseLsfClusterLine(self, line, nodename):
		"""If the first token in the line matches the nodename,
		   discard it. Otherwise, return the line as is."""

		tokens = line.split()
		if not tokens:
			return line

		host = tokens[0]
		if host == nodename:
			syslog('Removing %s from lsf.cluster.%s file' % (host, self.clusterName) )
			return None

		return line


	def parseLsfConfLine(self, line, nodename):
		"""Check if line has LSF_MASTER_LIST, remove the node
		from the list, and return the updated line.  Otherwise, 
		return the line as is."""

		if re.search('^LSF_MASTER_LIST=', line.strip()):
			line = re.sub('LSF_MASTER_LIST=', '', line)
			line = re.sub('"', '', line)
			host_list = line.split()
			new_host_str = ''

			for host in host_list:
				# strip .local from hostname
				host2 = re.sub('.local$', '', host)

				if host2 != nodename:
					if not new_host_str:
						new_host_str = host
					else:
						new_host_str += " %s" % host
				else:
					syslog('Removing %s from LSF_MASTER_LIST in '
						'lsf.conf' % host)

			return('LSF_MASTER_LIST="%s"\n' % new_host_str)

		return line


	def updateFile(self, curr_file, parse_line_func, nodename):
		"""Used for updating specific lines in a given file. User must
		specify a function to parse each line. Parse function must
		return a string to output to the file or 'None' to discard the line"""

		if not curr_file or not parse_line_func:
			return

		old_file = "%s.OLD" % curr_file
		new_file = "%s.NEW" % curr_file
		
		if not os.path.exists(curr_file):
			return
		curr_file_fp = open(curr_file, 'r')
		new_file_fp = open(new_file, 'w')

		while True:
			line = curr_file_fp.readline()
			if not line:
				break

			parsed_line = parse_line_func(line, nodename)
			if parsed_line != None:
				new_file_fp.write(parsed_line)

		curr_file_fp.close()
		new_file_fp.close()

		os.system('cp %s %s' % (curr_file, old_file))
		os.system('cp %s %s' % (new_file, curr_file))

	def updateLavaConfig(self):
		"""Update the Lava cluster file."""

		genconfig_cmd = '/opt/kusu/bin/genconfig lavacluster_1_0'
		lsf_cluster_file = '/opt/lava/conf/lsf.cluster.lava'

		if os.path.exists(lsf_cluster_file):
		   os.system('echo "Updating Lava files"') 
		   os.system('%s > %s.NEW 2> /dev/null' % (genconfig_cmd, lsf_cluster_file))
		   os.system('cp %s %s.OLD' % (lsf_cluster_file, lsf_cluster_file))
		   os.system('cp %s.NEW %s' % (lsf_cluster_file, lsf_cluster_file))
                   os.system('chown lavaadmin:root %s' % lsf_cluster_file)

	           genconfig_cmd = '/opt/kusu/bin/genconfig lavahosts_1_0'
                   lsf_host_file = '/opt/lava/conf/hosts'
                   os.system('echo "Updating Lava host file"')
                   os.system('%s > %s.tmp 2> /dev/null' % (genconfig_cmd, lsf_host_file))
                   os.system('cp %s.tmp %s' % (lsf_host_file, lsf_host_file))
                   os.system('chown lavaadmin:root %s' % lsf_host_file)

	def updateSymlinks(self, nodegroups):
    	    """ Fix CFM symlinks for master and master candidate Lava nodegroups """

	    for nodegroup in nodegroups:
	       if not os.path.exists("/etc/cfm/\'%s\'/opt/lava/conf/lsf.cluster.lava" % nodegroup):
		  os.system("mkdir -p /etc/cfm/\'%s\'/opt/lava/conf" % nodegroup)
                  os.symlink("/opt/lava/conf/lsf.cluster.lava", "/etc/cfm/\'%s\'/opt/lava/conf/lsf.cluster.lava" % nodegroup)

	       if not os.path.exists("/etc/cfm/\'%s\'/opt/lava/conf/hosts" % nodegroup):
		  os.symlink("/opt/lava/conf/hosts", "/etc/cfm/\'%s\'/opt/lava/conf/hosts" % nodegroup)
		       
	def reconfigLava(self):
		"""Restart Lava cluster"""

		profile_file = '/opt/lava/conf/profile.lsf'
		reconfig_cmd = 'lsadmin reconfig -f'

		if os.path.exists(profile_file):
	   	   os.system('. %s ;%s > /dev/null' % (profile_file, reconfig_cmd))

	def printLsfHpcRestartMsg(self):
		"""Print a reminder for the user to manually restart 
		   their Lava cluster """

		print "Note: Please run 'update -f' to finish configuring your nodes"
