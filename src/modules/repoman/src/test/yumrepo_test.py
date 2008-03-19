#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
from path import path
import tempfile

from kusu.util import tools
from kusu.repoman import yum

from nose.tools import assert_raises

cachedir = path(tempfile.mkdtemp(prefix='yumrepo', dir=os.environ['KUSU_TMP']))

def setup():
    url = 'http://www.osgdc.org/pub/build/tests/modules/yumrepo/'
    tools.url_mirror_copy(url, cachedir) 

def teardown():
    if cachedir.exists():
        cachedir.rmtree()

class TestWorkingLocalYumRepo:

    def setUp(self):
        self.y = yum.YumRepo(str(cachedir / 'working'))

    def testGetRepoMD(self):
        repomd = self.y.getRepoMD()

        assert repomd.has_key('filelists')
        assert repomd.has_key('other')
        assert repomd.has_key('group')
        assert repomd.has_key('primary')
        assert len(repomd.keys()) == 4

    def testGetPrimary(self):
        primary = self.y.getPrimary()

        assert primary.has_key('cyrus-sasl-ldap')
        assert primary['cyrus-sasl-ldap'].has_key('i386')
        assert len(primary['cyrus-sasl-ldap']['i386']) == 1

        r = primary['cyrus-sasl-ldap']['i386'][0]
        assert r.getName() == 'cyrus-sasl-ldap'
        assert r.getVersion() == '2.1.22'
        assert r.getRelease() == '4'
        assert r.getArch() == 'i386'
        assert r.getEpoch() == 0 #none is treated as 0 in xml
        assert r.getFilename() == cachedir / 'working/CentOS/cyrus-sasl-ldap-2.1.22-4.i386.rpm'
