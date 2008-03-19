#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from kusu.repoman import repo
from kusu.repoman.repofactory import RepoFactory
from path import path
import tempfile
import os

from nose import SkipTest

prefix = None
kusudb = None
cachedir = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP']))

def download(filename, dest, cache=cachedir):
    global cachedir

    if (cache / filename).exists():
        (cache / filename).copy(dest)
        return

    import urllib2
    url = 'http://www.osgdc.org/pub/build/tests/modules/repoman/'
    f = urllib2.urlopen(url + filename)
    content = f.read()
    f.close()

    f = open(cache / filename, 'w')
    f.write(content)
    f.close()

    (cache / filename).copy(dest)

def setup():
    global prefix
    global kusudb

    prefix = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP']))
    kusudb = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP'])) / 'kusu.db'

def teardown():
    global kusudb
    global cachedir
 
    kusudb.parent.rmtree()
    cachedir.rmtree()

class TestFedora6Repo:

    def setUp(self):
        global prefix
        global kusudb
        
        self.dbs = db.DB('sqlite', kusudb)
        self.dbs.createTables()
    
        # Network
        network = db.Networks()
        network.network = '10.0.0.0'
        network.subnet = '255.0.0.0'
        network.device = 'eth0'
        network.type = 'provision'
        network.save()
        network.flush()

        # nodegroup
        node = db.Nodes(name='master-0')
        self.masterIP = '10.1.1.1'
        node.nics.append(db.Nics(ip=self.masterIP, netid=network.netid))

        installer = db.NodeGroups(ngname='installer nodegroup',
                                  type='installer') 
        installer.nodes.append(node)
        installer.save()
        installer.flush()

        # Kits + components
        osKit = db.Kits()
        osKit.rname = 'fedora'
        osKit.version = '6'
        osKit.arch = 'i386'
        osKit.isOS = True
        osComp = db.Components(cname='fedora-6-i386')
        osKit.components.append(osComp)
        osKit.save()
        osKit.flush()

        baseKit = db.Kits()
        baseKit.rname = 'base'
        baseKit.version = '0.1'
        baseKit.arch = 'noarch'
        baseKit.isOS = False
        baseComp = db.Components(cname='base-installer')
        baseKit.components.append(baseComp, db.Components(cname='base-node'))
        baseKit.save()
        baseKit.flush()

        installer.components.append(osComp)
        installer.components.append(baseComp)
        installer.save() 
        installer.flush()

        appglobals = db.AppGlobals(kname='PrimaryInstaller', kvalue='master-0')
        appglobals.save()
        appglobals.flush()

        dirs = []
        dirs.append(prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch')
        dirs.append(prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'fedora' / '6' / 'i386')
       
        for dir in dirs:
            dir.makedirs()

        (prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch' / 'kitinfo').touch()
        (prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'fedora' / '6' / 'i386' / 'updates.img').touch()

        for p in self.getPath():
            new_path = prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / p
            try:
                new_path.parent.makedirs()
            except: pass

            if not new_path.isdir():    
                new_path.touch()

        download('comps.xml', \
                 prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'repodata' / 'comps.xml')

        download('ks.cfg.tmpl', \
                 prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'fedora' / '6' / 'i386' / 'ks.cfg.tmpl')

        download('kernel-2.6.9-22.0.1.EL.i386.rpm', \
                 prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'Fedora' / 'RPMS' / 'kernel-2.6.9-22.0.1.EL.i386.rpm')

        download('kernel-2.6.9-11.EL.i386.rpm', \
                 prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch' / 'kernel-2.6.9-11.EL.i386.rpm')

    def tearDown(self):
        global prefix
        self.dbs.dropTables()
        prefix.rmtree()

    def getPath(self):
        
        paths = ['Fedora/RPMS/',\
                 'Fedora/base/', \
                 'repodata/comps.xml', \
                 'repodata/other.xml.gz', \
                 'repodata/filelists.xml.gz', \
                 'repodata/repomd.xml', \
                 'repodata/primary.xml.gz', \
                 'isolinux/initrd', \
                 'isolinux/vmlinuz', \
                 'images/stage2.img', \
                 'images/updates.img']
        return paths

    def checkLayout(self, prefix):
        for p in self.getPath():
            assert (prefix / p).exists()

    def testDeleteRepo(self):
        raise SkipTest, "FIXME: Test does not work with SQLAlchemy 0.3.11."
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid 

        installer = self.dbs.NodeGroups.select_by(ngname='installer nodegroup')[0]
        installer.repoid = None
        installer.save()
        installer.flush()

        rfactory.delete(repoid)

        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

        assert not self.dbs.Repos.get(repoid)
        assert not len(self.dbs.ReposHaveKits.select_by(repoid=repoid))

    def testMakeUseSameRepo(self):
        global prefix

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

        rfactory = RepoFactory(self.dbs, prefix, True)
        repo1 = rfactory.make('installer nodegroup')

        repo2 = rfactory.make('installer nodegroup 2')
        assert repo1.repoid == repo2.repoid 
        assert len(self.dbs.Repos.select()) == 1

    def testMakeUseSameRepoMissingScript(self):
        global prefix

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

        rfactory = RepoFactory(self.dbs, prefix, True)
        repo1 = rfactory.make('installer nodegroup')

        row = self.dbs.AppGlobals.select_by(kname = 'PrimaryInstaller')
        row = row[0]
        masterNode = self.dbs.Nodes.select_by(name=row.kvalue)[0]

        for nic in masterNode.nics:
            if nic.ip: 
                ip = nic.ip
                (prefix / 'depot' / 'repos' / str(repo1.repoid) / 'ks.cfg.' + ip).unlink()

        repo2 = rfactory.make('installer nodegroup 2')
        assert repo1.repoid == repo2.repoid 
        self.checkLayout(prefix / 'depot' / 'repos' / str(repo2.repoid))

        for nic in masterNode.nics:
            if nic.ip: 
                ip = nic.ip
                assert (prefix / 'depot' / 'repos' / str(repo2.repoid) / 'ks.cfg.' + ip).exists()
        
    def testMake(self):
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')

        repoid = str(r.repoid)
        self.checkLayout(prefix / 'depot' / 'repos' / repoid)
        assert len(self.dbs.Repos.select()) == 1

    def testRefreshRepo(self):
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid
 
        r = rfactory.refresh(ngname='installer nodegroup')

        repoid = str(r.repoid)
        self.checkLayout(prefix / 'depot' / 'repos' / repoid)
        assert len(self.dbs.Repos.select()) == 1

    def testRefreshRepoWithNGType(self):
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid
 
        repos = rfactory.refresh(ngtype=['installer'])

        for r in repos:
            repoid = str(r.repoid)
            self.checkLayout(prefix / 'depot' / 'repos' / repoid)
        assert len(self.dbs.Repos.select()) == 1

    def testRefreshUseSameRepo(self):
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid
 
        r = rfactory.refresh(ngname='installer nodegroup')

        assert repoid == r.repoid
        assert len(self.dbs.Repos.select()) == 1
 
    def testRefreshUseSameRepoWithNGType(self):
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid
 
        repos = rfactory.refresh(ngtype=['installer'])

        assert repoid == repos[0].repoid
        assert len(self.dbs.Repos.select()) == 1
        
    def testRefreshUseSameRepo2(self):
        # New component added to the existing nodegrouip. Since
        # only 1 nodegroup is affected, repo will be refreshed

        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid

        kit = db.Kits()
        kit.rname = 'opengl'
        kit.version = '2.5'
        kit.arch = 'i386'
        kit.isOS = False
        comp = db.Components(cname='component-opengl')
        kit.components.append(comp)
        kit.save()
        kit.flush()
        
        (prefix / 'depot' / 'kits' / 'opengl' /  '2.5' / 'i386').makedirs()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        r = rfactory.refresh(ngname='installer nodegroup')

        # Only 1 nodegroup uses the same repoid
        assert repoid == r.repoid
        assert len(self.dbs.Repos.select()) == 1
        assert len(self.dbs.Repos.select()[0].kits) == 3
   
    def testRefreshUseSameRepo2WithNGType(self):
        # New component added to the existing nodegrouip. Since
        # only 1 nodegroup is affected, repo will be refreshed

        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid

        kit = db.Kits()
        kit.rname = 'opengl'
        kit.version = '2.5'
        kit.arch = 'i386'
        kit.isOS = False
        comp = db.Components(cname='component-opengl')
        kit.components.append(comp)
        kit.save()
        kit.flush()

        (prefix / 'depot' / 'kits' / 'opengl' /  '2.5' / 'i386').makedirs()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        repos = rfactory.refresh(ngtype=['installer'])

        # Only 1 nodegroup uses the same repoid
        assert len(self.dbs.Repos.select()) == 1
        assert len(self.dbs.Repos.select()[0].kits) == 3
        assert repoid == repos[0].repoid
 
    def testRefreshUseSameRepoMultipleNodeGroups(self):
        # New component added to the existing nodegroups. Since
        # only all nodegroups are affected, repo will be refreshed

        global prefix
        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup 2')

        kit = db.Kits()
        kit.rname = 'opengl'
        kit.version = '2.5'
        kit.arch = 'i386'
        kit.isOS = False
        comp = db.Components(cname='component-opengl')
        kit.components.append(comp)
        kit.save()
        kit.flush()
        
        (prefix / 'depot' / 'kits' / 'opengl' /  '2.5' / 'i386').makedirs()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup 2')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        r = rfactory.refresh(ngname='installer nodegroup')

        # All nodegroups use the same repoid
        assert repoid == r.repoid
        assert len(self.dbs.Repos.select()) == 1
        assert len(self.dbs.Repos.select()[0].kits) == 3
 
    def testRefreshUseSameRepoMultipleNodeGroupsWithNGType(self):
        # New component added to the existing nodegroups. Since
        # only all nodegroups are affected, repo will be refreshed

        global prefix
        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repoid = r.repoid

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup 2')

        kit = db.Kits()
        kit.rname = 'opengl'
        kit.version = '2.5'
        kit.arch = 'i386'
        kit.isOS = False
        comp = db.Components(cname='component-opengl')
        kit.components.append(comp)
        kit.save()
        kit.flush()
        
        (prefix / 'depot' / 'kits' / 'opengl' /  '2.5' / 'i386').makedirs()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup 2')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        repos = rfactory.refresh(ngtype=['installer'])

        # All nodegroups use the same repoid
        assert len(self.dbs.Repos.select()) == 1
        assert len(self.dbs.Repos.select()[0].kits) == 3
        assert repoid == repos[0].repoid
 
    def testRefreshUseDifferentRepo(self):
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup 2')
        repoid = r.repoid

        kit = db.Kits()
        kit.rname = 'opengl'
        kit.version = '2.5'
        kit.arch = 'i386'
        kit.isOS = False
        comp = db.Components(cname='component-opengl')
        kit.components.append(comp)
        kit.save()
        kit.flush()

        (prefix / 'depot' / 'kits' / 'opengl' /  '2.5' / 'i386').makedirs()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup 2')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        r = rfactory.refresh(ngname='installer nodegroup 2')

        assert repoid != r.repoid
        assert len(self.dbs.Repos.select()) == 2
        assert len(self.dbs.Repos.select_by(repoid = repoid)[0].kits) == 2
        assert len(self.dbs.Repos.select_by(repoid = r.repoid)[0].kits) == 3

    def testRefreshUseDifferentRepoWithNGType(self):
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        
        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup 2')
        repoid = r.repoid

        kit = db.Kits()
        kit.rname = 'opengl'
        kit.version = '2.5'
        kit.arch = 'i386'
        kit.isOS = False
        comp = db.Components(cname='component-opengl')
        kit.components.append(comp)
        kit.save()
        kit.flush()

        (prefix / 'depot' / 'kits' / 'opengl' /  '2.5' / 'i386').makedirs()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup 2')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        repos = rfactory.refresh(ngtype=['installer'])

        assert len(repos) == 2
        assert repoid == self.dbs.NodeGroups.select_by(ngname='installer nodegroup')[0].repoid
        assert repoid != self.dbs.NodeGroups.select_by(ngname='installer nodegroup 2')[0].repoid

        for r in repos:
            assert r.repoid in [self.dbs.NodeGroups.select_by(ngname='installer nodegroup')[0].repoid,
                                self.dbs.NodeGroups.select_by(ngname='installer nodegroup 2')[0].repoid]
        assert len(self.dbs.Repos.select()) == 2
        assert len(self.dbs.Repos.select()[0].kits) == 2
        assert len(self.dbs.Repos.select()[1].kits) == 3
 
    def testRefreshWithOldRepoDeleted(self):
        raise SkipTest, "FIXME: Test does not work with SQLAlchemy 0.3.11."
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup 2')
        repoid = r.repoid

        kit = db.Kits()
        kit.rname = 'opengl'
        kit.version = '2.5'
        kit.arch = 'i386'
        kit.isOS = False
        comp = db.Components(cname='component-opengl')
        kit.components.append(comp)
        kit.save()
        kit.flush()

        (prefix / 'depot' / 'kits' / 'opengl' /  '2.5' / 'i386').makedirs()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup 2')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()
        r2 = rfactory.refresh(ngname='installer nodegroup 2')

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()
        r1 = rfactory.refresh(ngname='installer nodegroup')

        assert r1.repoid == r2.repoid
        assert not self.dbs.Repos.get(repoid)
        assert len(self.dbs.Repos.select()) == 1

    def testRefreshWithOldRepoDeletedWithNGType(self):
        raise SkipTest, "FIXME: Test does not work with SQLAlchemy 0.3.11."
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        
        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup 2')
        repoid = r.repoid
        
        kit = db.Kits()
        kit.rname = 'opengl'
        kit.version = '2.5'
        kit.arch = 'i386'
        kit.isOS = False
        comp = db.Components(cname='component-opengl')
        kit.components.append(comp)
        kit.save()
        kit.flush()

        (prefix / 'depot' / 'kits' / 'opengl' /  '2.5' / 'i386').makedirs()

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup 2')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()

        repos = rfactory.refresh(ngtype=['installer'])

        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.components.append(comp)
        ng.save()  
        ng.flush()
        
        repos = rfactory.refresh(ngtype=['installer'])

        assert len(repos) == 2
        assert repos[0].repoid == repos[1].repoid
        assert not self.dbs.Repos.get(repoid)
        assert len(self.dbs.Repos.select()) == 1

    def testGetRepo(self):
        global prefix

        rfactory = RepoFactory(self.dbs, prefix, True)
        r = rfactory.make('installer nodegroup')
        repo = rfactory.getRepo(r.repoid)

        assert repo.os_name == 'fedora'
        assert repo.os_version == '6'
        assert repo.os_arch == 'i386'
        assert repo.repoid == r.repoid
        assert repo.repo_path == prefix / 'depot' / 'repos' / str(r.repoid)
        assert repo.os_path == prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386'
