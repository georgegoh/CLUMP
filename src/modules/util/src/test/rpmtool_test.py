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

from kusu.util import testing
from kusu.util import rpmtool

cachedir = path(tempfile.mkdtemp(prefix='rpmtool', dir=os.environ['KUSU_TMP']))

def setUp():
    url = 'http://www.osgdc.org/pub/build/tests/modules/rpmtool/'

    rpms = ['openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm',
            'openoffice.org-xsltfilter-2.0.4-5.4.17.2.i386.rpm',
            'php5-sqlite-5.2.0-14.x86_64.rpm',
            'php5-sqlite-5.2.0-16.x86_64.rpm',
            'php-ldap-5.1.6-11.el5.i386.rpm',
            'php-ldap-5.1.6-12.el5.i386.rpm',
            'php-ldap-5.1.6-7.el5.i386.rpm',
            'segatex-3.04-1.el5.rf.i386.rpm',
            'segatex-3.05-1.el5.rf.i386.rpm']

    for r in rpms:
        testing.download(url + r, dest=cachedir)

def tearDown():
    if cachedir.exists():
        cachedir.rmtree()

class TestRPMTool:

    def testgetName(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getName() == 'openoffice.org-xsltfilter'
  
    def testgetVersion(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getVersion() == '2.0.4'
    
    def testgetRelease(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getRelease() == '5.4.17.1'

    def testgetEpoch(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        # This rpm has epoch == 1
        # rpm -qp --qf="%{epoch}\n}" openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm
        assert r.getEpoch() == 1

    def testgetArch(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getArch() == 'i386'
   
     
