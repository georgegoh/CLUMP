#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.core import database as db
from path import path
from nose import SkipTest
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

        for name in ['installer', 'compute']:
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

    def testFindNodeGroupsFromKit(self):
        raise SkipTest
        self.dbs.createTables()
        self.dbs.bootstrap()
        self.prepareDatabase()

        ngs = db.findNodeGroupsFromKit(self.dbs,
                                       columns=[],
                                       ngargs={},
                                       kitargs={})
        wantngnames = ['installer', 'compute']

        # we are expecting three nodegroups
        assert len(ngs) == 3, 'Got %d nodegroup(s), expecting 3' % len(ngs)

        for x in xrange(len(ngs)):
            assert ngs[x].ngname == wantngnames[x], \
                "ngname '%s', expected '%s'" % (ngs[x].ngname, wantngnames[x])

        ngs = db.findNodeGroupsFromKit(self.dbs,
                                       columns=['ngname', 'type'],
                                       ngargs={'type': 'compute'},
                                       kitargs={})
        wantngs = [{'ngname': 'compute', 'type': 'compute'}]

        # only one nodegroup here
        assert len(ngs) == 1, 'Got %d nodegroup(s), expecting 1' % len(ngs)

        for x in xrange(len(ngs)):
            # ensure the selected columns are available
            for col in wantngs[x]:
                assert ngs[x].has_key(col), \
                    "Column '%s' missing in result" % col

            # ensure no extra columns are available
            for col in self.dbs.nodegroups.c.keys():
                if col not in wantngs[x]:
                    assert not ngs[x].has_key(col), \
                        "Column '%s' not expected in result" % col

            assert ngs[x].ngname == wantngs[x]['ngname'], \
                "ngname '%s', expected '%s'" % (ngs[x].ngname,
                                                wantngs[x]['ngname'])
            assert ngs[x].type == wantngs[x]['type'], \
                "type '%s', expected '%s'" % (ngs[x].type, wantngs[x]['type'])

        ngs = db.findNodeGroupsFromKit(self.dbs,
                                       columns=['ngname', 'ngid'],
                                       ngargs={'type': 'installer'},
                                       kitargs={'isOS': True})
        wantngs = [{'ngname': 'installer', 'ngid': 1}]

        # only one nodegroup here
        assert len(ngs) == 1, 'Got %d nodegroup(s), expecting 1' % len(ngs)

        for x in xrange(len(ngs)):
            # ensure the selected columns are available
            for col in wantngs[x]:
                assert ngs[x].has_key(col), \
                    "Column '%s' missing in result" % col

            # ensure no extra columns are available
            for col in self.dbs.nodegroups.c.keys():
                if col not in wantngs[x]:
                    assert not ngs[x].has_key(col), \
                        "Column '%s' not expected in result" % col

            assert ngs[x].ngname == wantngs[x]['ngname'], \
                "ngname '%s', expected '%s'" % (ngs[x].ngname,
                                                wantngs[x]['ngname'])
            assert ngs[x].ngid == wantngs[x]['ngid'], \
                "ngid %d, expected 1" % ngs[x].type

    def testFindKitsFromNodeGroup(self):
        raise SkipTest
        self.dbs.createTables()
        self.dbs.bootstrap()
        self.prepareDatabase()

        kits = db.findKitsFromNodeGroup(self.dbs,
                                        columns=[],
                                        kitargs={},
                                        ngargs={})
        wantkitnames = ['base', 'fedora']

        # we are expecting two kits
        assert len(kits) == 2, 'Got %d kit(s), expecting 2' % len(kits)

        for x in xrange(len(kits)):
            assert kits[x].rname == wantkitnames[x], \
                "rname '%s', expected '%s'" % (kits[x].rname, wantkitnames[x])

        kits = db.findKitsFromNodeGroup(self.dbs,
                                        columns=['rname', 'version'],
                                        # rename this as SOON AS POSSIBLE
                                        kitargs={'removeable': False},
                                        ngargs={})
        wantkits = [{'rname': 'base', 'version': '0.1'},
                    {'rname': 'fedora', 'version': '6'}]

        # we are expecting two kits
        assert len(kits) == 2, 'Got %d kit(s), expecting 2' % len(kits)

        for x in xrange(len(kits)):
            # ensure the selected columns are available
            for col in wantkits[x]:
                assert kits[x].has_key(col), \
                    "Column '%s' missing in result" % col

            for col in self.dbs.kits.c.keys():
                if col not in wantkits[x]:
                    assert not kits[x].has_key(col), \
                        "Column '%s' not expected in result" % col

            assert kits[x].rname == wantkits[x]['rname'], \
                "rname '%s', expected '%s'" % (kits.rname, wantkits[x]['rname'])
            assert kits[x].version == wantkits[x]['version'], \
                "version '%s', expected '%s'" % (kits.version,
                                                 wantkits[x]['version'])

        kits = db.findKitsFromNodeGroup(self.dbs,
                                        columns=['rname', 'arch'],
                                        # rename this as SOON AS POSSIBLE
                                        kitargs={'isOS': True},
                                        ngargs={'type': 'installer'})
        wantkits = [{'rname': 'fedora', 'arch': 'i386'}]

        # we are expecting one kit
        assert len(kits) == 1, 'Got %d kit(s), expecting 1' % len(kits)

        for x in xrange(len(kits)):
            # ensure the selected columns are available
            for col in wantkits[x]:
                assert kits[x].has_key(col), \
                    "Column '%s' missing in result" % col

            for col in self.dbs.kits.c.keys():
                if col not in wantkits[x]:
                    assert not kits[x].has_key(col), \
                        "Column '%s' not expected in result" % col

            assert kits[x].rname == wantkits[x]['rname'], \
                "rname '%s', expected '%s'" % (kits.rname, wantkits[x]['rname'])
            assert kits[x].arch == wantkits[x]['arch'], \
                "arch '%s', expected '%s'" % (kits.arch, wantkits[x]['arch'])

    def prepareDatabase(self):
        # insert data into DB
        # create a new kit with removable set to True
        basekit = self.dbs.Kits(rname='base', rdesc='Base Kit',
                               version='0.1', isOS=False, removable=False)
        component_node = self.dbs.Components(cname='component-base-node',
                                        cdesc='Component for Kusu Node Base')
        component_installer = self.dbs.Components(
                                    cname='component-base-installer',
                                    cdesc='Component for Kusu Installer Base')
        basekit.components.append(component_node)
        basekit.components.append(component_installer)

        oskit = self.dbs.Kits(rname='fedora', rdesc='FC6', version='6',
                              arch='i386', isOS=True, removable=False)
        component_os = self.dbs.Components(cname='component-fc6',
                                           cdesc='fc6 component')
        oskit.components.append(component_os)

        ng = self.dbs.NodeGroups.selectfirst_by(ngname='compute')
        ng.components.append(component_node)
        ng.components.append(component_os)

        ng = self.dbs.NodeGroups.selectfirst_by(ngname='installer')
        ng.components.append(component_installer)
        ng.components.append(component_os)
        ng.packages.append(self.dbs.Packages(packagename='kit-base'))

        basekit.save()
        oskit.save()
        self.dbs.flush()
