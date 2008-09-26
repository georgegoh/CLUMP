#!/usr/bin/env python
# $Id: S02KusuRepo.rc.py 2190 2007-09-10 07:54:35Z ltsai $
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

        from kusu.repoman.repofactory import RepoFactory
        rfactory = RepoFactory(self.dbs) 
        repoObj = rfactory.getRepo(repoid)

        repoObj.copyKusuNodeInstaller()
        repoObj.makeAutoInstallScript()
 
        return True
