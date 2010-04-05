#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#

from primitive.repo.hdlist import RedHat4Repo , Centos4Repo, _pkgorder_cleanup
from primitive.fetchtool.commands import FetchCommand

from path import path

from nose import SkipTest
import tempfile
import tarfile
import os

prefix = None

def setup():
    pass

def teardown():
    pass

def unpack(filename, dest):
    tar = tarfile.open(filename, 'r:gz')
    for tarinfo in tar:
        tar.extract(tarinfo.name, dest)
    tar.close()

def test_pkgorder_cleanup():
    ''' Remove /tmp/pkgorder-<pid> directory'''
    suffix = 1
    tmpfile = path('/tmp/pkgorder-' + str(suffix))
    # don't clash with existing directories.
    while tmpfile.exists():
        suffix += 1
        tmpfile = path('/tmp/pkgorder-' + str(suffix))
    # no clash, create the mock directory.
    tmpfile.mkdir()
    assert tmpfile.exists()
    _pkgorder_cleanup(suffix)
    assert not tmpfile.exists()


class TestHDList:
    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repo'))

        fc = FetchCommand(uri='http://www.osgdc.org/pub/build/tests/modules/primitive/repotool/hdlist.tgz',
                         fetchdir=False,
                         destdir=self.prefix,
                         overwrite=False)
        fc.execute()
      
        if os.uname()[4] in ['i386', 'i486', 'i586', 'i686']:
            self.arch = 'i386'
        else:
            self.arch =  os.uname()[4]
       
        unpack(self.prefix  / 'hdlist.tgz', self.prefix)

    def tearDown(self):
        self.prefix.rmtree()
   
    def checkHdlist(self, file1, file2):
        fd = open(file1, 'r')
        content = fd.read()
        fd.close()

        assert content.find('kernel') != -1
        assert content.find('perl-Digest-HMAC') != -1
        assert content.find('php-ldap') != -1
        assert content.find('xorg-x11-xfs-utils') != -1

        fd = open(file2, 'r')
        content = fd.read()
        fd.close()

        assert content.find('vmlinuz') != -1
        assert content.find('HMAC_MD5.pm') != -1
        assert content.find('ldap.ini') != -1
        assert content.find('xfsinfo') != -1

    def testRedHatMake(self):
        (self.prefix / 'RedHat' / 'base').makedirs()
        (self.prefix / 'RedHat' / 'RPMS').makedirs()

        (self.prefix / 'comps.xml').move(self.prefix / 'RedHat' / 'base' / 'comps.xml')
        for r in self.prefix.glob('*.rpm'):
            r.move(self.prefix / 'RedHat' / 'RPMS')

        repo = RedHat4Repo(self.prefix, self.arch)
        repo.make()

        assert (self.prefix / 'RedHat' / 'base' / 'hdlist').exists()
        assert (self.prefix / 'RedHat' / 'base' / 'hdlist2').exists()

        self.checkHdlist(self.prefix / 'RedHat' / 'base' / 'hdlist', \
                         self.prefix / 'RedHat' / 'base' / 'hdlist2')

    def testCentosMake(self):
        (self.prefix / 'CentOS' / 'base').makedirs()
        (self.prefix / 'CentOS' / 'RPMS').makedirs()

        (self.prefix / 'comps.xml').move(self.prefix / 'CentOS' / 'base' / 'comps.xml')
        for r in self.prefix.glob('*.rpm'):
            r.move(self.prefix / 'CentOS' / 'RPMS')

        repo = Centos4Repo(self.prefix, self.arch)
        repo.make()

        assert (self.prefix / 'CentOS' / 'base' / 'hdlist').exists()
        assert (self.prefix / 'CentOS' / 'base' / 'hdlist2').exists()

        self.checkHdlist(self.prefix / 'CentOS' / 'base' / 'hdlist', \
                         self.prefix / 'CentOS' / 'base' / 'hdlist2')



