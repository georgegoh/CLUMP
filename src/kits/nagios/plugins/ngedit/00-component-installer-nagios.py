#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

try:
    import subprocess
except:
    from popen5 import subprocess

from path import path

from kusu.ngedit.ngedit import NGEPluginBase
#from kusu.nagios.plugins import NagiosConfigHelper, \
#                                NAGIOS_CFM_DIR, \
#                                NAGIOS_PICKLE_FILENAME

### Code below comes from nagios_lib.py. Replicated here until buildkit can
### package arbitrary files in the kit RPM.
import cPickle

NAGIOS_CFM_DIR = '/etc/cfm/%s/etc/nagios'
NAGIOS_PICKLE_FILENAME = 'nagios.pickle'

class NagiosConfigHelper(object):
    def __init__(self, database):
        super(NagiosConfigHelper, self).__init__()
        self.database = database

    def generate_nagios_config(self, this_host=None):
        # Select all nodes, along with their nodegroup and nodegroup type
        # if 'component-compute-nagios' is associated with it.
        self.database.execute("SELECT nodegroups.ngname, nodegroups.type, " +
                        "             nodes.name " +
                        "FROM nodegroups, nodes, ng_has_comp, components " +
                        "WHERE nodegroups.ngid = nodes.ngid " +
                        "AND nodegroups.ngid = ng_has_comp.ngid " +
                        "AND ng_has_comp.cid = components.cid " +
                        "AND components.cname = 'component-compute-nagios'")
        rs = self.database.fetchall()

        compute_ngs = {}
        for r in rs:
            if r[0] not in compute_ngs:
                compute_ngs[r[0]] = {'type': r[1], 'nodes': []}
            compute_ngs[r[0]]['nodes'].append(r[2])

        # Which nodegroups have component-installer-nagios?
        self.database.execute("SELECT nodegroups.ngname, nodegroups.type, " +
                        "             nodes.name " +
                        "FROM nodegroups, nodes, ng_has_comp, components " +
                        "WHERE nodegroups.ngid = nodes.ngid " +
                        "AND nodegroups.ngid = ng_has_comp.ngid " +
                        "AND ng_has_comp.cid = components.cid " +
                        "AND components.cname = 'component-installer-nagios'")
        installer_ngs = self.database.fetchall()
        for installer_ng in installer_ngs:
            # Make a copy of our nodes dictionary and add this node to it.
            ngs = compute_ngs.copy()
            if installer_ng[0] not in ngs:
                ngs[installer_ng[0]] = {'type': installer_ng[1], 'nodes': []}
            ngs[installer_ng[0]]['nodes'].append(installer_ng[2])

            nagios_cfm = path(NAGIOS_CFM_DIR % installer_ng[0])
            if not nagios_cfm.exists(): nagios_cfm.makedirs()
            f = open(nagios_cfm / NAGIOS_PICKLE_FILENAME, 'w')
            pickled = cPickle.dump(ngs, f)
            f.close()
            
            if installer_ng[2] == this_host:
                f = open('/etc/nagios/%s' % NAGIOS_PICKLE_FILENAME, 'w')
                pickled = cPickle.dump(ngs, f)
                f.close()
### End nagios_lib content

class NGPlugin(NGEPluginBase):
    def add(self):
        nch = NagiosConfigHelper(database=self.database)
        nch.generate_nagios_config()

        self.finish()

    def remove(self):
        nch = NagiosConfigHelper(database=self.database)
        nch.generate_nagios_config()

        # Get the nodegroup name.
        self.database.execute("SELECT ngname FROM nodegroups " +
                              "WHERE ngid = %s" % self.ngid)
        ngname = self.database.fetchall()[0][0]
        f = path(NAGIOS_CFM_DIR % ngname)
        if f.exists():
            if (f / NAGIOS_PICKLE_FILENAME).exists():
                (f / NAGIOS_PICKLE_FILENAME).remove()
            if not f.listdir(): f.rmdir()

        self.finish()

    def finish(self):
        # Now, sync the pickled file to all the nodes
        cmds = ['cfmsync', '-f']
        cfmsyncP = subprocess.Popen(cmds, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
