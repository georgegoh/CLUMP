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

tempdir = tempfile.mkdtemp(prefix='dbtest')
kusudb = path(tempdir) / 'kusu.db'
newtempdir = tempfile.mkdtemp(prefix='dbtest')
newkusudb = path(newtempdir) / 'newkusu.db'

def tearDown():
    global kusudb
    global tempdir
    global newkusudb
    global newtempdir

    try:
        os.unlink(kusudb)
    except: pass
    
    try:
        os.removedirs(tempdir)
    except: pass

    try:
        os.unlink(newkusudb)
    except: pass
    
    try:
        os.removedirs(newtempdir)
    except: pass

class TestSQLITE:
    def setUp(self):
        self.dbs = db.DB('sqlite', db=kusudb)

    def tearDown(self):
        self.dbs.dropTables()

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

    def testCopyTo(self):
        global newkusudb

        self.dbs.createTables()

        ag = self.dbs.AppGlobals(kname='test1', kvalue='test2')
        self.dbs.Kits(rname='fedora', version='6', arch='sparc',
                      rdesc='Fedora 6 for SPARC', isOS=True, removable=False)

        self.dbs.flush()

        """
        newdb = db.DB('sqlite', db=newkusudb, entity_name='alt')
        self.dbs.copyTo(newdb)

        newag = newdb.AppGlobals.select()

        assert len(newag) == 1, \
                'Copied more than 1 AppGlobals rows: %d' % len(newag)

        newag = newag[0]
        assert newag.kname == 'test1', \
                "New AppGlobals name is %s, expected 'test1'" % newag.kname
        assert newag.kvalue == 'test2', \
                "New AppGlobals value is %s, expected 'test2'" % newag.kvalue

        newkit = newdb.Kits.select()
        assert len(newkit) == 1, \
                'Copied more than 1 AppGlobals rows: %d' % len(newkit)

        newkit = newkit[0]
        assert newkit.rname == 'fedora', \
                "New Kit rname is %s, expected 'fedora'" % newkit.rname
        assert newkit.version == '6', \
                "New Kit version is %s, expected '6'" % newkit.version
        assert newkit.arch == 'sparc', \
                "New Kit arch is %s, expected 'sparc'" % newkit.arch
        assert newkit.rdesc == 'Fedora 6 for SPARC', \
                "New Kit rdesc is %s, " % newkit.arch + \
                "expected 'Fedora 6 for SPARC'"
        assert newkit.isOS, "New Kit is not OS"
        assert not newkit.removable, "New Kit removable"

        newdb.dropTables()
        """
