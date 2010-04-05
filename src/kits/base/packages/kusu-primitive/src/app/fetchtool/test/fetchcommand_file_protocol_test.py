#!/usr/bin/env python
# $Id: fetchcommand_file_protocol_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for the FileCommand class of the FetchTool.
"""
import urllib
import tarfile
from sets import Set
from path import path
from tempfile import mkdtemp
from primitive.fetchtool.commands import FetchCommand
from primitive.fetchtool.helper import matchFileMD5SUM

TESTDIR1_TARBALL_URL = 'http://www.osgdc.org/pub/build/tests/modules/primitive/fetchtool/testdir.tar.bz2'
TESTDIR2_TARBALL_URL = 'http://www.osgdc.org/pub/build/tests/modules/primitive/fetchtool/testdir2.tar.bz2'
TESTFILE1_MD5SUM = 'f0ef7081e1539ac00ef5b761b4fb01b3'
TESTFILE2_MD5SUM = 'b6762754c468d6256f7887e56dd8dcbc'

def hasSrcFiles(src_dir, dest_dir):
    ''' Verify dest_dir has all the files and directories that src_dir has.
    '''
    s = path(src_dir)
    d = path(dest_dir)
    s_files = [x.basename() for x in s.files()]
    s_dirs = [x.basename() for x in s.dirs()]
    d_files = [x.basename() for x in d.files()]
    d_dirs = [x.basename() for x in d.dirs()]

    if not Set(s_files).issubset(Set(d_files)) \
       or \
       not Set(s_dirs).issubset(Set(d_dirs)):
        return False

    for dir_ in filter(lambda x: not x.islink(), s.dirs()):
        if not hasSrcFiles(s/dir_, d/dir_):
            return False

    return True


class TestFileProtocol(object):
    ''' Test cases for the file: protocol '''
    def setup(self):
        ''' Need a known directory for the test, so download
            from www.osgdc.org.
        '''
        # get the premade directory structure from OSGDC.
        tarball_dir = path(mkdtemp(prefix='TestFileProtocolTarball'))
        tarball_path = tarball_dir / 'testdir.tar.bz2'
        urllib.urlretrieve(TESTDIR1_TARBALL_URL,
                           tarball_path)

        # for overwrite tests.
        tarball2_path = tarball_dir / 'testdir2.tar.bz2'
        urllib.urlretrieve(TESTDIR2_TARBALL_URL,
                           tarball2_path)

        # set up src dir.
        self.src_dir = path(mkdtemp(prefix='TestFileProtocolSrc'))
        self.src_dir2 = path(mkdtemp(prefix='TestFileProtocolSrc2'))
        self.dest_dir = path(mkdtemp(prefix='TestFileProtocolDest'))

        # extract tarball for tests.
        tar = tarfile.open(tarball_path)
        [ tar.extract(x, path=self.src_dir) for x in tar.getmembers() ]

        tar = tarfile.open(tarball2_path)
        [ tar.extract(x, path=self.src_dir2) for x in tar.getmembers() ]
        tarball_dir.rmtree()

    def teardown(self):
        ''' Remove the temporary directories created.'''
        self.src_dir.rmtree()
        self.src_dir2.rmtree()
        self.dest_dir.rmtree()

    def testCopyDirPositive(self):
        ''' Copy a directory via file:// protocol (no overwrite)
            This test is a straightforward test of the copy directory,
            with no overwrite.
            Preconditions:
            * destination directory is empty.
        '''
        uri = 'file://%s' % self.src_dir
        fc = FetchCommand(uri=uri,
                          fetchdir=True,
                          destdir=self.dest_dir,
                          overwrite=False)
        status,dest = fc.execute()
        # Test for directories, dest dir is the same as the one supplied.
        assert status
        assert dest == self.dest_dir
        assert path(dest).exists() 
        assert path(dest).isdir()
        assert hasSrcFiles(self.src_dir, self.dest_dir)
        

    def testCopyDirOverwritePositive(self):
        ''' Copy a directory via file:// protocol to existing \
 destination (with overwrite)
            This test exercises the overwrite option by having data
            existing from a previous operation.
        '''
        self.testCopyDirPositive()
        assert matchFileMD5SUM(TESTFILE1_MD5SUM,
                               self.dest_dir / 'testdir' / 'sub2' / 'testfile')

        # should have existing directory structure here.
        uri = 'file://%s' % self.src_dir2
        fc = FetchCommand(uri=uri,
                          fetchdir=True,
                          destdir=self.dest_dir,
                          overwrite=True)
        status,dest = fc.execute()
        assert status
        assert dest == self.dest_dir 
        assert path(dest).exists() 
        assert path(dest).isdir()
        assert hasSrcFiles(self.src_dir2, self.dest_dir)
        assert matchFileMD5SUM(TESTFILE2_MD5SUM,
                               self.dest_dir / 'testdir' / 'sub2' / 'testfile')

    def testCopyDirOverwriteNegative(self):
        ''' Copy a directory via file:// protocol to existing \
 destination (no overwrite)
            This test confirms that the destination directory will
            not be touched if overwrite is false.
        '''
        self.testCopyDirPositive()
        assert matchFileMD5SUM(TESTFILE1_MD5SUM,
                               self.dest_dir / 'testdir' / 'sub2' / 'testfile')

        # should have existing directory structure here.
        uri = 'file://%s' % self.src_dir
        fc = FetchCommand(uri=uri,
                          fetchdir=True,
                          destdir=self.dest_dir,
                          overwrite=False)
        status, dest = fc.execute()
        assert status # Even though we are not overwriting, the command has exit successfully
        assert hasSrcFiles(self.src_dir, self.dest_dir)
        assert matchFileMD5SUM(TESTFILE1_MD5SUM,
                               self.dest_dir / 'testdir' / 'sub2' / 'testfile')
