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

class NGPlugin(NGEPluginBase):
    def add(self):
        # Select all nodes, along with their nodegroup and nodegroup type.
        self.database.execute("SELECT nodegroups.ngname, nodegroups.type, " + \
                            "       nodes.name " + \
                            "FROM nodegroups, nodes " + \
                            "WHERE nodegroups.ngid = nodes.ngid")
        rs = self.database.fetchall()

        ngs = {}
        for r in rs:
            if r[0] not in ngs:
                ngs[r[0]] = {'type': r[1], 'nodes': []}
            ngs[r[0]]['nodes'].append(r[2])

        # Get the nodegroup name.
        self.database.execute("SELECT ngname FROM nodegroups " +
                              "WHERE ngid = %s" % self.ngid)
        ngname = self.database.fetchall()[0][0]
        f = open('/etc/cfm/%s/etc/nagios_pickle.cfg' % ngname, 'w')
        import cPickle
        pickled = cPickle.dump(ngs, f)
        f.close()

        self.finish()

    def remove(self):
        # Get the nodegroup name.
        self.database.execute("SELECT ngname FROM nodegroups " +
                              "WHERE ngid = %s" % self.ngid)
        ngname = self.database.fetchall()[0][0]
        f = path('/etc/cfm/%s/etc/nagios_pickle.cfg' % ngname)
        if f.exists(): f.remove()

        self.finish()

    def finish(self):
        self.generate_nagios_nrpe_config()

        # Now, sync the pickled file to all the nodes
        cmds = ['cfmsync', '-f']
        cfmsyncP = subprocess.Popen(cmds, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

    def generate_nagios_nrpe_config(self):
        # Grab the IPs of any nagios monitoring nodes.
        self.database.execute("SELECT nics.ip " +
                        "FROM nics, nodes, ng_has_comp, components " +
                        "WHERE nics.nid = nodes.nid " +
                        "AND nodes.ngid = ng_has_comp.ngid " +
                        "AND ng_has_comp.cid = components.cid " +
                        "AND components.cname = 'component-installer-nagios'")
        nagios_ips = ' '.join([x[0] for x in self.database.fetchall()])

        # Which nodegroups have component-compute-nagios?
        self.database.execute("SELECT nodegroups.ngname " +
                        "FROM nodegroups, ng_has_comp, components " +
                        "WHERE nodegroups.ngid = ng_has_comp.ngid " +
                        "AND ng_has_comp.cid = components.cid " +
                        "AND components.cname = 'component-compute-nagios'")
        nagios_ngs = self.database.fetchall()
        for nagios_ng in nagios_ngs:
            f = open('/etc/cfm/%s/etc/nagios_monitor_ips.cfg' % nagios_ng[0],   'w')
            f.write(nagios_ips)
            f.close()
