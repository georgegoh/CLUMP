#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core import rcplugin

class KusuRC(rcplugin.Plugin):

    def __init__(self):
        rcplugin.Plugin.__init__(self)
        self.name = 'repos'
        self.desc = 'Setting up additional repository'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Makes the repoistory for compute and installer nodes."""

        repoid = self.dbs.Repos.select()[0].repoid

        ngs = self.dbs.NodeGroups.select()
        for ng in ngs:
            if ng.ngname == 'unmanaged':
                continue

            ng.repoid = repoid
            ng.save()
            ng.flush()

        return True
