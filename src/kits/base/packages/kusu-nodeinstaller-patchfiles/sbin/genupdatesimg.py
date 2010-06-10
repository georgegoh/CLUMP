#!/usr/bin/env python

from kusu.core.app import KusuApp
from kusu.core import database
from path import path
import tempfile
import subprocess
import os
import sys
from primitive.system.software.dispatcher import Dispatcher
from kusu.repoman.repofactory import RepoFactory
from kusu.repoman.genupdates import GenUpdatesFactory
from kusu.repoman import tools

class GenUpdatesImg(KusuApp):
    def __init__(self):
        KusuApp.__init__(self)

        dbdriver =  os.getenv('KUSU_DB_ENGINE', 'postgres')

        if dbdriver == 'postgres':
            dbdatabase = 'kusudb'
            dbuser = 'apache'
            self.dbs = database.DB(dbdriver, dbdatabase, dbuser)
        elif dbdriver == 'sqlite':
            if os.path.exists('/root/kusu.db'):
                self.dbs = database.DB(dbdriver, '/root/kusu.db')
            else:
                sys.stderr.write('SQLite database was not found.\n')
                sys.exit(1)

        provision = self.dbs.AppGlobals.select_by(kname = 'PROVISION')[0].kvalue
        if provision and provision.lower() != 'kusu':
            sys.stderr.write('Kusu provisioning has been disabled. genupdatesimg will not run.\n')
            sys.exit(1)

        self.parser.add_option('-r', '--repoid', action='store', help='Target repository id')


    def parse(self):
        options, args = self.parser.parse_args()

        if options.repoid is None:
            print 'Please provide a target repository id using -r/--repoid option.'
            return False
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

        return True

    def _runCommand(self, cmd):
        p = subprocess.Popen(cmd, shell=True)
        retval = p.wait()
        return retval

    def packUpdatesImg(self, repoid, updater, os, sdir):        
        os_kit = self.dbs.Repos.selectone_by(repoid=self.repoid).oskit

        if not os_kit:
            return 

        os_updatesimg = path('/depot/kits/%s/images/updates.img' % os_kit.kid)
        if os_updatesimg.exists():
            gen_updatesimg = sdir / os.name / os.major / os.arch / 'updates.img'
            updater.repackUpdatesImg(os_updatesimg, gen_updatesimg)

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
        os_version = tools.getEffectiveOSVersion(self.dbs, self.repoid)
        target = (os.name, os_version, os.arch)
         
        updater = GenUpdatesFactory().getUpdatesClass(target_os=target)
        try:
            updater.doGenUpdates(str(scratchdir))
        except Exception, e:
            print e
            if scratchdir.exists():
                scratchdir.rmtree()
            return

        if target[0] in ['scientificlinux', 'scientificlinuxcern']:
            self.packUpdatesImg(self.repoid, updater, os, scratchdir/'nodeinstaller')       

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
