#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.core.plugin import Plugin

class KusuRC(Plugin):

    def __init__(self):
        Plugin.__init__(self)
        self.name = 'repos'
        self.desc = 'Setting up additional repository'

    def run(self):
        """Makes the repoistory for compute and installer nodes."""

        from kusu.repoman.repofactory import RepoFactory

        rfactory = RepoFactory(self.dbs)
        longname = '%s-%s-%s' % (self.os_name, self.os_version, self.os_arch)

        try:
            ngname = 'compute' + '-' + longname
            rfactory.make(ngname, 'Repo for ' + ngname)
        except: pass

        try:
            ngname = 'compute-diskless' + '-' + longname
            rfactory.make(ngname, 'Repo for ' + ngname)
        except: pass
        
        try:
            ngname = 'compute-imaged' + '-' + longname
            rfactory.make(ngname, 'Repo for ' + ngname)
        except: pass

        return True
