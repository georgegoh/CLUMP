#/usr/bin/env python

from primitive.updatetool import you
from primitive.fetchtool.commands import FetchCommand

from path import path
import tempfile

class TestUpdatedPackages:

    def setUp(self):
        self.you = you.YouUpdate(username='test', password='test', \
                                 channel='SLES10-SP2-Updates', arch='i586', \
                                 uri='https://%s:%s@www.osgdc.org/pub/build/tests/modules/primitive/updatetool-protected/repo/$RCE') 

        self.dir = path(tempfile.mkdtemp(prefix='youtest', dir='/tmp'))
        (self.dir / 'suse' / 'i586').makedirs()
        (self.dir / 'suse' / 'i686').makedirs()
        (self.dir / 'suse' / 'noarch').makedirs()

    def tearDown(self):
        if self.dir.exists(): self.dir.rmtree()

    def testUpdatePackages(self):
        packages = self.you.getUpdates(self.dir)

        assert len(packages) == 2

        for p in packages:
            assert p.name in ['python-ipy', 'createrepo']
                
    def testUpdatePackagesWithExistingRPMS(self):

        url = 'https://test:test@www.osgdc.org/pub/build/tests/modules/primitive/updatetool-protected/repo/$RCE/SLES10-SP2-Updates/sles-10-i586/rpm/i586'
        fc = FetchCommand(uri= url + '/python-ipy-0.56-1.2.i586.rpm',
                          fetchdir=False,
                          destdir=self.dir / 'suse' / 'i586',
                          overwrite=False)
        status, dest = fc.execute()
        
        packages = self.you.getUpdates(self.dir)
        assert len(packages) == 1
        assert packages[0].name == 'createrepo'
 
