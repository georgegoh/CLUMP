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
        """Makes the repository for compute and installer nodes."""

        repoid = self.dbs.Repos.select()[0].repoid

        from kusu.repoman.repofactory import RepoFactory
        rfactory = RepoFactory(self.dbs) 
        repoObj = rfactory.getRepo(repoid)

        if self.os_name in ['rhel', 'centos', 'fedora']:
            repoObj.copyKusuNodeInstaller()
            repoObj.makeAutoInstallScript()
 
        return True
