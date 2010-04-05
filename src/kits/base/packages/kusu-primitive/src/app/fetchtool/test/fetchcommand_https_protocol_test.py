#!/usr/bin/env python
# $Id: fetchcommand_https_protocol_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for the HTTPSCommand class of the FetchTool.
"""
from path import path
from tempfile import mkdtemp
from nose.tools import assert_raises
from primitive.core.errors import FetchException
from primitive.core.errors import HTTPAuthException
from primitive.core.errors import UnknownHostException
from primitive.fetchtool.helper import matchFileMD5SUM
from primitive.fetchtool.commands import FetchCommand

# This following URLs are from locations with self-signed certificates.
TESTDIR_TARBALL_URL = 'https://www.osgdc.org/pub/build/tests/modules/primitive/fetchtool/'
TESTDIR_AUTH_URL = 'https://test:test@www.osgdc.org/pub/build/tests/modules/primitive/fetchtool-protected/'
TESTDIR_BADAUTH_URL = 'https://test:bad@www.osgdc.org/pub/build/tests/modules/primitive/fetchtool-protected/'
TARBALL_NAME = 'testdir.tar.bz2'
TESTDIR_TARBALL_MD5SUM = '64c795fb6cc5d41c62ee8f21725874d2'
TESTSUBDIR_TEST_MD5SUM = 'd41d8cd98f00b204e9800998ecf8427e'


class TestHTTPSProtocol(object):
    ''' Test cases for the https: protocol '''

    def setup(self):
        '''Create a temporary directory for the tests.'''
        self.target_dir = path(mkdtemp(prefix='TestHTTPSProtocol'))

    def teardown(self):
        '''Remove the temporary directory created for the tests.'''
        self.target_dir.rmtree()


    def testHTTPSFetchFile(self):
        ''' Fetch a single file via HTTPS
        '''
        fc = FetchCommand(uri=TESTDIR_TARBALL_URL + TARBALL_NAME,
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False)
        status,dest = fc.execute()
        assert status
        assert path(dest).exists() 
        assert path(dest).isfile()
        assert dest == path(self.target_dir) / TARBALL_NAME
        assert matchFileMD5SUM(TESTDIR_TARBALL_MD5SUM,
                               path(self.target_dir) / TARBALL_NAME)


    def testHTTPSFetchFileNegative(self):
        ''' Fetch a bad URL via HTTPS raises UnknownHostException
        '''
        fc = FetchCommand(uri='https://badurl/nofile',
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False)
        assert_raises(UnknownHostException, fc.execute)


    def testHTTPSFetchFileAuth(self):
        ''' Fetch a single file via HTTPS with authentication
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


    def testHTTPSFetchFileAuthNegative(self):
        ''' Fetch a single file via HTTPS with bad authentication \
            raises HTTPAuthException
        '''
        fc = FetchCommand(uri=TESTDIR_BADAUTH_URL + TARBALL_NAME,
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False)
        assert_raises(HTTPAuthException, fc.execute)


    def testHTTPSFetchDir(self):
        ''' Mirror a directory via HTTPS
        '''
        fc = FetchCommand(uri=TESTDIR_TARBALL_URL,
                          fetchdir=True,
                          destdir=self.target_dir,
                          overwrite=False)
        status , dest = fc.execute()
        assert status
        assert dest == path(self.target_dir)
        assert path(dest).exists() 

        assert matchFileMD5SUM(TESTDIR_TARBALL_MD5SUM,
                               path(self.target_dir) / TARBALL_NAME)
        assert matchFileMD5SUM(TESTSUBDIR_TEST_MD5SUM,
                               path(self.target_dir) / 'subdir' / 'test')


    def testHTTPSFetchDirNegative(self):
        ''' Mirror a bad directory via HTTPS raises FetchException
        '''
        fc = FetchCommand(uri=TESTDIR_TARBALL_URL + 'badplace',
                          fetchdir=True,
                          destdir=self.target_dir,
                          overwrite=False)
        assert_raises(FetchException, fc.execute)


    def testHTTPSFetchDirAuth(self):
        ''' Mirror a directory via HTTPS with authentication
        '''
        fc = FetchCommand(uri=TESTDIR_AUTH_URL,
                          fetchdir=True,
                          destdir=self.target_dir,
                          overwrite=False)
        status,dest = fc.execute()
        assert status
        assert dest == path(self.target_dir)
        assert path(dest).exists() 
        assert path(dest).isdir()
        
        assert matchFileMD5SUM(TESTDIR_TARBALL_MD5SUM,
                               path(self.target_dir) / TARBALL_NAME)
        assert matchFileMD5SUM(TESTSUBDIR_TEST_MD5SUM,
                               path(self.target_dir) / 'subdir' / 'test')


    def testHTTPFetchDirAuthNegative(self):
        ''' Mirror a directory via HTTPS with bad authentication \
            raises HTTPAuthException
        '''
        fc = FetchCommand(uri=TESTDIR_BADAUTH_URL,
                          fetchdir=True,
                          destdir=self.target_dir,
                          overwrite=False)
        assert_raises(HTTPAuthException, fc.execute)
