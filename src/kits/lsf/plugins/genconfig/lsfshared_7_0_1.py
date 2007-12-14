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

    def getLSFConfDir(self, clusterName):
        lsfMasterNodegroup = self.getLsfMasterNodegroup(clusterName)
        if not lsfMasterNodegroup:
            return None

        return "/etc/cfm/%s/opt/lsf/conf" % ( lsfMasterNodegroup )

    # Using an existing file as a template, update the lsf.shared file
    def generateLSFSharedFile(self, clusterName):
        lsfConfDir = self.getLSFConfDir(clusterName)
        if not lsfConfDir:
            return False

        lsfSharedFile = lsfConfDir + "/lsf.shared"

        try:
            fp = open(lsfSharedFile, 'r')
        except:
            # Error: unable to open lsf.shared file for reading
            return False

        inClusterSection = False

        while True:
            instr = fp.readline()
            if instr == "":
                break

            if instr[:1] == '#':
                print instr,
                continue

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
                        print clusterName
                        continue

            print instr,

        fp.close()

        # Success!
        return True

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

        if not self.generateLSFSharedFile(pluginargs[0]):
            sys.exit(-1)
