#!/usr/bin/env python
#
# $Id: yumrepo_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
from path import path
import tempfile
import subprocess

from primitive.support import yum
from primitive.core.errors import *

from nose.tools import assert_raises

cachedir = path(tempfile.mkdtemp(prefix='yumrepo', dir='/tmp'))

class CopyFailedError(Exception): pass
class NotSupportedURIError(Exception): pass


def url_mirror_copy(src, dst):
    """Performs a mirror copy of a http or ftp url.
       It will mirror everything that is under the 
       url.
    """ 
    import urlparse
    import errno

    if urlparse.urlsplit(src)[0] in ['http', 'ftp']:
        p = path(urlparse.urlsplit(src)[2]).splitall()

        # Deals with non-ending slash. 
        # Non-ending slash url ends up with an empty string in the 
        # last index of the list when a splitall is done
        if not p[-1]: 
            cutaway = len(p[1:]) - 1
        else: # non-ending slash
            cutaway = len(p[1:])
            src = src + '/' # Append a trailing slash

        if cutaway <= 0:
            cutaway = 0

        cmd = 'wget -m -np -nH --cut-dirs=%s %s' % (cutaway, src)

        try:
            p = subprocess.Popen(cmd,
                                 cwd = dst,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode

        except OSError, e:
            if e.errno == errno.ENOENT:
                raise FileDoesNotExistError, 'wget or destination dir not found' 
            else:
                raise CommandFailedToRunError, 'Unable to copy. Error Message: %s' % os.strerror(e.errno)

        except:
            raise CommandFailedToRunError

        if retcode:
            raise CopyFailedError, 'Failed to copy %s to %s' % (src,dst)
        else:
            return True
    else:
        raise NotSupportedURIError

def setup():
    url = 'http://www.osgdc.org/pub/build/tests/modules/yumrepo/'
    url_mirror_copy(url, cachedir) 

def teardown():
    if cachedir.exists():
        cachedir.rmtree()

class TestWorkingLocalYumRepo:

    def setUp(self):
        self.y = yum.YumRepo('file://' + str(cachedir / 'working'))

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

        assert r.getFilename() == 'file://' + str(cachedir / 'working/CentOS/cyrus-sasl-ldap-2.1.22-4.i386.rpm')

