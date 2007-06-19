#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from path import path
import tempfile
import os

tempdir = tempfile.mkdtemp()
kusudb = path(tempdir) / 'kusu.db'

def tearDown():
    global kusudb
    global tempdir

    try:
        os.unlink(kusudb)
    except: pass
    
    try:
        os.removedirs(tempdir)
    except: pass

class TestSQLITE:
    def setUp(self):
        global kusudb
        self.dbs = db.DB('sqlite', db=kusudb)

    def tearDown(self):
        pass

    def testTableCreation(self):
        self.dbs.createTables()
        
        for table in self.dbs.metadata.table_iterator():
            assert self.dbs.metadata.engine.has_table(str(table))

    def testTableDrop(self):
        self.dbs.createTables()
        self.dbs.dropTables()
        
        for table in self.dbs.metadata.table_iterator():
            assert not self.dbs.metadata.engine.has_table(str(table))

    def testBootstrap(self):
        self.dbs.bootstrap()

        for name in ['master', 'installer', 'compute']:
            ng = self.dbs.NodeGroups.select_by(ngname=name)[0]
            assert ng.ngname == name

        assert len(self.dbs.NodeGroups.select_by(ngname='compute')[0].partitions) > 0


    def testInsertSelect(self):

        self.dbs.createTables()

        appglobals = self.dbs.AppGlobals(kname='key name')
        appglobals.save()
        appglobals.flush()
        
        assert self.dbs.AppGlobals.get(1).kname == 'key name'

        self.dbs.dropTables()

