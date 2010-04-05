#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#

from primitive.repo.yast import YastRepo
from primitive.fetchtool.commands import FetchCommand
from primitive.support.util import MD5SUM

from path import path


from nose import SkipTest
import tempfile
import os
import tarfile
import sha

prefix = None
cachedir = path(tempfile.mkdtemp(prefix='repo'))

ROOTIMG1_URL="http://www.osgdc.org/pub/build/tests/modules/primitive/repotool/root"
UPDATEIMG1_URL="http://www.osgdc.org/pub/build/tests/modules/primitive/repotool/update1.img"
ROOTIMG1_MD5SUM="880593231d77c933dbe375034e517ab8"
ROOTIMG2_MD5SUM="36cabf3f19ea520b41f9cc0440cde72c"

def download(filename, dest, cache=cachedir):
    global cachedir

    if (cache / filename).exists():
        (cache / filename).copy(dest)
        return

    import urllib2
    url = 'http://www.osgdc.org/pub/build/tests/modules/primitive/repotool/'
    f = urllib2.urlopen(url + filename)
    content = f.read()
    f.close()

    f = open(cache / filename, 'w')
    f.write(content)
    f.close()

    (cache / filename).copy(dest)


def unpack(filename, dest):
    tar = tarfile.open(filename, 'r:gz')
    for tarinfo in tar:
        tar.extract(tarinfo.name, dest)
    tar.close()

def setup():
    pass

def teardown():
    global cachedir
    cachedir.rmtree()

class TestOSMediaYast:
    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repo'))

        download('os.tgz', self.prefix)
        unpack(self.prefix / 'os.tgz', self.prefix)
        self.repo = YastRepo(self.prefix)

    def tearDown(self):
        self.prefix.rmtree()

    def testCheckOSMedia(self):
        assert self.repo.checkOSMedia() == True

    def testMakeMedia(self):
        self.repo.makeMedia()
        assert (self.prefix / 'media.1' / 'media').exists()

        f = open(self.prefix / 'media.1' / 'media', 'r')
        content = f.read()
        assert content.find('primitive') == -1

    def testMakeProducts(self):
        self.repo.makeProducts()
        assert (self.prefix / 'media.1' / 'products').exists()

        f = open(self.prefix / 'media.1' / 'products', 'r')
        content = f.read()
        assert content.find('primitive') == -1

    def testMakeMeta(self):
        self.repo.makeMeta()
        assert (self.prefix / 'suse' / 'setup' / 'descr' / 'packages').exists()

        f = open(self.prefix / 'suse' / 'setup' / 'descr' / 'packages', 'r')
        content = f.read()
        f.close()

        assert content.find('rpmsections') != -1

        f = open(self.prefix / 'suse' / 'setup' / 'descr' / 'packages', 'r')
        content = f.read()
        f.close()

        assert content.find('rpmsections') != -1

    def testMakeContent(self):
        self.repo.makeMeta()
        self.repo.makeContent()

        assert (self.prefix / 'content').exists()

        f = open(self.prefix / 'content', 'r')
        content = f.read()
        f.close()

        assert content.find('packages') != -1
 
        assert content.find(sha.new((self.prefix / 'suse' / 'setup' / 'descr' / 'packages').open().read()).hexdigest()) != -1

        assert content.find('PRODUCT') != -1
        assert content.find('LABEL') != -1
        assert content.find('VENDOR') != -1
        assert content.find('ARCH') != -1
        assert content.find('DEFAULTBASE') != -1
        assert content.find('DESCRDIR') != -1

    def testWriteMedia(self):
        self.repo.writeMedia(vendor='test', timestamp='123', mediacount=999)

        f = open(self.prefix / 'media.1' / 'media', 'r')
        media = f.read()
        f.close()

        assert media == 'test\n123\n999\n'
      
class TestNonOSMediaYast:
    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repo'))

        download('rpm.tgz', self.prefix)
        unpack(self.prefix / 'rpm.tgz', self.prefix)
        self.repo = YastRepo(self.prefix)

    def tearDown(self):
        self.prefix.rmtree()

    def testCheckOSMedia(self):
        assert self.repo.checkOSMedia() == False 

    def testMakeMedia(self):
        self.repo.makeMedia()
        assert (self.prefix / 'media.1' / 'media').exists()

        f = open(self.prefix / 'media.1' / 'media', 'r')
        content = f.read()
        assert content.find('primitive') != -1 

    def testMakeProducts(self):
        self.repo.makeProducts()
        assert (self.prefix / 'media.1' / 'products').exists()

        f = open(self.prefix / 'media.1' / 'products', 'r')
        content = f.read()
        assert content.find('primitive') != -1

    def testMakeMeta(self):
        self.repo.makeMeta()
        assert (self.prefix / 'setup' / 'descr' / 'packages').exists()

        f = open(self.prefix / 'setup' / 'descr' / 'packages', 'r')
        content = f.read()
        f.close()

        assert content.find('kernel') != -1
        assert content.find('perl-Digest-HMAC') != -1
        assert content.find('php-ldap') != -1
        assert content.find('xorg-x11-xfs-utils') != -1

        f = open(self.prefix / 'setup' / 'descr' / 'packages', 'r')
        content = f.read()
        f.close()

        assert content.find('kernel') != -1
        assert content.find('perl-Digest-HMAC') != -1
        assert content.find('php-ldap') != -1
        assert content.find('xorg-x11-xfs-utils') != -1

    def testMakeContent(self):
        self.repo.makeMeta()
        self.repo.makeContent()

        assert (self.prefix / 'content').exists()

        f = open(self.prefix / 'content', 'r')
        content = f.read()
        f.close()

        assert content.find('packages') != -1
 
        assert content.find(sha.new((self.prefix / 'setup' / 'descr' / 'packages').open().read()).hexdigest()) != -1

        assert content.find('PRODUCT') != -1
        assert content.find('LABEL') != -1
        assert content.find('VENDOR') != -1
        assert content.find('ARCH') != -1
        assert content.find('DEFAULTBASE') != -1
        assert content.find('DESCRDIR') != -1

class TestGeneralYast:

    def setUp(self):
        self.prefix = path(tempfile.mkdtemp(prefix='repo'))

    def tearDown(self):
        self.prefix.rmtree()

    def testDirectoryYast(self):
    
        (self.prefix / 'a').touch()
        (self.prefix / 'b').touch()
        (self.prefix / 'c').touch()

        y = YastRepo(self.prefix)
        y.makeDirectoryYast(self.prefix)

        assert (self.prefix / 'directory.yast').exists()

        f = open(self.prefix / 'directory.yast', 'r')
        assert len(f.read().strip().split('\n')) == 3
        f.close()

    def testMakeMD5(self):
    
        (self.prefix / 'a').touch()
        (self.prefix / 'b').touch()
        (self.prefix / 'c').touch()

        y = YastRepo(self.prefix)
        y.makeMD5(self.prefix)

        assert (self.prefix / 'MD5SUMS').exists()

        f = open(self.prefix / 'MD5SUMS', 'r')
        assert len(f.read().strip().split('\n')) == 3
        f.close()

    def testHandleUpdates(self):
        root_img_dir = self.prefix / 'boot' / 'i386'
        root_img_dir.makedirs()
        directory = self.prefix / 'boot' / 'directory.yast'
        directory.touch()
        directory.write_lines(['i386/'])

        fc = FetchCommand(uri=ROOTIMG1_URL, fetchdir=False,
                          destdir=root_img_dir, overwrite=True)
        root_img = fc.execute()[1]
        assert MD5SUM(root_img) == ROOTIMG1_MD5SUM
        y = YastRepo(self.prefix)
        y.makeContent()
        y.handleUpdates(UPDATEIMG1_URL)
        assert MD5SUM(root_img) != ROOTIMG1_MD5SUM
        assert MD5SUM(root_img) == ROOTIMG2_MD5SUM
