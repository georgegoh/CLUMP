#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from kusu.core import rcplugin

from kusu.util import tools
from path import path
import tempfile
import os

prefix = None
kusudb = None

def setup():
    global prefix
    global kusudb

    prefix = path(tempfile.mkdtemp(prefix='kusurc', dir=os.environ['KUSU_TMP']))
    kusudb = path(tempfile.mkdtemp(prefix='kusurc', dir=os.environ['KUSU_TMP'])) / 'kusu.db'

    url = 'http://www.osgdc.org/pub/build/tests/modules/kusurc'
    tools.url_mirror_copy(url, prefix) 

    for f in prefix.listdir('index.html*'):
        f.remove()
    
    for f in prefix.listdir():
        f.chmod(0755)

def teardown():
    global kusudb
    kusudb.parent.rmtree()


class TestPlugin:
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
        self.masterIP2 = '192.168.1.1'
        node.nics.append(db.Nics(ip=self.masterIP1, netid=network1.netid))
        node.nics.append(db.Nics(ip=self.masterIP2, netid=network2.netid))

        # nodegroup
        installer = db.NodeGroups(ngname='installer nodegroup',
                                  type='installer') 
        installer.nodes.append(node)
        installer.save()
        installer.flush()

        appglobals = db.AppGlobals(kname='PrimaryInstaller', kvalue='master-0')
        appglobals.save()
        appglobals.flush()

    def tearDown(self):
        global prefix
        self.dbs.dropTables()

    def testScriptPass(self):
        global prefix

        pRunner = rcplugin.PluginRunner('KusuRC', prefix, self.dbs)
        results = pRunner.run()

        assert len(results) == 7

        for result in results:
            if result[0] == 'hello':
                assert result[2] == True
                assert result[3] == None
            elif result[0] == 'fail':
                assert result[2] == False
                assert result[3] == None
            elif result[0] == 'except':
                assert result[2] == False
                assert result[3] != None
            elif result[0] == 'ok.sh':
                assert result[2] == True
                assert result[3] == None
            elif result[0] == 'fail.sh':
                assert result[2] == False
                assert result[3] == None
            elif result[0] == 'scriptOK.py':
                assert result[2] == True
                assert result[3] == None
            elif result[0] == 'scriptFail.py':
                assert result[2] == False
                assert result[3] == None
 

            assert result[0] != 'norun'

    def testSingleScriptPass(self):
        global prefix

        pRunner = rcplugin.PluginRunner('KusuRC', prefix / 'ok.sh', self.dbs)
        results1 = pRunner.run()

        pRunner = rcplugin.PluginRunner('KusuRC', prefix / 'fail.sh', self.dbs)
        results2 = pRunner.run()

        assert len(results1 + results2) == 2

        for result in results1 + results2:
            if result[0] == 'ok.sh':
                assert result[2] == True
                assert result[3] == None
            elif result[0] == 'fail.sh':
                assert result[2] == False
                assert result[3] == None
