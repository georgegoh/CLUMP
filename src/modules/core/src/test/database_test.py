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

class TestSQLITE:
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.kusudb = path(self.tempdir) / 'kusu.db'

        self.dbs = db.DB('sqlite', db=self.kusudb)

    def tearDown(self):
        self.dbs.dropTables()

        try:
            os.unlink(self.kusudb)
        except: pass
        
        try:
            os.removedirs(self.tempdir)
        except: pass

        session = self.dbs.createSession()
        session.clear()
        session.close()

    def testTableCreation(self):
        self.dbs.createTables()

        for table in self.dbs.mapTableClass.keys():
            assert self.dbs.metadata.engine.has_table(table)

    def testTableDrop(self):
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
