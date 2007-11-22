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

EGO_VERSION_WITH_UNDERSCORES = "1_2"

global COMPONENT_NAME
COMPONENT_NAME = "component-LSF-Master-v%s" % ( VERSION_WITH_UNDERSCORES )

global CLUSTER_NAME_KEY
CLUSTER_NAME_KEY = 'LSF%s_ClusterName' % ( VERSION_WITH_UNDERSCORES )

global EGO_CLUSTER_PLUGIN
EGO_CLUSTER_PLUGIN = 'egocluster_%s' % ( EGO_VERSION_WITH_UNDERSCORES )

global LSF_HOSTS_PLUGIN
LSF_HOSTS_PLUGIN = 'lsfhosts_%s' % ( VERSION_WITH_UNDERSCORES )

class AddHostPlugin(AddHostPluginBase):
    """LSF cluster file updater plugin"""

    def enabled(self):
        return True

    def getClusterName(self, ngid):
        clusterName = None

        try:
            sql = 'SELECT kvalue FROM appglobals WHERE kname = \'%s\' AND ngid=%d' % ( CLUSTER_NAME_KEY, ngid )

            self.dbconn.execute(sql)
            clusterName = self.dbconn.fetchone()[0]
        except:
            pass

        return clusterName

    def getNodegroupName(self, ngid):
	ngName = None

	try:
	    sql = "SELECT ngname FROM nodegroups WHERE ngid = %d" % ngid
	    self.dbconn.execute(sql)
	    ngName = self.dbconn.fetchone()[0]
	except:
	    pass

	return ngName

    def getMasterNodegroupName(self, clusterName, ngid):
	"""Determine the master nodegroup name for the specified ngid"""

	masterNgName = None

	sql = "SELECT nodegroups.ngname FROM nodegroups, components, ng_has_comp, appglobals WHERE components.cname = \"component-LSF-Master-v7_0_1\" and components.cid = ng_has_comp.cid and ng_has_comp.ngid = appglobals.ngid and nodegroups.ngid = appglobals.ngid and appglobals.kvalue = \"%s\"" % ( clusterName )

	try:
	    self.dbconn.execute(sql)
	    masterNgName = self.dbconn.fetchone()[0]
	except:
	    pass

	return masterNgName

    def initClusterInfo(self, nodename, info):
	self.ngid = 0
	self.clusterName = None
	self.ngName = None
	self.clusterFileName = None
	self.clusterFilePath = None
	self.masterNgName = None

	try:
	    self.ngid = int(info[nodename][0]["nodegroupid"])
	except:
	    return False

        self.clusterName = self.getClusterName(self.ngid)

	self.ngName = self.getNodegroupName(self.ngid)

	# Get nodegroup name for master candidate
	self.masterNgName = self.getMasterNodegroupName(self.clusterName,
		 self.ngid)

        self.clusterFileName = 'ego.cluster.%s' % self.clusterName
        self.clusterFilePath = '/etc/cfm/%s/opt/lsf/ego/kernel/conf/%s' % \
		( self.masterNgName, self.clusterFileName )

	return True

    def added(self, nodename, info, prePopulateMode):
	if not self.initClusterInfo(nodename, info):
	    return

    def removed(self, nodename, info):
	if not self.initClusterInfo(nodename, info):
	    return

        # Remove host from the lsf.cluster file for the master node
        self.updateFile(self.clusterFilePath, self.parseLsfClusterLine,
            nodename)

        # Remove host from LSF_MASTER_LIST in lsf.conf if
        # it is a master candidate host
        self.updateFile("/etc/cfm/%s/opt/lsf/conf/lsf.conf" % self.masterNgName,
		 self.parseLsfConfLine, nodename)

    def finished(self, nodelist, prePopulateMode):
	if not self.clusterName:
		return

        nodelist = self.checkAvailableComponent()
        if not nodelist:
           return

        self.updateLSFConfig()

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


    def updateLSFHosts(self):
	"""
	Update all /opt/lsf/conf/hosts files for the nodes in the cluster.
	This includes the master candidates and any compute nodegroups.
	"""

	print "Updating LSF hosts file"

	# Update hosts file for master nodegroup
	genconfig_cmd = '/opt/kusu/bin/genconfig %s %s' % \
		( LSF_HOSTS_PLUGIN, self.clusterName )

	# lsf_host_file = '/etc/cfm/%s/opt/lsf/conf/hosts' % self.masterNgName

	# os.system('%s > %s.tmp 2> /dev/null' % (genconfig_cmd, lsf_host_file))
	# os.system('cp %s.tmp %s' % (lsf_host_file, lsf_host_file))
	# os.system('rm -f %s.tmp' % lsf_host_file)

	# Find all nodegroups that have nodes in this cluster
	sql = "SELECT nodegroups.ngname FROM nodegroups, appglobals WHERE kvalue = \"%s\" and kname = \"LSF7_0_1_ClusterName\" and nodegroups.ngid = appglobals.ngid" % ( self.clusterName )

	try:
	    self.dbconn.execute(sql)
	except:
	    return False

	# Update the hosts file
	for ngName in self.dbconn.fetchall():
	    ngHostFile = '/etc/cfm/%s/opt/lsf/conf/hosts' % ngName
	    
	    print "Updating %s" % ( ngHostFile )

	    # os.system('cp %s %s' % ( lsf_host_file, ngHostFile ) )

	    os.system('%s > %s.tmp 2> /dev/null' % \
		(genconfig_cmd, ngHostFile ))
	    os.system('cp %s.tmp %s' % (ngHostFile, ngHostFile))
	    os.system('rm -f %s.tmp' % ngHostFile)

	return True

    def updateLSFClusterFile(self):
        """Update the LSF cluster file."""

	# print 'Nodegroup:', self.ngName
	# print 'Clustername:', self.clusterName
	# print 'ClusterFilePath:', self.clusterFilePath
	# print 'Master nodegroup name:', self.masterNgName

        genconfig_cmd = '/opt/kusu/bin/genconfig %s %s' % \
		( EGO_CLUSTER_PLUGIN, self.clusterName )

        if os.path.exists(self.clusterFilePath):
           os.system('echo "Updating LSF files"') 

           os.system('%s > %s.NEW 2> /dev/null' % \
		(genconfig_cmd, self.clusterFilePath))

           os.system('cp %s %s.OLD' % \
		(self.clusterFilePath, self.clusterFilePath))

           os.system('cp %s.NEW %s' % \
		(self.clusterFilePath, self.clusterFilePath))


    def updateLSFConfig(self):
	"""Regenerate all LSF cfg files"""

	self.updateLSFClusterFile()
	self.updateLSFHosts()
