#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for the HTTPCommand class of the FetchTool.
"""
from path import path
from tempfile import mkdtemp
from nose.tools import assert_raises
from primitive.fetchtool.commands import FetchCommand
from primitive.core.errors import FetchException
from primitive.core.errors import HTTPAuthException
from primitive.core.errors import UnknownHostException
from primitive.fetchtool.helper import matchFileMD5SUM

TESTDIR_TARBALL_URL = 'http://www.osgdc.org/pub/build/tests/modules/primitive/fetchtool/'
TESTDIR_AUTH_URL = 'http://test:test@www.osgdc.org/pub/build/tests/modules/primitive/fetchtool-protected/'
TESTDIR_BADAUTH_URL = 'http://test:bad@www.osgdc.org/pub/build/tests/modules/primitive/fetchtool-protected/'
TARBALL_NAME = 'testdir.tar.bz2'
TESTDIR_TARBALL_MD5SUM = '64c795fb6cc5d41c62ee8f21725874d2'
TESTSUBDIR_TEST_MD5SUM = 'd41d8cd98f00b204e9800998ecf8427e'

class TestHTTPProtocol(object):
    ''' Test cases for the http: protocol '''

    def setup(self):
        '''Create a temporary directory for the tests.'''
        self.target_dir = path(mkdtemp(prefix='TestHTTPProtocol'))

    def teardown(self):
        '''Remove the temporary directory created for the tests.'''
        self.target_dir.rmtree()


    def testHTTPFetchFile(self):
        ''' Fetch a single file via HTTP
        '''
        fc = FetchCommand(uri=TESTDIR_TARBALL_URL + TARBALL_NAME,
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False)
        status , dest = fc.execute()
        assert status
        assert dest == path(self.target_dir) / TARBALL_NAME
        assert path(dest).exists() 
        assert path(dest).isfile()
        assert matchFileMD5SUM(TESTDIR_TARBALL_MD5SUM,
                               path(self.target_dir) / TARBALL_NAME)


    def testHTTPFetchFileNegative(self):
        ''' Fetch a bad URL via HTTP raises UnknownHostException
        '''
        fc = FetchCommand(uri='http://badurl/nofile',
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False)
        assert_raises(UnknownHostException, fc.execute)


    def testHTTPFetchFileAuth(self):
        ''' Fetch a single file via HTTP with authentication
        '''
        fc = FetchCommand(uri=TESTDIR_AUTH_URL + TARBALL_NAME,
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False)
        status, dest = fc.execute()
        assert status
        assert dest == path(self.target_dir) / TARBALL_NAME
        assert path(dest).exists() 
        assert path(dest).isfile()
        assert matchFileMD5SUM(TESTDIR_TARBALL_MD5SUM,
                               path(self.target_dir) / TARBALL_NAME)


    def testHTTPFetchFileAuthNegative(self):
        ''' Fetch a single file via HTTP with bad authentication \
            raises HTTPAuthException
        '''
        fc = FetchCommand(uri=TESTDIR_BADAUTH_URL + 'test',
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False)
        assert_raises(HTTPAuthException, fc.execute)


    def testHTTPFetchDir(self):
        ''' Mirror a directory via HTTP
        '''
        fc = FetchCommand(uri=TESTDIR_TARBALL_URL,
                          fetchdir=True,
                          destdir=self.target_dir,
                          overwrite=False)
        status,dest = fc.execute()
        assert status
        assert dest == path(self.target_dir)
        assert path(dest).exists() 


        assert matchFileMD5SUM(TESTDIR_TARBALL_MD5SUM,
                               path(self.target_dir) / TARBALL_NAME)
        assert matchFileMD5SUM(TESTSUBDIR_TEST_MD5SUM,
                               path(self.target_dir) / 'subdir' / 'test')


    def testHTTPFetchDirNegative(self):
        ''' Mirror a bad directory via HTTP raises FetchException
        '''
        fc = FetchCommand(uri=TESTDIR_TARBALL_URL + 'badplace',
                          fetchdir=True,
                          destdir=self.target_dir,
                          overwrite=False)
        assert_raises(FetchException, fc.execute)


    def testHTTPFetchDirAuth(self):
        ''' Mirror a directory via HTTP with authentication
        '''
        fc = FetchCommand(uri=TESTDIR_AUTH_URL,
                          fetchdir=True,
                          destdir=self.target_dir,
                          overwrite=False)
        status, dest = fc.execute()
        assert status
        assert dest == path(self.target_dir)
        assert path(dest).exists() 
        assert matchFileMD5SUM(TESTDIR_TARBALL_MD5SUM,
                               path(self.target_dir) / TARBALL_NAME)
        assert matchFileMD5SUM(TESTSUBDIR_TEST_MD5SUM,
                               path(self.target_dir) / 'subdir' / 'test')


    def testHTTPFetchDirAuthNegative(self):
        ''' Mirror a directory via HTTP with bad authentication \
            raises HTTPAuthException
        '''
        fc = FetchCommand(uri=TESTDIR_BADAUTH_URL,
                          fetchdir=True,
                          destdir=self.target_dir,
                          overwrite=False)
        assert_raises(HTTPAuthException, fc.execute)
