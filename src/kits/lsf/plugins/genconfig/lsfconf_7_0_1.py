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

# Generate node and master configs, don't check if the file exists.

from kusu.genconfig import Report

import os
import string
import sys
import re

global APPKEY
APPKEY   = "LSF7_0_1_ClusterName"

COMP_MASTER = "component-LSF-Master-v7_0_1"

LSF_TMPLDIR = "/etc/cfm/templates/lsf"

class ClusterInfo:
    pass

class thisReport(Report):

    def toolHelp(self):
        print self.gettext("genconfig_LSFconf_Help")

    def validateCluster(self, clustername):
        global APPKEY

        ci = ClusterInfo()
        ci.clusterName = clustername

        query = ('select ngid from appglobals where kname="%s" '
             'and kvalue="%s"' % (APPKEY, ci.clusterName)) 
        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)

        row = self.db.fetchone()

        if not row:
            return None

        if row[0] != '':
            ci.masterCandidateNGID = int(row[0])
            return ci

        return None

    def getMasterCandidateList(self, ci):
        query = 'SELECT name FROM nodes, nodegroups WHERE nodes.ngid = %d AND nodes.ngid = nodegroups.ngid' % ( ci.masterCandidateNGID )

        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            sys.exit(-1)

        l = []
        for row in self.db.fetchall():
            l.append(row[0])

        if not l:
            print '# No master hosts defined for cluster'
            sys.exit(-1)

        return ' '.join(l)

    def getLsfMasterNodegroup(self, clusterName):
        query = ('SELECT ngname FROM '
            'nodegroups, appglobals, ng_has_comp, components '
            'WHERE appglobals.ngid=nodegroups.ngid AND '
            'nodegroups.ngid=ng_has_comp.ngid AND '
            'ng_has_comp.cid=components.cid AND '
            'components.cname="%s" AND appglobals.kvalue="%s"' % \
                (COMP_MASTER, clusterName))

        try:
            self.db.execute(query)
        except:
            sys.stderr.write(self.gettext("DB_Query_Error\n"))
            return None

        try:
            row = self.db.fetchone()
        except:
            return None

        return row[0]

    def generateLsfConfig(self, ci, mode):
        # Determine location of the configuration file based on the
        # nodegroup.

        lsfConfFileName = LSF_TMPLDIR + "/default.lsf.conf.%s" % ( mode )

        # Ensure LSF configuration file exists
        if not os.path.exists(lsfConfFileName):
            # default.lsf.conf.<mode> does not exist, attempt to fallback
            # to default.lsf.conf
            lsfConfFileName = LSF_TMPLDIR + "/default.lsf.conf"
            if not os.path.exists(lsfConfFileName):
                return False

        installerName = self.db.getAppglobals('PrimaryInstaller')

        dnsZone = self.db.getAppglobals('DNSZone')

        mcList = self.getMasterCandidateList(ci)

        try:
            fin = open(lsfConfFileName, "r")
        except:
            return False

        while True:
            instr = fin.readline()
            if instr == '':
                break

            if re.compile("^LSF_MASTER_LIST=").search(instr):
                print "LSF_MASTER_LIST=\"%s\"" % ( mcList )
                continue

            if mode == "master":
                if re.compile("^LSB_MAILTO").search(instr):
                    print """LSB_MAILTO=!U@%s.%s
LSB_MAILSERVER=SMTP:%s.%s""" % ( installerName, dnsZone, installerName, dnsZone )
                    continue

            if re.compile("^LSF_EGO_ENVDIR=").search(instr):
                print "LSF_EGO_ENVDIR=/opt/lsf/conf/ego/%s/kernel" % \
                    ( ci.clusterName )
                continue

            if re.compile("^EGO_WORKDIR=").search(instr):
                print "EGO_WORKDIR=/opt/lsf/work/%s/ego" % \
                    ( ci.clusterName )
                continue

            print instr,

        fin.close()

        if mode == "slave":
            print """LSF_GET_CONF=LIM"""

        return True

    def runPlugin(self, pluginargs):
        if not pluginargs:
            print "# ERROR:  No LSF cluster provided!"
            print self.gettext("genconfig_LSFconf_Help")
            return

        if pluginargs[0] == '':
            print "# ERROR:  No LSF cluster provided!"
            print self.gettext("genconfig_LSFconf_Help")
            return
        
        ci = self.validateCluster(pluginargs[0])
        if not ci:
            print "# ERROR:  Invalid LSF clustername: %s" % pluginargs[0]
            return

        generate = 'master'
        if len(pluginargs) > 1:
            if pluginargs[1] == 'master':
                generate = 'master'
            if pluginargs[1] == 'slave':
                generate = 'slave'

        if not self.generateLsfConfig(ci, mode = generate):
            sys.exit(-1)
