#!/usr/bin/env python

from kusu.core.app import KusuApp
from kusu.core import database
from path import path
import tempfile
import subprocess
import os
from primitive.system.software.dispatcher import Dispatcher
from kusu.repoman.repofactory import RepoFactory
from kusu.repoman.genupdates import GenUpdatesFactory

class GenUpdatesImg(KusuApp):
    def __init__(self):
        KusuApp.__init__(self)
        
        dbdriver =  os.getenv('KUSU_DB_ENGINE', 'postgres')
        dbdatabase = 'kusudb'
        dbuser = 'apache'
        
        self.dbs = database.DB(dbdriver, dbdatabase, dbuser)

        self.parser.add_option('-r', '--repoid', action='store', help='Target repository id')

    def parse(self):
        options, args = self.parser.parse_args()
        try:
            self.repoid = int(options.repoid)
        except ValueError:
            print 'Non-integer repository id is not supported.'
            return False
        return True

    def verify(self):
        try:
            self.dbs.Repos.selectone_by(repoid=self.repoid)
        except Exception, e:
            print e
            return False


    def _runCommand(self, cmd):
        p = subprocess.Popen(cmd, shell=True)
        retval = p.wait()
        return retval

    def run(self):
        if not self.parse():
            return

        if self.repoid is None:
            self.repoid = self.dbs.Repos.select()[0].repoid
        
        elif not self.verify():
            return
        
        # create scratchdir
        scratchdir = path(tempfile.mkdtemp('patchfiles-'))
        
        dest = path('/opt/kusu/lib/nodeinstaller')
       
        os = self.dbs.Repos.selectone_by(repoid=self.repoid).os
        target = (os.name, os.major+'.'+os.minor, os.arch)
        
        updater = GenUpdatesFactory().getUpdatesClass(target_os=target)
        try:
            updater.doGenUpdates(str(scratchdir))
        except Exception, e:
            print e
            if scratchdir.exists():
                scratchdir.rmtree()
            return
       
        self._runCommand('cd %s/nodeinstaller && find . | cpio -mpdu %s' % (scratchdir, dest))
        
        if scratchdir.exists():
            scratchdir.rmtree()
       
        rfactory = RepoFactory(self.dbs)
        repoObj = rfactory.getRepo(self.repoid)
        repoObj.copyKusuNodeInstaller()
        repoObj.makeAutoInstallScript()

if __name__ == "__main__":
    app = GenUpdatesImg()
    app.run()
