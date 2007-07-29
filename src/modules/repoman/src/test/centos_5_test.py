#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from kusu.repoman import repo
from path import path
import tempfile
import os

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

def setUp():
    global prefix
    global kusudb

    prefix = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP']))
    kusudb = path(tempfile.mkdtemp(prefix='repoman', dir=os.environ['KUSU_TMP'])) / 'kusu.db'
    dbs = db.DB('sqlite', kusudb)

def tearDown():
    global kusudb
    global cachedir
    
    kusudb.parent.rmtree()
    cachedir.rmtree()

class TestCentos5Repo:

    def setUp(self):
        global prefix
        global kusudb
        
        self.dbs = db.DB('sqlite', kusudb)
        self.dbs.createTables()
    
        # Network
        network1 = db.Networks()
        network1.network = '10.0.0.0'
        network1.subnet = '255.0.0.0'
        network1.device = 'eth0'
        network1.type = 'public'
        network1.save()
        network1.flush()

        network2 = db.Networks()
        network2.network = '192.168.1.0'
        network2.subnet = '255.255.255.0'
        network2.device = 'eth1'
        network2.type = 'provision'
        network2.save()
        network2.flush()

        # nodegroup
        node = db.Nodes(name='master-0')
        self.masterIP1 = '10.1.1.1'
        self.masterIP2 = '192.168.l.1'
        node.nics.append(db.Nics(ip=self.masterIP1, netid=network1.netid))
        node.nics.append(db.Nics(ip=self.masterIP2, netid=network2.netid))

        installer = db.NodeGroups(ngname='installer nodegroup',
                                  type='installer') 
        installer.nodes.append(node)
        installer.save()
        installer.flush()

        # Kits + components
        osKit = db.Kits()
        osKit.rname = 'centos'
        osKit.version = '5'
        osKit.arch = 'i386'
        osKit.isOS = True
        osComp = db.Components(cname='centos-5-i386')
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
        dirs.append(prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'centos' / '5' / 'i386')
       
        for dir in dirs:
            dir.makedirs()

        (prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch' / 'base-installer.rpm').touch()
        (prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch' / 'base-node.rpm').touch()
        (prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'centos' / '5' / 'i386' / 'updates.img').touch()

        for p in self.getPath():
            new_path = prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / p
            try:
                new_path.parent.makedirs()
            except: pass

            if not new_path.isdir():    
                new_path.touch()

        download('comps.xml', \
                 prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'repodata' / 'comps.xml')

        download('ks.cfg.tmpl', \
                 prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'centos' / '5' / 'i386' / 'ks.cfg.tmpl')


    def tearDown(self):
        global prefix
        
        self.dbs.dropTables()
        prefix.rmtree()

    def getPath(self):
        paths = ['CentOS/yum-3.0.5-1.el5.centos.2.noarch.rpm',\
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

    def testRelativeLinks(self):
        global prefix

        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')

        repoid = str(r.repoid)

        for p in self.getPath():
            p = prefix / 'depot' / 'repos' / repoid / p
            if p.islink():
                assert not p.readlink().isabs()
 
    def testNodeInstallerImg(self):
        global prefix

        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')
        repoid = str(r.repoid)

        assert (prefix / 'depot' / 'repos' / repoid / 'images' / 'updates.img').exists()

    def testKickstartGeneration(self):
        global prefix

        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')
        repoid = str(r.repoid)

        row = self.dbs.AppGlobals.select_by(kname = 'PrimaryInstaller')
        row = row[0]
        masterNode = self.dbs.Nodes.select_by(name=row.kvalue)[0]

        for nic in masterNode.nics:
            if nic.ip: 
                ip = nic.ip
                assert (prefix / 'depot' / 'repos' / repoid / 'ks.cfg.' + ip).exists()
      
                f = open(prefix / 'depot' / 'repos' / repoid / 'ks.cfg.' + ip, 'r')
                assert f.readlines()[1].strip()  == 'url --url http://%s/repos/%s' % (ip, repoid)
                f.close() 
 
    def testMakeOSType(self):
        global prefix
 
        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')

        assert r.ostype == 'centos-5-i386'
 
    def testMakeOInstallerIP(self):
        global prefix
 
        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')

        assert self.dbs.Repos.get(r.repoid).installers == ';'.join([self.masterIP1, self.masterIP2])
 
    def testMake(self):
        global prefix
 
        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')

        repoid = str(r.repoid)
        self.checkLayout(prefix / 'depot' / 'repos' / repoid)

    def testNodeGroupHasRepoID(self):
        global prefix

        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')

        repoid = str(r.repoid)
 
        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')

        assert len(ng) == 1
        assert ng[0].repoid == r.repoid
 
    def testDeleteRepo(self):
        global prefix

        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')
        repoid = r.repoid
  
        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.delete(repoid)
        
        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

        assert not self.dbs.Repos.get(repoid)
        assert not len(self.dbs.ReposHaveKits.select_by(repoid=repoid))

    def testCleanRepo(self):
        global prefix

        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')
        repoid = r.repoid
 
        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.clean(repoid)
 
        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

    def testRefreshRepo(self):
        global prefix

        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.make('installer nodegroup')
        repoid = r.repoid
 
        r = repo.Centos5Repo('i386', prefix, self.dbs)
        r.test = True
        r.refresh(repoid)

        repoid = str(r.repoid)
        self.checkLayout(prefix / 'depot' / 'repos' / repoid)

