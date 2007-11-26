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

global EGO_CONF_PLUGIN
EGO_CONF_PLUGIN = 'egoconf_%s' % ( EGO_VERSION_WITH_UNDERSCORES )

global LSF_HOSTS_PLUGIN
LSF_HOSTS_PLUGIN = 'lsfhosts_%s' % ( VERSION_WITH_UNDERSCORES )

global LSF_CONF_PLUGIN
LSF_CONF_PLUGIN = 'lsfconf_%s' % ( VERSION_WITH_UNDERSCORES )

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

    def getMasterNodegroup(self, clusterName):
	"""Determine the master nodegroup name for this cluster"""

	masterNgName = None
	masterNgId = 0

	sql = "SELECT nodegroups.ngname,nodegroups.ngid FROM nodegroups, components, ng_has_comp, appglobals WHERE components.cname = \"component-LSF-Master-v7_0_1\" and components.cid = ng_has_comp.cid and ng_has_comp.ngid = appglobals.ngid and nodegroups.ngid = appglobals.ngid and appglobals.kvalue = \"%s\"" % ( clusterName )

	try:
	    self.dbconn.execute(sql)
	    row = self.dbconn.fetchone()
	    masterNgName = row[0]
	    masterNgId = row[1]
	except:
	    pass

	return (masterNgName, masterNgId)

    def initClusterInfo(self, nodename, info):
	self.ngid = 0
	self.clusterName = None
	self.ngName = None
	self.masterNgName = None
	self.masterNgId = 0

	try:
	    self.ngid = int(info[nodename][0]["nodegroupid"])
	except:
	    return False

        self.clusterName = self.getClusterName(self.ngid)

	self.ngName = self.getNodegroupName(self.ngid)

	# Get nodegroup name for master candidate
	(self.masterNgName, self.masterNgId) = \
	    self.getMasterNodegroup(self.clusterName)

	return True

    def added(self, nodename, info, prePopulateMode):
	if not self.initClusterInfo(nodename, info):
	    return

    def removed(self, nodename, info):
	if not self.initClusterInfo(nodename, info):
	    return

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

    def updateLSFConfig(self):
	"""
	Update all LSF configuration files for the nodes in the cluster.
	This includes the master candidates and any compute nodegroups.
	"""

	# Find all nodegroups that have nodes in this cluster
	sql = "SELECT nodegroups.ngname, IF(nodegroups.ngid = %d, 'master', 'slave') FROM nodegroups, appglobals WHERE kvalue = \"%s\" and kname = \"LSF7_0_1_ClusterName\" and nodegroups.ngid = appglobals.ngid" % \
		( self.masterNgId, self.clusterName )

	try:
	    self.dbconn.execute(sql)
	except:
	    return False

	# Update the hosts file
	for row in self.dbconn.fetchall():
	    print 'Updating configuration for nodegroup %s' % row[0]

	    # Update /opt/lsf/conf/hosts
	    hostsFileName = '/etc/cfm/%s/opt/lsf/conf/hosts' % row[0]

	    cmd = '/opt/kusu/bin/genconfig %s %s' % \
		( LSF_HOSTS_PLUGIN, self.clusterName )

	    os.system("%s >%s.tmp 2>/dev/null" % ( cmd, hostsFileName ))
	    os.system("cp %s.tmp %s" % ( hostsFileName, hostsFileName ))
	    os.system("rm -f %s.tmp" % ( hostsFileName ))

	    # Update /opt/lsf/conf/lsf.conf
	    confFileName = '/etc/cfm/%s/opt/lsf/conf/lsf.conf' % row[0]

	    cmd = '/opt/kusu/bin/genconfig %s %s %s' % \
		( LSF_CONF_PLUGIN, self.clusterName, row[1] )

	    os.system("%s >%s.tmp 2>/dev/null" % ( cmd, confFileName ))
	    os.system("cp %s.tmp %s" % ( confFileName, confFileName ))
	    os.system("rm -f %s.tmp" % ( confFileName ))

	    # Update /opt/lsf/ego/kernel/conf/ego.conf
	    confFileName = '/etc/cfm/%s/opt/lsf/ego/kernel/conf/ego.conf' % \
		row[0]

	    cmd = '/opt/kusu/bin/genconfig %s %s %s' % \
		( EGO_CONF_PLUGIN, self.clusterName, row[1] )

	    os.system("%s >%s.tmp 2>/dev/null" % ( cmd, confFileName ))
	    os.system("cp %s.tmp %s" % ( confFileName, confFileName ))
	    os.system("rm -f %s.tmp" % ( confFileName ))

	    if row[1] == 'master':	
	    	# Update /opt/lsf/ego/kernel/conf/ego.cluster.<clustername>
		clusFileName = '/etc/cfm/%s/opt/lsf/ego/kernel/conf/ego.cluster.%s' % \
		    ( row[0], self.clusterName )

	    	cmd = '/opt/kusu/bin/genconfig %s %s' % \
		    ( EGO_CLUSTER_PLUGIN, self.clusterName )

		os.system("%s >%s.tmp 2>/dev/null" % ( cmd, clusFileName ))
		os.system("cp %s.tmp %s" % ( clusFileName, clusFileName ))
		os.system("rm -f %s.tmp" % ( clusFileName ))

		# Update /opt/lsf/ego/kernel/conf/ego.shared
		sharedFileName = '/etc/cfm/%s/opt/lsf/ego/kernel/conf/ego.shared' % ( row[0] )

		cmd = '/opt/kusu/bin/genconfig %s' % self.clusterName

		os.system("%s >%s.tmp 2>/dev/null" % ( cmd, sharedFileName ))
		os.system("cp %s.tmp %s" % ( clusFileName, sharedFileName ))
		os.system("rm -f %s.tmp" % ( sharedFileName ))

	return True
