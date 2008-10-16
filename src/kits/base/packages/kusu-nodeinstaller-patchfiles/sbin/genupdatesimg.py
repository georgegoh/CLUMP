#!/usr/bin/env python

from kusu.core.app import KusuApp
from kusu.core import database
from path import path
import tempfile
import subprocess
import os
class GenUpdatesImg(KusuApp):
    def __init__(self):
        engine =  os.getenv('KUSU_DB_ENGINE')
        if engine == 'mysql':
            dbdriver = 'mysql'
        else:
            dbdriver = 'postgres'
        dbdatabase = 'kusudb'
        dbuser = 'apache'
        dbpassword = None

        self.dbs = database.DB(dbdriver, dbdatabase, dbuser, dbpassword)


    def _updateRepos(self):
        """
        Updates the repos to include the patchfiles and prepare the 
        autoinstall script
        """

        repoid = self.dbs.Repos.select()[0].repoid

        ngs = self.dbs.NodeGroups.select()
        for ng in ngs:
            if ng.ngname == 'unmanaged':
                continue

            ng.repoid = repoid
            ng.save()
            ng.flush()

        from kusu.repoman.repofactory import RepoFactory
        rfactory = RepoFactory(self.dbs) 
        repoObj = rfactory.getRepo(repoid)

        repoObj.copyKusuNodeInstaller()
        repoObj.makeAutoInstallScript()


    def _runCommand(self, cmd):
        p = subprocess.Popen(cmd, shell=True)
        retval = p.wait()
        return retval

    def run(self):
        # create scratchdir
        scratchdir = path(tempfile.mkdtemp('patchfiles-'))
        
        dest = path('/opt/kusu/lib/nodeinstaller')

        self._runCommand('$KUSU_ROOT/lib/nodeinstaller/bin/gen-nodeinstaller-updatesimg -d %s' % scratchdir)
        self._runCommand('cd %s/nodeinstaller && find . | cpio -mpdu %s' % (scratchdir,dest))
        
        if scratchdir.exists(): scratchdir.rmtree()
        
        self._updateRepos()

if __name__ == "__main__":
    app = GenUpdatesImg()
    app.run()
