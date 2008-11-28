#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin 

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'No Partitions Preserved For Node Groups'
        self.desc = 'Removing preservation rules from node group partitions'
        self.ngtypes = ['installer']
        self.delete = False

    def run(self):
        compute_ngs = self.dbs.NodeGroups.select_by(type='compute')
        for ng in compute_ngs:
            for p in self.dbs.Partitions.select_by(ngid=ng.ngid,
                                                   options='partitionID=Dell Utility'):
                p.delete()
                p.flush()
        return True
