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
import sys
import subprocess
from syslog import syslog
from kusu.addhost import *

LSF_VERSION = '7.0.2'

LSF_VERSION_WITH_UNDERSCORES = LSF_VERSION.replace('.', '_')

EGO_VERSION = '1.2'

EGO_VERSION_WITH_UNDERSCORES = EGO_VERSION.replace('.', '_')

COMPONENT_NAME = "component-LSF-Master-v%s" % ( LSF_VERSION_WITH_UNDERSCORES )

CLUSTER_NAME_KEY = 'LSF%s_ClusterName' % ( LSF_VERSION_WITH_UNDERSCORES )

LSF_CLUSTER_PLUGIN = 'lsfcluster_%s' % ( LSF_VERSION_WITH_UNDERSCORES )

LSF_HOSTS_PLUGIN = 'lsfhosts_%s' % ( LSF_VERSION_WITH_UNDERSCORES )

LSF_CONF_PLUGIN = 'lsfconf_%s' % ( LSF_VERSION_WITH_UNDERSCORES )

EGO_CONF_PLUGIN = 'egoconf_%s' % ( EGO_VERSION_WITH_UNDERSCORES )

LSF_SHARED_PLUGIN = 'lsfshared_%s' % ( LSF_VERSION_WITH_UNDERSCORES )

LSF_CLUSTER_KNAME = 'LSF%s_ClusterName' % ( LSF_VERSION_WITH_UNDERSCORES )

class AddHostPlugin(AddHostPluginBase):
    """LSF cluster file updater plugin"""

    def enabled(self):
        return True

    def getClusterName(self, ngid):
        clusterName = None

        try:
            sql = ('SELECT kvalue FROM appglobals WHERE '
                'kname = \'%s\' AND ngid=%d' % 
                    ( CLUSTER_NAME_KEY, ngid ))

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

        sql = ("SELECT nodegroups.ngname,nodegroups.ngid FROM "
            "nodegroups, components, ng_has_comp, appglobals WHERE "
            "components.cname = \"%s\" AND "
            "components.cid = ng_has_comp.cid AND "
            "ng_has_comp.ngid = appglobals.ngid AND "
            "nodegroups.ngid = appglobals.ngid AND "
            "appglobals.kvalue = \"%s\"" % ( COMPONENT_NAME, clusterName ))

        try:
            self.dbconn.execute(sql)

            row = self.dbconn.fetchone()

            return (row[0], row[1])
        except:
            return (None, 0)

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
        """
        Return a list of all nodegroups that have the LSF components in
        use.
        """

        query = 'SELECT nodegroups.ngname FROM ' \
            'nodegroups, ng_has_comp, components WHERE ' \
            'nodegroups.ngid = ng_has_comp.ngid AND ' \
            'ng_has_comp.cid = components.cid AND ' \
            'components.cname = "%s"' % ( COMPONENT_NAME )

        try:
            self.dbconn.execute(query)
            return list(self.dbconn.fetchall())
        except:
            return []

    # Redirect the output of 'cmd' to a temporary file, and replace the
    # original file only if 'cmd' was successful.
    def safeFileUpdate(self, cmd, destFileName):
        cmdLine = cmd + " >%s.tmp 2>/dev/null" % ( destFileName )

        try:
            retcode = subprocess.call(cmdLine, shell=True)
            if retcode != 0:
                return False
        except OSError, e:
            # Error updating file
            return False

        # Copy temporary file into place
        cmdLine = "cp %s.tmp %s" % ( destFileName, destFileName )

        try:
            retcode = subprocess.call(cmdLine, shell=True)
        except OSError, e:
            pass

        # Remove duplicate file
        cmdLine = "rm -f %s.tmp" % ( destFileName )

        try:
            retcode = subprocess.call(cmdLine, shell=True)
        except OSError, e:
            pass

        return True

    def updHostsFile(self, hostsFileName):
        cmd = '/opt/kusu/bin/genconfig %s %s' % \
            ( LSF_HOSTS_PLUGIN, self.clusterName )

        return self.safeFileUpdate(cmd, hostsFileName)

    def updLSFConfFile(self, lsfConfFileName, type):
        cmd = '/opt/kusu/bin/genconfig %s %s %s' % \
            ( LSF_CONF_PLUGIN, self.clusterName, type )

        return self.safeFileUpdate(cmd, lsfConfFileName)

    def updEGOConfFile(self, egoConfFileName, type):
        cmd = '/opt/kusu/bin/genconfig %s %s %s' % \
            ( EGO_CONF_PLUGIN, self.clusterName, type )

        return self.safeFileUpdate(cmd, egoConfFileName)

    def updLSFClusterFile(self, clusFileName):
        cmd = '/opt/kusu/bin/genconfig %s %s' % \
            ( LSF_CLUSTER_PLUGIN, self.clusterName )

        return self.safeFileUpdate(cmd, clusFileName)

    def updLSFSharedFile(self, sharedFileName):
        cmd = '/opt/kusu/bin/genconfig %s %s' % \
            ( LSF_SHARED_PLUGIN, self.clusterName )

        return self.safeFileUpdate(cmd, sharedFileName)

    def updateLSFConfig(self):
        """
        Update all LSF configuration files for the nodes in the cluster.
        This includes the master candidates and any compute nodegroups.
        """

        # Find all nodegroups that have nodes in this cluster
        sql = ("SELECT nodegroups.ngname, "
            "IF(nodegroups.ngid = %d, 'master', 'slave') FROM "
            "nodegroups, appglobals WHERE kvalue = \"%s\" AND "
            "kname = \"%s\" AND "
            "nodegroups.ngid = appglobals.ngid" % \
                ( self.masterNgId, self.clusterName, LSF_CLUSTER_KNAME ))

        try:
            self.dbconn.execute(sql)
        except:
            return False

        # Update the hosts file
        for row in self.dbconn.fetchall():
            print 'Updating configuration for nodegroup %s' % ( row[0] )

            cfmTopDir = "/etc/cfm/" + row[0]

            # Update /opt/lsf/conf/hosts
            hostsFileName = cfmTopDir + '/opt/lsf/conf/hosts'
            self.updHostsFile(hostsFileName)

            # Update /opt/lsf/conf/lsf.conf
            confFileName = cfmTopDir + '/opt/lsf/conf/lsf.conf'
            self.updLSFConfFile(confFileName, row[1])

            # Update /opt/lsf/ego/kernel/conf/ego.conf
            confFileName = cfmTopDir + '/opt/lsf/conf/ego/%s/kernel/ego.conf' % \
                ( self.clusterName )
            self.updEGOConfFile(confFileName, row[1])

            if row[1] == 'master':    
                # Update /opt/lsf/conf/lsf.cluster.<clustername>
                clusFileName = cfmTopDir + '/opt/lsf/conf/lsf.cluster.%s' % \
                    ( self.clusterName )
                self.updLSFClusterFile(clusFileName)

                # Update /opt/lsf/conf/lsf.shared
                sharedFileName = cfmTopDir + '/opt/lsf/conf/lsf.shared'
                self.updLSFSharedFile(sharedFileName)

        # Success!
        return True
