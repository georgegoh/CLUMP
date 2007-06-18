#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from kusu.repoman import repo
from path import path
import tempfile
import os

prefix = None
kusudb = None
cachedir = path(tempfile.mkdtemp())

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

    prefix = path(tempfile.mkdtemp())
    kusudb = path(tempfile.mkdtemp()) / 'kusudb'
    dbs = db.DB('sqlite', kusudb)

def tearDown():
    global kusudb
    global cachedir
    
    kusudb.parent.rmtree()
    cachedir.rmtree()

class TestRedhat5Repo:

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
        network.save()
        network.flush()

        # nodegroup
        node = db.Nodes(name='master-0')
        self.masterIP = '10.1.1.1'
        node.nics.append(db.Nics(ip=self.masterIP, netid=network.netid))

        installer = db.NodeGroups(ngname='installer nodegroup') 
        installer.nodes.append(node)
        installer.save()
        installer.flush()

        # Kits + components
        osKit = db.Kits()
        osKit.rname = 'rhel'
        osKit.version = '5'
        osKit.arch = 'i386'
        osKit.isOS = True
        osComp = db.Components(cname='rhel-5-i386')
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
        dirs.append(prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'rhel' / '5' / 'i386')
      
        for dir in dirs:
            dir.makedirs()

        (prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch' / 'base-installer.rpm').touch()
        (prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch' / 'base-node.rpm').touch()
        (prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'rhel' / '5' / 'i386' / 'updates.img').touch()

        for p in self.getPath():
            try:
                (prefix / 'depot' / 'kits' / 'rhel' / '5' / 'i386' / p).parent.makedirs()
            except: pass
            (prefix / 'depot' / 'kits' / 'rhel' / '5' / 'i386' / p).touch()

        download('comps.xml', \
                 prefix / 'depot' / 'kits' / 'rhel' / '5' / 'i386' / 'Server' / \
                 'repodata' / 'comps-rhel5-server-core.xml')

        download('ks.cfg.tmpl', \
                 prefix / 'opt' / 'kusu' / 'lib' / 'nodeinstaller' / 'rhel' / '5' / 'i386' / 'ks.cfg.tmpl')


    def tearDown(self):
        global prefix
        
        self.dbs.dropTables()
        prefix.rmtree()

    def getPath(self):
        paths = ['Server/yum-3.0.1-5.el5.noarch.rpm', \
                 'Server/repodata/comps-rhel5-server-core.xml', \
                 'Server/repodata/other.xml.gz', \
                 'Server/repodata/filelists.xml.gz', \
                 'Server/repodata/repomd.xml', \
                 'Server/repodata/primary.xml.gz', \
                 'Cluster/repodata/comps-rhel5-cluster.xm', \
                 'Cluster/repodata/other.xml.gz', \
                 'Cluster/repodata/filelists.xml.gz', \
                 'Cluster/repodata/repomd.xml', \
                 'Cluster/repodata/primary.xml.gz', \
                 'ClusterStorage/repodata/comps-rhel5-cluster-st.xml', \
                 'ClusterStorage/repodata/other.xml.gz', \
                 'ClusterStorage/repodata/filelists.xml.gz', \
                 'ClusterStorage/repodata/repomd.xml', \
                 'ClusterStorage/repodata/primary.xml.gz', \
                 'VT/repodata/comps-rhel5-vt.xml', \
                 'VT/repodata/other.xml.gz', \
                 'VT/repodata/filelists.xml.gz', \
                 'VT/repodata/repomd.xml', \
                 'VT/repodata/primary.xml.gz', \
                 'isolinux/initrd', \
                 'isolinux/vmlinuz', \
                 'images/stage2.img']
        return paths

    def checkLayout(self, prefix):
        for p in self.getPath():
            assert (prefix / p).exists()

    def testRelativeLinks(self):
        global prefix

        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup', 'a repo during testing')

        repoid = str(r.repoid)

        for p in self.getPath():
            p = prefix / 'depot' / 'repos' / repoid / p
            if p.islink():
                assert not p.readlink().isabs()

    def testNodeInstallerImg(self):
        global prefix

        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup', 'a repo during testing')
        repoid = str(r.repoid)

        assert (prefix / 'depot' / 'repos' / repoid / 'images' / 'updates.img').exists()

    def testKickstartGeneration(self):
        global prefix

        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup', 'a repo during testing')
        repoid = str(r.repoid)

        assert (prefix / 'depot' / 'repos' / repoid / 'ks.cfg').exists()
      
        f = open(prefix / 'depot' / 'repos' / repoid / 'ks.cfg', 'r')
        assert f.readlines()[1].strip()  == 'url --url http://%s/repos/%s' % (self.masterIP, repoid)

        f.close() 
 
    def testMake(self):
        global prefix

        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup', 'a repo during testing')

        repoid = str(r.repoid)
        self.checkLayout(prefix / 'depot' / 'repos' / repoid)

    def testGettingOS(self):
        global prefix

        os_name, os_version, os_arch = repo.getOS(self.dbs, 'installer nodegroup')

        assert os_name == 'rhel'
        assert os_version == '5'
        assert os_arch == 'i386'

    def testDeleteRepo(self):
        global prefix

        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
  
        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.delete(repoid)
        
        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

        assert not self.dbs.Repos.get(repoid)
        assert not len(self.dbs.ReposHaveKits.select_by(repoid=repoid))

    def testCleanRepo(self):
        global prefix

        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
 
        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.clean(repoid)
 
        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

    def testRefreshRepo(self):
        global prefix

        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
 
        r = repo.Redhat5Repo('i386', prefix, self.dbs)
        r.debug = True
        r.refresh(repoid)

        repoid = str(r.repoid)
        self.checkLayout(prefix / 'depot' / 'repos' / repoid)

