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

class TestCentos5Repo:

    def setUp(self):
        global prefix
        global kusudb
        
        self.dbs = db.DB('sqlite', kusudb)
        self.dbs.createTables()
    
        # nodegroup
        installer = db.NodeGroups(ngname='installer nodegroup') 
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

        dirs = []
        dirs.append(prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch')
       
        for dir in dirs:
            dir.makedirs()

        for p in self.getPath():
            new_path = prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / p
            try:
                new_path.parent.makedirs()
            except: pass

            if not new_path.isdir():    
                new_path.touch()

        download('comps.xml', \
                 prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'repodata' / 'comps.xml')

    def tearDown(self):
        global prefix
        
        self.dbs.dropTables()
        prefix.rmtree()

    def getPath(self):
        paths = ['CentOS/',\
                 'repodata/comps.xml', \
                 'repodata/other.xml.gz', \
                 'repodata/filelists.xml.gz', \
                 'repodata/repomd.xml', \
                 'repodata/primary.xml.gz', \
                 'isolinux/initrd', \
                 'isolinux/vmlinuz', \
                 'images/stage2.img']
        return paths

    def checkLayout(self, prefix):
        for p in self.getPath():
            assert (prefix / p).exists()

    def testMake(self):
        global prefix
 
        r = repo.Centos5Repo('5', 'i386', prefix, self.dbs)
        r.make('installer nodegroup', 'a repo during testing')

        repoid = str(r.repoid)
        self.checkLayout(prefix / 'depot' / 'repos' / repoid)

    def testGettingOS(self):
        global prefix

        os_name, os_version, os_arch = repo.getOS(self.dbs, 'installer nodegroup')

        assert os_name == 'centos'
        assert os_version == '5'
        assert os_arch == 'i386'

    def testDeleteRepo(self):
        global prefix

        r = repo.Centos5Repo('5', 'i386', prefix, self.dbs)
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
  
        r = repo.Centos5Repo('5', 'i386', prefix, self.dbs)
        r.delete(repoid)
        
        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

        assert not self.dbs.Repos.get(repoid)
        assert not len(self.dbs.ReposHaveKits.select_by(repoid=repoid))

    def testCleanRepo(self):
        global prefix

        r = repo.Centos5Repo('5', 'i386', prefix, self.dbs)
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
 
        r = repo.Centos5Repo('5', 'i386', prefix, self.dbs)
        r.clean(repoid)
 
        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

    def testRefreshRepo(self):
        global prefix

        r = repo.Centos5Repo('5', 'i386', prefix, self.dbs)
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
 
        r = repo.Centos5Repo('5', 'i386', prefix, self.dbs)
        r.refresh(repoid)

        repoid = str(r.repoid)
        self.checkLayout(prefix / 'depot' / 'repos' / repoid)

