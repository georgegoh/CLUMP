#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from kusu.repoman import tools, repo
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

def tearDown():
    global kusudb
    global cachedir
 
    kusudb.parent.rmtree()
    cachedir.rmtree()

class TestTools:

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

        (prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch' / 'base-installer.rpm').touch()
        (prefix / 'depot' / 'kits' / 'base' /  '0.1' / 'noarch' / 'base-node.rpm').touch()
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

    def tearDown(self):
        global prefix
        self.dbs.dropTables()
        prefix.rmtree()

    def getPath(self):
        
        paths = ['Fedora/RPMS/yum-3.0-6.noarch.rpm',\
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

    def testRepoExistsTrue(self):

        r = repo.Fedora6Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup')

        assert tools.repoExists(self.dbs, 1) == True

    def testRepoExistsFalse(self):
        assert tools.repoExists(self.dbs, 'installer nodegroup') == False

    def testNodeGroupExistsTrue(self):
        assert tools.nodeGroupExists(self.dbs, 'installer nodegroup') == True
    
    def testNodeGroupExistsFalse(self):
        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        
        for node in ng.nodes:
            for nic in node.nics:
                nic.delete()
                nic.flush()

            node.delete()
            node.save()
            node.flush()
        ng.delete()
        ng.flush()

        assert tools.nodeGroupExists(self.dbs, 'installer nodegroup') == False

    def testGetRepoFromNodeGroupTrue(self):
        r = repo.Fedora6Repo('i386', prefix, self.dbs)
        r.debug = True
        r.make('installer nodegroup')
    
        ng = self.dbs.NodeGroups.select_by(ngname = 'installer nodegroup')[0]
        ng.repoid = r.repoid
        ng.save()
        ng.flush()

        assert tools.getRepoFromNodeGroup(self.dbs, 'installer nodegroup') == 1
        
    def testGetRepoFromNodeGroupFalse(self):
        assert tools.getRepoFromNodeGroup(self.dbs, 'installer nodegroup') == None

    def getKits(self):
        assert tools.getKits(self.dbs, 'installer nodegroup') == ['fedora-6-i386', 'base']

    def testGetOS(self):
        os_name, os_version, os_arch = tools.getOS(self.dbs, 'installer nodegroup')
    
        assert os_name == 'fedora'
        assert os_version == '6'
        assert os_arch == 'i386'

    def testGetFileFromWeb(self):
        url = 'http://www.osgdc.org/pub/build/tests/modules/repoman/comps.xml'
        
        content = None
        content = tools.getFile(url)

        assert content

    def testGetFileFromFile(self):
        p = prefix / 'touchme'
        f = open(p, 'w')
        f.write('touch me again')
        f.close()
                
        content = None
        content = tools.getFile(str(p))

        assert content

