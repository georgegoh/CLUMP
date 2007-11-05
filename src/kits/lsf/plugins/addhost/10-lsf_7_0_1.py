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
# Update the LSF clusters file on demand.
#

import re
import os
from syslog import syslog
from kusu.addhost import *

global VERSION
VERSION = '7.0.1'

global VERSION_WITH_UNDERSCORES
VERSION_WITH_UNDERSCORES = VERSION.replace('.', '_')

global COMPONENT_NAME
COMPONENT_NAME = "component-LSF-Master-v%s" % ( VERSION_WITH_UNDERSCORES )

global CLUSTER_NAME_KEY
CLUSTER_NAME_KEY = 'LSF%s_ClusterName' % ( VERSION_WITH_UNDERSCORES )

global LSF_CLUSTER_PLUGIN
LSF_CLUSTER_PLUGIN = 'lsfcluster_%s' % ( VERSION_WITH_UNDERSCORES )

class AddHostPlugin(AddHostPluginBase):
    "LSF cluster file updater plugin"

    def enabled(self):
        return True

	def added(self, nodename, info, prePopulateMode):
		clusterName = self.getClusterName()

        self.clusterFileName = 'lsf.cluster.%s' % clusterName
        self.clusterFilePath = '/opt/lsf/conf/%s' % self.clusterFileName

	def getClusterName(self):
		ngid = int(info[nodename][0]["nodegroupid"])

		clusterName = None

		try:
			sql = 'SELECT kvalue FROM appglobals WHERE kname = \'%s\' AND ngid=%d' % ( CLUSTER_NAME_KEY, ngid )

			self.dbconn.execute(sql)
			clusterName = self.dbconn.fetchone()[0]
		except:
			pass

		return clusterName

    def removed(self, nodename, info):

        clusterName = self.getClusterName()

        self.clusterFileName = 'lsf.cluster.%s' % clusterName
        self.clusterFilePath = '/opt/lsf/conf/%s' % self.clusterFileName

        # Remove host from the lsf.cluster file
        self.updateFile(self.clusterFilePath, self.parseLsfClusterLine,
            nodename)

        # Remove host from LSF_MASTER_LIST in lsf.conf if
        # it is a master candidate host
        self.updateFile("/opt/lsf/conf/lsf.conf", 
             self.parseLsfConfLine, nodename)

        # Remove host from the lsf host file
        # os.system("grep -v %s /opt/lsf/conf/hosts > /opt/lsf/conf/hosts.OLD" % (nodename + "."))
        # os.rename("/opt/lsf/conf/hosts.OLD", "/opt/lsf/conf/hosts")

    def finished(self, nodelist, prePopulateMode):
        nodelist = self.checkAvailableComponent()
        if not nodelist:
           return

        self.updateLSFConfig()
        self.updateSymlinks(nodelist)
        self.reconfigLSF()
        self.printLsfHpcRestartMsg()

    def checkAvailableComponent(self):
        """Return a list of all nodegroups that have the LSF components in
        use."""

        query = ('SELECT nodegroups.ngname FROM nodegroups, ng_has_comp, components WHERE '
             'nodegroups.ngid = ng_has_comp.ngid AND ng_has_comp.cid = components.cid AND '
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
            syslog('Removing %s from %s file' % (host, self.clusterFilePath) )
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

    def updateLSFConfig(self):
        """Update the LSF cluster file."""

        genconfig_cmd = '/opt/kusu/bin/genconfig %s' % ( LSF_CLUSTER_PLUGIN )

        if os.path.exists(self.clusterFilePath):
           os.system('echo "Updating LSF files"') 
           os.system('%s > %s.NEW 2> /dev/null' % (genconfig_cmd, self.clusterFilePath))
           os.system('cp %s %s.OLD' % (self.clusterFilePath, self.clusterFilePath))
           os.system('cp %s.NEW %s' % (self.clusterFilePath, self.clusterFilePath))
           os.system('chown lsfadmin:lsfadmin %s' % self.clusterFilePath)

           # genconfig_cmd = '/opt/kusu/bin/genconfig lsfhosts_1_0'
           # lsf_host_file = '/opt/lsf/conf/hosts'
           # os.system('echo "Updating LSF host file"')
           # os.system('%s > %s.tmp 2> /dev/null' % (genconfig_cmd, lsf_host_file))
           # os.system('cp %s.tmp %s' % (lsf_host_file, lsf_host_file))
           # os.system('chown lsfadmin:lsfadmin %s' % lsf_host_file)

    def updateSymlinks(self, nodegroups):
        """ Fix CFM symlinks for master and master candidate LSF nodegroups """

        for nodegroup in nodegroups:
            if not os.path.exists(self.clusterFilePath):
                os.system("mkdir -p '/etc/cfm/%s/opt/lsf/conf'" % nodegroup)
                try:
                    os.symlink(self.clusterFilePath, '/etc/cfm/%s/opt/lsf/conf/%s' % ( nodegroup, self.clusterFileName ) )
                except:
                    pass

            if not os.path.exists("/etc/cfm/%s/opt/lsf/conf/hosts" % nodegroup):
                try:
                    os.symlink("/opt/lsf/conf/hosts", "/etc/cfm/%s/opt/lsf/conf/hosts" % nodegroup)
                except:
                    pass
               
    def reconfigLSF(self):
        """Restart LSF cluster"""

        profile_file = '/opt/lsf/conf/profile.lsf'
        reconfig_cmd = 'lsadmin reconfig -f'

        if os.path.exists(profile_file):
            os.system('. %s ;%s > /dev/null' % (profile_file, reconfig_cmd))

    def printLsfHpcRestartMsg(self):
        """Print a reminder for the user to manually restart LSF cluster"""

        print "Please run: 'cfmsync -f' to restart the LSF batch service."
