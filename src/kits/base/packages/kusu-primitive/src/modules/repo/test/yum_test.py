#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#

from primitive.support.util import MD5SUM
from primitive.repo.yum import YumRepo
from primitive.repo.yum import RHEL5Repo
from primitive.fetchtool.commands import FetchCommand

from path import path

from nose import SkipTest
import tempfile
import os
import gzip

prefix = None

UPDATEIMG1_URL="http://www.osgdc.org/pub/build/tests/modules/primitive/repotool/update1.img"
UPDATEIMG1_MD5SUM="967d9b358b7dbbd7b15f3ddb430bf631"

def setup():
    pass

def teardown():
    pass

class TestYum:
    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repo'))

        fc = FetchCommand(uri='http://www.osgdc.org/pub/build/tests/modules/yumrepo/working/',
                         fetchdir=True,
                         destdir=self.prefix,
                         overwrite=False)
        fc.execute()
        
        self.repo = YumRepo(self.prefix)

    def tearDown(self):
        self.prefix.rmtree()

    def checkLayOut(self):

        assert (self.prefix / 'repodata').exists()
        assert (self.prefix / 'repodata' / 'repomd.xml').exists()

        for f in ['primary.xml.gz', 'other.xml.gz', 'filelists.xml.gz']:
            f = self.prefix / 'repodata' / f
            assert f.exists() 

            fd = gzip.open(f)
            content = fd.read()
            fd.close()
            assert content.find('cyrus-sasl-ldap') != -1

    def testYumWithComp(self):

        self.repo.makeMeta()
        self.checkLayOut()

    def testYumWithNoComp(self):

        comp = self.prefix / 'repodata' / 'comps.xml'
        if comp.exists(): comp.remove

        self.repo.makeMeta()
        self.checkLayOut()
 

class TestRHEL5Repo:
    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repo'))

        fc = FetchCommand(uri='http://www.osgdc.org/pub/build/tests/modules/yumrepo/working/',
                         fetchdir=True,
                         destdir=self.prefix,
                         overwrite=False)
        fc.execute()
        
        self.repo = RHEL5Repo(self.prefix)

    def tearDown(self):
        self.prefix.rmtree()

    def testHandleUpdates(self):
        images_dir = self.prefix / 'images'
        images_dir.makedirs()

        self.repo.handleUpdates(UPDATEIMG1_URL)
        update_img = images_dir / 'update1.img'
        assert MD5SUM(update_img) == UPDATEIMG1_MD5SUM
