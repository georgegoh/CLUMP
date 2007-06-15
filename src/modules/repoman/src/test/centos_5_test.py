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

class TestCentosRepo:

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
        dirs.append(prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386')
        dirs.append(prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'CentOS')
        dirs.append(prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'images')
        dirs.append(prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'repodata')
        dirs.append(prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'isolinux')
        dirs.append(prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch')
       
        for dir in dirs:
            dir.makedirs()

        download('comps.xml', \
                 prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'repodata' / 'comps.xml')

        (prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'isolinux' / 'initrd').touch()
        (prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'isolinux' / 'vmlinuz').touch()
        (prefix / 'depot' / 'kits' / 'centos' / '5' / 'i386' / 'images' / 'stage2.img').touch()

    def tearDown(self):
        global prefix
        
        self.dbs.dropTables()
        prefix.rmtree()
        
    def testMake(self):
        global prefix
 
        r = repo.CentosRepo('5', 'i386', prefix, self.dbs)
        r.make('installer nodegroup', 'a repo during testing')

        repoid = str(r.repoid)
        depot = prefix / 'depot'
        assert (depot / 'repos' / repoid / 'repodata' / 'comps.xml').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'other.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'filelists.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'repomd.xml').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'primary.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'CentOS').exists()
        assert (depot / 'repos' / repoid / 'isolinux' / 'initrd').exists()
        assert (depot / 'repos' / repoid / 'isolinux' / 'vmlinuz').exists()
        assert (depot / 'repos' / repoid / 'images' / 'stage2.img').exists()

    def testGettingOS(self):
        global prefix

        os_name, os_version, os_arch = repo.getOS(self.dbs, 'installer nodegroup')

        assert os_name == 'centos'
        assert os_version == '5'
        assert os_arch == 'i386'

    def testDeleteRepo(self):
        global prefix

        r = repo.CentosRepo('5', 'i386', prefix, self.dbs)
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
  
        r = repo.CentosRepo('5', 'i386', prefix, self.dbs)
        r.delete(repoid)
        
        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

        assert not self.dbs.Repos.get(repoid)
        assert not len(self.dbs.ReposHaveKits.select_by(repoid=repoid))

    def testCleanRepo(self):
        global prefix

        r = repo.CentosRepo('5', 'i386', prefix, self.dbs)
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
 
        r = repo.CentosRepo('5', 'i386', prefix, self.dbs)
        r.clean(repoid)
 
        depot = prefix / 'depot'    
        assert not (depot / 'repos' / str(repoid)).exists() 

    def testRefreshRepo(self):
        global prefix

        r = repo.CentosRepo('5', 'i386', prefix, self.dbs)
        r.make('installer nodegroup', 'a repo during testing')
        repoid = r.repoid
 
        r = repo.CentosRepo('5', 'i386', prefix, self.dbs)
        r.refresh(repoid)

        repoid = str(r.repoid)
        depot = prefix / 'depot'
        assert (depot / 'repos' / repoid / 'repodata' / 'comps.xml').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'other.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'filelists.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'repomd.xml').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'primary.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'CentOS').exists()
        assert (depot / 'repos' / repoid / 'isolinux' / 'initrd').exists()
        assert (depot / 'repos' / repoid / 'isolinux' / 'vmlinuz').exists()
        assert (depot / 'repos' / repoid / 'images' / 'stage2.img').exists()


