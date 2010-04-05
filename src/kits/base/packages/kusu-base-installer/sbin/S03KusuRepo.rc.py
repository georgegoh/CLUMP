#!/usr/bin/env python
# $Id: S03KusuRepo.rc.py 3135 2009-10-23 05:42:58Z ltsai $
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
        self.desc = 'Preparing repository for compute nodes provisioning'
        self.ngtypes = ['installer']
        self.delete = True

    def run(self):
        """Makes the repository for compute and installer nodes."""

        repoid = self.dbs.Repos.select()[0].repoid

        from kusu.repoman.repofactory import RepoFactory
        rfactory = RepoFactory(self.dbs) 
        repoObj = rfactory.getRepo(repoid)

        repoObj.copyKusuNodeInstaller()
        repoObj.makeAutoInstallScript()
 
        return True
