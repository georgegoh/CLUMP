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
from nose import SkipTest
from primitive.fetchtool.commands import FetchCommand
from primitive.core.errors import FetchException
from primitive.core.errors import HTTPAuthException
from primitive.core.errors import UnknownHostException
from primitive.fetchtool.helper import matchFileMD5SUM

TARBALL_NAME = 'acpid-1.0.4-5.i386.rpm'
TESTDIR_TARBALL_MD5SUM = '419158735d99bb73970768c23131e485'

class TestRHNProtocol(object):
    ''' Test cases for the http: protocol '''

    def setup(self):
        '''Create a temporary directory for the tests.'''
        self.target_dir = path(mkdtemp(prefix='TestRHNProtocol'))

    def teardown(self):
        '''Remove the temporary directory created for the tests.'''
        self.target_dir.rmtree()

    def testHTTPFetchFile(self):
        ''' Fetch a single file via RHN
        '''

        raise SkipTest
        # sample code. Need a real systemid to function

        fc = FetchCommand(uri='rhn://rhel-i386-server-5/' + TARBALL_NAME,
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False,
                          systemid=open('/tmp/systemid', 'r'),
                          up2dateURL='https://xmlrpc.rhn.redhat.com/XMLRPC')
        status, dest = fc.execute()

        assert status
        assert dest == path(self.target_dir) / TARBALL_NAME
        assert path(dest).exists() 
        assert path(dest).isfile()
        assert matchFileMD5SUM(TESTDIR_TARBALL_MD5SUM,
                               path(self.target_dir) / TARBALL_NAME)
    def testHTTPFetchYumMeta(self):
        ''' Fetch yum meta via RHN
        '''

        raise SkipTest
        # sample code. Need a real systemid to function

        fc = FetchCommand(uri='rhn://rhel-i386-server-5/repodata/repomd.xml',
                          fetchdir=False,
                          destdir=self.target_dir,
                          overwrite=False,
                          systemid=open('/tmp/systemid', 'r'),
                          up2dateURL='https://xmlrpc.rhn.redhat.com/XMLRPC')
        status, dest = fc.execute()

        assert status
        assert dest == path(self.target_dir) / 'repomd.xml'
        assert path(dest).exists() 
        assert path(dest).isfile()
        assert matchFileMD5SUM('md5sum',
                               path(self.target_dir) / 'repomd.xml')

