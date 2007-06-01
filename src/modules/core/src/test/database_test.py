#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
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

        for table in self.dbs.mapTableClass.keys():
            assert self.dbs.metadata.engine.has_table(table)

    def testTableDrop(self):
        self.dbs.createTables()
        self.dbs.dropTables()

        for table in self.dbs.mapTableClass.keys():
            assert not self.dbs.metadata.engine.has_table(table)

    def testBootstrap(self):
        self.dbs.bootstrap()

        session = self.dbs.createSession()

        for name in ['installer', 'compute']:
            ng = session.query(self.dbs.nodegroups).select_by(ngname=name)[0]
            assert ng.ngname == name

        assert len(session.query(self.dbs.nodegroups).select_by(ngname='compute')[0].partitions) > 0

        session.clear()
        session.close()

    def testInsertSelect(self):

        self.dbs.createTables()

        session = self.dbs.createSession()
        session.save(db.AppGlobals(kname='key name'))
        session.flush()
        
        assert session.query(self.dbs.appglobals).get(1).kname == 'key name'

        session.clear()
        session.close()

        self.dbs.dropTables()

