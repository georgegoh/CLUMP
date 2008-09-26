#!/usr/bin/env python
# $Id: repoman_app_test.py 476 2008-01-25 12:36:55Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from kusu.repoman import repo
from path import path
import tempfile
import os
from nose import SkipTest

prefix = None
kusudb = None
cachedir = path(tempfile.mkdtemp(prefix='repoman_app', dir=os.environ['KUSU_TMP']))

try:
    import subprocess
except:
    from popen5 import subprocess

def runCommand(cmd):
    p = subprocess.Popen(cmd,
                 shell=True,
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE)
    rv = p.wait()
    return p.stdout.read(), p.stderr.read(), rv

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

def setUp():
    global prefix
    global kusudb

    prefix = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP']))
    kusudb = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP'])) / 'kusu.db'

def tearDown():
    global kusudb
    global cachedir
 
    kusudb.parent.rmtree()
    cachedir.rmtree()

class TestRepoman:
    def setUp(self):
        global prefix
        global kusudb

        dbs = db.DB('sqlite', kusudb)
        self.dbs = dbs
        dbs.createTables()

        # Network
        network1 = dbs.Networks()
        network1.network = '10.0.0.0'
        network1.subnet = '255.0.0.0'
        network1.device = 'eth0'
        network1.type = 'public'
        network1.save()
        network1.flush()

        network2 = dbs.Networks()
        network2.network = '192.168.1.0'
        network2.subnet = '255.255.255.0'
        network2.device = 'eth1'
        network2.type = 'provision'
        network2.save()
        network2.flush()

        # nodegroup
        node = dbs.Nodes(name='master-0')
        masterIP1 = '10.1.1.1'
        masterIP2 = '192.168.1.1'
        node.nics.append(dbs.Nics(ip=masterIP1, netid=network1.netid))
        node.nics.append(dbs.Nics(ip=masterIP2, netid=network2.netid))

        installer = dbs.NodeGroups(ngname='installer nodegroup',
                                  type='installer') 
        installer.nodes.append(node)
        installer.save()
        installer.flush()

        # Kits + components
        osKit = dbs.Kits()
        osKit.rname = 'fedora'
        osKit.version = '6'
        osKit.arch = 'i386'
        osKit.isOS = True
        osComp = dbs.Components(cname='fedora-6-i386')
        osKit.components.append(osComp)
        osKit.save()
        osKit.flush()

        baseKit = dbs.Kits()
        baseKit.rname = 'base'
        baseKit.version = '0.1'
        baseKit.arch = 'noarch'
        baseKit.isOS = False
        baseComp = dbs.Components(cname='base-installer')
        baseKit.components.append(baseComp, dbs.Components(cname='base-node'))
        baseKit.save()
        baseKit.flush()

        installer.components.append(osComp)
        installer.components.append(baseComp)
        installer.save() 
        installer.flush()

        appglobals = dbs.AppGlobals(kname='PrimaryInstaller', kvalue='master-0')
        appglobals.save()
        appglobals.flush()

        dirs = []
        dirs.append(prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch')
        dirs.append(prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'fedora' / '6' / 'i386')
       
        for dir in dirs:
            dir.makedirs()

        (prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'fedora' / '6' / 'i386' / 'updates.img').touch()

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

        for p in paths:
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

    def tearDown(self):
        global prefix
        self.dbs.dropTables()
        prefix.rmtree()

    def testNew(self):
        raise SkipTest

        cmd = 'repoman -n testing -o fedora-6-i386 --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0

        repo = self.dbs.Repos.select_by(reponame = 'testing')
        assert len(repo) == 1
        assert repo[0].reponame == 'testing'
        assert path(prefix / 'depot' / 'repos' / str(repo[0].repoid)).exists()

    def testNewWithNodeGroup(self):
        raise SkipTest

        cmd = 'repoman -n testing -o fedora-6-i386 --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repo = self.dbs.Repos.select_by(reponame = 'testing')[0]
        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.repoid = repo.repoid
        ng.save()
        ng.flush()

        cmd = 'repoman -n testing --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repo = self.dbs.Repos.select_by(reponame = 'testing')
        assert len(repo) == 1
        assert len(repo[0].kits) == 2
        assert path(prefix / 'depot' / 'repos' / str(repo[0].repoid)).exists()

    def testNewWithNodeGroupDifferentRepo(self):
        raise SkipTest

        cmd = 'repoman -n testing -o fedora-6-i386 --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repo = self.dbs.Repos.select_by(reponame = 'testing')[0]
        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.repoid = repo.repoid
        ng.save()
        ng.flush()

        cmd = 'repoman -n testing --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repo = self.dbs.Repos.select_by(reponame = 'testing')
        assert len(repo) == 1
        repo[0].refresh()
        assert len(repo[0].kits) == 2

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.save()
        installer.flush()

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
        ng.repoid = repo[0].repoid
        ng.save()  
        ng.flush()
        
        cmd = 'repoman -n testing --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repos = self.dbs.Repos.select()
        assert len(repos) == 2
        assert len(repos[0].kits) == 2
        assert len(repos[1].kits) == 3
        for r in repos:
            assert path(prefix / 'depot' / 'repos' / str(r.repoid)).exists()

    def testNewWithNodeGroupSameRepo(self):
        raise SkipTest

        cmd = 'repoman -n testing -o fedora-6-i386 --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repo = self.dbs.Repos.select_by(reponame = 'testing')[0]
        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.repoid = repo.repoid
        ng.save()
        ng.flush()

        cmd = 'repoman -n testing --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repo = self.dbs.Repos.select_by(reponame = 'testing')
        assert len(repo) == 1
        repo[0].refresh()
        assert len(repo[0].kits) == 2

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.repoid = repo[0].repoid
        installer.save()
        installer.flush()
        
        cmd = 'repoman -n testing --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repos = self.dbs.Repos.select()
        assert len(repos) == 1
        assert len(repos[0].kits) == 2
        assert path(prefix / 'depot' / 'repos' / str(repos[0].repoid)).exists()

    def testNewWithNodeGroupChangeKitsSameRepo(self):
        raise SkipTest

        cmd = 'repoman -n testing -o fedora-6-i386 --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repo = self.dbs.Repos.select_by(reponame = 'testing')[0]
        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.repoid = repo.repoid
        ng.save()
        ng.flush()

        cmd = 'repoman -n testing --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        repo = self.dbs.Repos.select_by(reponame = 'testing')
        assert len(repo) == 1
        assert len(repo[0].kits) == 2

        installer = self.dbs.NodeGroups(ngname='installer nodegroup 2',
                                        type='installer') 
        installer.components = self.dbs.Components.select()
        installer.repoid = repo[0].repoid
        installer.save()
        installer.flush()
 
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

        installers = self.dbs.NodeGroups.select()
        for installer in installers:
            installer.components = self.dbs.Components.select()
            installer.save()
            installer.flush()

        cmd = 'repoman -n testing --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0

        assert str(kusudb) == self.dbs.metadata.engine.url.database
        
        repos = self.dbs.Repos.select()
        assert len(repos) == 1
        repos[0].refresh()
        assert len(repos[0].kits) == 3
        assert path(prefix / 'depot' / 'repos' / str(repos[0].repoid)).exists()
 
    def testSnapshost(self):
        raise SkipTest

        cmd = 'repoman -n testing -o fedora-6-i386 --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
 
        cmd = 'repoman -n testing -s  --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0

        repo = self.dbs.Repos.select()
        assert len(repo) == 2
        for r in repo:
            assert path(prefix / 'depot' / 'repos' / str(r.repoid)).exists()

    def testDelete(self):
        raise SkipTest

        cmd = 'repoman -n testing -o fedora-6-i386 --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        oldRepo = self.dbs.Repos.select_by(reponame = 'testing')[0]

        cmd = 'repoman -d testing --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0

        repo = self.dbs.Repos.select_by(reponame = 'testing')
        assert len(repo) == 0
        assert not path(prefix / 'depot' / 'repos' / str(oldRepo.repoid)).exists()

    def testList(self):
        raise SkipTest

        cmd = 'repoman -n testing -o fedora-6-i386 --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        assert runCommand(cmd)[2] == 0
        
        cmd = 'repoman -l --dbdriver=sqlite --dbdatabase %s -p %s' % (kusudb,prefix)
        out,err,rv = runCommand(cmd)

        assert out.find('testing') != '-1'
