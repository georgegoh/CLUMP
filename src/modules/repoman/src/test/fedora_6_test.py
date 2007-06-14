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

prefix = path(tempfile.mkdtemp())


def download(filename, dest):
    import urllib2

    prefix = 'http://www.osgdc.org/pub/build/tests/modules/repoman/'
    f = urllib2.urlopen(prefix + filename)
    content = f.read()
    f.close()

    f = open(dest, 'w')
    f.write(content)
    f.close()

def setUp():
    global prefix

    # Sets up database
    kusudb = prefix / 'kusudb'
    dbs = db.DB('sqlite', kusudb)
    dbs.createTables()
    
    # nodegroup
    installer = db.NodeGroups(ngname='installer nodegroup') 
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

    dirs = []
    dirs.append(prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386')
    dirs.append(prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'Fedora' / 'RPMS')
    dirs.append(prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'Fedora' / 'base')
    dirs.append(prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'images')
    dirs.append(prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'repodata')
    dirs.append(prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'isolinux')
    dirs.append(prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch')
   
    for dir in dirs:
        dir.makedirs()

    download('comps.xml', \
             prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'repodata' / 'comps.xml')

    (prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'isolinux' / 'initrd').touch()
    (prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'isolinux' / 'vmlinuz').touch()
    (prefix / 'depot' / 'kits' / 'fedora' / '6' / 'i386' / 'images' / 'stage2.img').touch()

def tearDown():
    global prefix
    #prefix.rmtree() 

class TestFedoraRepo:

    def testMake(self):
        global prefix
   
        r = repo.FedoraRepo('6', 'i386', prefix, \
                            db.DB('sqlite', prefix / 'kusudb') )
        r.make('installer nodegroup', 'a repo during testing')
        repoid = str(r.repoid)
        depot = prefix / 'depot'
        assert (depot / 'repos' / repoid / 'repodata' / 'comps.xml').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'other.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'filelists.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'repomd.xml').exists()
        assert (depot / 'repos' / repoid / 'repodata' / 'primary.xml.gz').exists()
        assert (depot / 'repos' / repoid / 'Fedora' / 'RPMS').exists()
        assert (depot / 'repos' / repoid / 'isolinux' / 'initrd').exists()
        assert (depot / 'repos' / repoid / 'isolinux' / 'vmlinuz').exists()
        assert (depot / 'repos' / repoid / 'images' / 'stage2.img').exists()




