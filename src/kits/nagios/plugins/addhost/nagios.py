#!/usr/bin/env python
# $Id: kitops.py 2412 2007-09-29 03:30:56Z mike $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
try:
    import subprocess
except:
    from popen5 import subprocess

import sqlalchemy as sa
import kusu.core.database as db

from kusu.addhost import *

class AddHostPlugin(AddHostPluginBase):
    def finished(self, nodelist, prePopulateMode):
        # Select all nodes, along with their nodegroup and nodegroup type.
        self.dbconn.execute("SELECT nodegroups.ngname, nodegroups.type, " + \
                            "       nodes.name " + \
                            "FROM nodegroups, nodes " + \
                            "WHERE nodegroups.ngid = nodes.ngid")
        rs = self.dbconn.fetchall()

        ngs = {}
        for r in rs:
            if r[0] not in ngs:
                ngs[r[0]] = {'type': r[1], 'nodes': []}
            ngs[r[0]]['nodes'].append(r[2])

        # Which nodegroups have component-installer-nagios?
        self.dbconn.execute("SELECT nodegroups.ngname " +
                        "FROM nodegroups, ng_has_comp, components " +
                        "WHERE nodegroups.ngid = ng_has_comp.ngid " +
                        "AND ng_has_comp.cid = components.cid " +
                        "AND components.cname = 'component-installer-nagios'")
        nagios_ngs = self.dbconn.fetchall()
        for nagios_ng in nagios_ngs:
            f = open('/etc/cfm/%s/etc/nagios_pickle.cfg' % nagios_ng[0], 'w')
            import cPickle
            pickled = cPickle.dump(ngs, f)
            f.close()

        # Grab the IPs of any nagios monitoring nodes.
        self.dbconn.execute("SELECT nics.ip " +
                        "FROM nics, nodes, ng_has_comp, components " +
                        "WHERE nics.nid = nodes.nid " +
                        "AND nodes.ngid = ng_has_comp.ngid " +
                        "AND ng_has_comp.cid = components.cid " +
                        "AND components.cname = 'component-installer-nagios'")
        nagios_ips = ' '.join([x[0] for x in self.dbconn.fetchall()])

        # Which nodegroups have component-compute-nagios?
        self.dbconn.execute("SELECT nodegroups.ngname " +
                        "FROM nodegroups, ng_has_comp, components " +
                        "WHERE nodegroups.ngid = ng_has_comp.ngid " +
                        "AND ng_has_comp.cid = components.cid " +
                        "AND components.cname = 'component-compute-nagios'")
        nagios_ngs = self.dbconn.fetchall()
        for nagios_ng in nagios_ngs:
            f = open('/etc/cfm/%s/etc/nagios_monitor_ips.cfg' % nagios_ng[0], 'w')
            f.write(nagios_ips)
            f.close()

        # Now, sync the pickled file to all the nodes
        cmds = ['cfmsync', '-f']
        cfmsyncP = subprocess.Popen(cmds, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        # We launch the cfmsync process and cross our fingers it completes;
        # we won't wait until it's done.
        #out, err = cfmsyncP.communicate()
