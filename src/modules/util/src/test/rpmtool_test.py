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
            'php-ldap-5.1.6-11.el5.i386.rpm',
            'php-ldap-5.1.6-12.el5.i386.rpm',
            'php-ldap-5.1.6-7.el5.i386.rpm',
            'segatex-3.04-1.el5.rf.i386.rpm',
            'segatex-3.05-1.el5.rf.i386.rpm', 
            'blogtk-1.0-1.1.fc2.dag.i386.rpm',
            'blogtk-1.1-1.fc2.rf.i386.rpm', 
            'myconflictpkg-1-1.i386.rpm',
            'kernel-2.6.18-1.2798.fc6.i386.rpm', 
            'kernel-2.6.20-1.2952.fc6.i386.rpm',
            'kernel-2.6.20-1.2962.fc6.i386.rpm', 
            'gaim-1.0.3-0.EL4.1.i386.rpm',
            'gaim-1.1.4-1.EL4.i386.rpm',
            'gaim-1.2.1-4.el4.i386.rpm',
            'gaim-1.2.1-6.el4.i386.rpm',
            'gaim-1.3.1-0.el4.3.i386.rpm',
            'gaim-1.3.1-0.el4.i386.rpm',
            'gaim-1.5.0-12.el4.i386.rpm',
            'mysql-4.1.10a-1.RHEL4.1.i386.rpm',
            'mysql-4.1.10a-2.RHEL4.1.i386.rpm',
            'mysql-4.1.12-3.RHEL4.1.i386.rpm',
            'mysql-4.1.20-1.RHEL4.1.i386.rpm',
            'mysql-4.1.20-2.RHEL4.1.i386.rpm',
            'mysql-4.1.7-4.RHEL4.1.i386.rpm',
            'kernel-2.6.9-11.EL.i386.rpm',
            'kernel-2.6.9-22.0.1.EL.i386.rpm',
            'kernel-2.6.9-22.0.2.EL.i386.rpm',
            'kernel-2.6.9-22.EL.i386.rpm',
            'kernel-2.6.9-34.0.1.EL.i386.rpm',
            'kernel-2.6.9-34.0.2.EL.i386.rpm',
            'kernel-2.6.9-34.EL.i386.rpm',
            'kernel-2.6.9-42.0.10.EL.i386.rpm',
            'kernel-2.6.9-42.0.2.EL.i386.rpm',
            'kernel-2.6.9-42.0.3.EL.i386.rpm',
            'kernel-2.6.9-42.0.8.EL.i386.rpm',
            'kernel-2.6.9-42.EL.i386.rpm',
            'kernel-2.6.9-5.0.3.EL.i386.rpm',
            'kernel-2.6.9-5.0.5.EL.i386.rpm',
            'kernel-2.6.9-5.EL.i386.rpm',
            'kernel-2.6.9-55.0.2.EL.i386.rpm',
            'kernel-2.6.9-55.EL.i386.rpm']

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

        r = rpmtool.RPM(str(cachedir / 'php-ldap-5.1.6-11.el5.i386.rpm'))
        assert r.getEpoch() == 0

    def testgetArch(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        assert r.getArch() == 'i386'

        r = rpmtool.RPM(str(cachedir / 'php5-sqlite-5.2.0-14.x86_64.rpm'))
        assert r.getArch() == 'x86_64'

    def testgetBuildhost(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getBuildhost() == 'builder6'

    def testgetProvides(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
    
        assert r.getProvides()[0][0] == 'openoffice.org-xsltfilter'
   
    def testgetVendor(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getVendor() == 'CentOS'

    def testgetInstallTime(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        
        # Not installed
        assert r.getInstallTime() == None

    def testgetFileList(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getFileList()[0] == '/usr/lib/openoffice.org2.0'

    def testgetRequires(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getRequires()[0][0] == 'openoffice.org-core'

    def testgetChangelog(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getChangelog()[0]['TEXT'] == '- Resolves: CVE-2007-0239 rhbz#228002 shell ' \
                                             'escape\n- Resolves: CVE-2007-0238 rhbz#226967 ' \
                                             'starcalc overflow'
        assert r.getChangelog()[0]['NAME'] == 'Caolan McNamara <caolanm@redhat.com> - 1:2.0.4-5.4.17.1'
        assert r.getChangelog()[0]['TIME'] == 1172268000

    def testgetSummary(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r.getSummary() == 'extra xsltfilter module for openoffice.org'

    def testgetConflicts(self):
        r = rpmtool.RPM(str(cachedir / 'myconflictpkg-1-1.i386.rpm'))
       
        assert r.getConflicts()[0] == 'conflictwiththisrpm'

    def testEqual(self):
        r1 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))

        assert r1 == r1

    def testLessThan(self):
        r1 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.2.i386.rpm'))

        assert r1 < r2

        r1 = rpmtool.RPM(str(cachedir / 'segatex-3.04-1.el5.rf.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'segatex-3.05-1.el5.rf.i386.rpm'))

        assert r1 < r2

        r1 = rpmtool.RPM(str(cachedir / 'blogtk-1.0-1.1.fc2.dag.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'blogtk-1.1-1.fc2.rf.i386.rpm'))

        assert r1 < r2

    def testGreaterThan(self):
        r1 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.2.i386.rpm'))

        assert r2 > r1

        r1 = rpmtool.RPM(str(cachedir / 'segatex-3.04-1.el5.rf.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'segatex-3.05-1.el5.rf.i386.rpm'))

        assert r2 > r1

        r1 = rpmtool.RPM(str(cachedir / 'blogtk-1.0-1.1.fc2.dag.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'blogtk-1.1-1.fc2.rf.i386.rpm'))

        assert r2 > r1

    def testNotEqual(self):
        r1 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.2.i386.rpm'))
        assert r1 != r2

        r1 = rpmtool.RPM(str(cachedir / 'segatex-3.04-1.el5.rf.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'segatex-3.05-1.el5.rf.i386.rpm'))
        assert r1 != r2

    def testSort(self):
        r1 = rpmtool.RPM(str(cachedir / 'php-ldap-5.1.6-11.el5.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'php-ldap-5.1.6-12.el5.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'php-ldap-5.1.6-7.el5.i386.rpm'))

        lst = [r1, r2, r3]
        lst.sort()

        assert lst[0] == r3
        assert lst[1] == r1
        assert lst[2] == r2

        r1 = rpmtool.RPM(str(cachedir / 'segatex-3.04-1.el5.rf.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'segatex-3.05-1.el5.rf.i386.rpm'))

        lst = [r1, r2]
        lst.sort()

        assert lst[0] == r1
        assert lst[1] == r2

        r1 = rpmtool.RPM(str(cachedir / 'kernel-2.6.18-1.2798.fc6.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'kernel-2.6.20-1.2952.fc6.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'kernel-2.6.20-1.2962.fc6.i386.rpm'))

        lst = [r1, r2, r3]
        lst.sort()

        assert lst[0] == r1
        assert lst[1] == r2
        assert lst[2] == r3

        r1 = rpmtool.RPM(str(cachedir / 'gaim-1.0.3-0.EL4.1.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'gaim-1.1.4-1.EL4.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'gaim-1.2.1-4.el4.i386.rpm'))
        r4 = rpmtool.RPM(str(cachedir / 'gaim-1.2.1-6.el4.i386.rpm'))
        r5 = rpmtool.RPM(str(cachedir / 'gaim-1.3.1-0.el4.i386.rpm'))
        r6 = rpmtool.RPM(str(cachedir / 'gaim-1.3.1-0.el4.3.i386.rpm'))
        r7 = rpmtool.RPM(str(cachedir / 'gaim-1.5.0-12.el4.i386.rpm'))

        lst = [r1, r2, r3, r4, r5, r6, r7]
        lst.sort()

        assert lst[0] == r1
        assert lst[1] == r2
        assert lst[2] == r3
        assert lst[3] == r4
        assert lst[4] == r5
        assert lst[5] == r6
        assert lst[6] == r7

        r1 = rpmtool.RPM(str(cachedir / 'mysql-4.1.10a-1.RHEL4.1.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'mysql-4.1.10a-2.RHEL4.1.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'mysql-4.1.12-3.RHEL4.1.i386.rpm'))
        r4 = rpmtool.RPM(str(cachedir / 'mysql-4.1.20-1.RHEL4.1.i386.rpm'))
        r5 = rpmtool.RPM(str(cachedir / 'mysql-4.1.20-2.RHEL4.1.i386.rpm'))
        r6 = rpmtool.RPM(str(cachedir / 'mysql-4.1.7-4.RHEL4.1.i386.rpm'))

        lst = [r1, r2, r3, r4, r5, r6]
        lst.sort()

        assert lst[0] == r6
        assert lst[1] == r1
        assert lst[2] == r2
        assert lst[3] == r3
        assert lst[4] == r4
        assert lst[5] == r5

        r1 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-5.EL.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-5.0.3.EL.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-5.0.5.EL.i386.rpm'))
        r4 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-11.EL.i386.rpm'))
        r5 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-22.EL.i386.rpm'))
        r6 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-22.0.1.EL.i386.rpm'))
        r7 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-22.0.2.EL.i386.rpm'))
        r8 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-34.EL.i386.rpm'))
        r9 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-34.0.1.EL.i386.rpm'))
        r10 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-34.0.2.EL.i386.rpm'))
        r11 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.EL.i386.rpm'))
        r12 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.0.2.EL.i386.rpm'))
        r13 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.0.3.EL.i386.rpm'))
        r14 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.0.8.EL.i386.rpm'))
        r15 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.0.10.EL.i386.rpm'))
        r16 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-55.EL.i386.rpm'))
        r17 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-55.0.2.EL.i386.rpm'))
        r18 = rpmtool.RPM(str(cachedir / 'kernel-2.6.18-1.2798.fc6.i386.rpm'))
        r19 = rpmtool.RPM(str(cachedir / 'kernel-2.6.20-1.2952.fc6.i386.rpm'))
        r20 = rpmtool.RPM(str(cachedir / 'kernel-2.6.20-1.2962.fc6.i386.rpm'))
       
        lst = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10,
               r11, r12, r13, r14, r15, r16, r17, r18, r19, r20]
        lst.sort()

        assert lst[0] == r1
        assert lst[1] == r2
        assert lst[2] == r3
        assert lst[3] == r4
        assert lst[4] == r5
        assert lst[5] == r6
        assert lst[6] == r7
        assert lst[7] == r8
        assert lst[8] == r9
        assert lst[9] == r10
        assert lst[10] == r11
        assert lst[11] == r12
        assert lst[12] == r13
        assert lst[13] == r14
        assert lst[14] == r15
        assert lst[15] == r16
        assert lst[16] == r17
        assert lst[17] == r18
        assert lst[18] == r19
        assert lst[19] == r20

    def testReverseSort(self):
        r1 = rpmtool.RPM(str(cachedir / 'php-ldap-5.1.6-11.el5.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'php-ldap-5.1.6-12.el5.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'php-ldap-5.1.6-7.el5.i386.rpm'))

        lst = [r1, r2, r3]
        lst.sort(reverse=True)

        assert lst[0] == r2
        assert lst[1] == r1
        assert lst[2] == r3

        r1 = rpmtool.RPM(str(cachedir / 'segatex-3.04-1.el5.rf.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'segatex-3.05-1.el5.rf.i386.rpm'))

        lst = [r1, r2]
        lst.sort(reverse=True)

        assert lst[0] == r2
        assert lst[1] == r1

        r1 = rpmtool.RPM(str(cachedir / 'kernel-2.6.18-1.2798.fc6.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'kernel-2.6.20-1.2952.fc6.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'kernel-2.6.20-1.2962.fc6.i386.rpm'))

        lst = [r1, r2, r3]
        lst.sort(reverse=True)

        assert lst[0] == r3
        assert lst[1] == r2
        assert lst[2] == r1

        r1 = rpmtool.RPM(str(cachedir / 'gaim-1.0.3-0.EL4.1.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'gaim-1.1.4-1.EL4.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'gaim-1.2.1-4.el4.i386.rpm'))
        r4 = rpmtool.RPM(str(cachedir / 'gaim-1.2.1-6.el4.i386.rpm'))
        r5 = rpmtool.RPM(str(cachedir / 'gaim-1.3.1-0.el4.i386.rpm'))
        r6 = rpmtool.RPM(str(cachedir / 'gaim-1.3.1-0.el4.3.i386.rpm'))
        r7 = rpmtool.RPM(str(cachedir / 'gaim-1.5.0-12.el4.i386.rpm'))

        lst = [r1, r2, r3, r4, r5, r6, r7]
        lst.sort(reverse=True)

        assert lst[0] == r7
        assert lst[1] == r6
        assert lst[2] == r5
        assert lst[3] == r4
        assert lst[4] == r3
        assert lst[5] == r2
        assert lst[6] == r1

        r1 = rpmtool.RPM(str(cachedir / 'mysql-4.1.10a-1.RHEL4.1.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'mysql-4.1.10a-2.RHEL4.1.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'mysql-4.1.12-3.RHEL4.1.i386.rpm'))
        r4 = rpmtool.RPM(str(cachedir / 'mysql-4.1.20-1.RHEL4.1.i386.rpm'))
        r5 = rpmtool.RPM(str(cachedir / 'mysql-4.1.20-2.RHEL4.1.i386.rpm'))
        r6 = rpmtool.RPM(str(cachedir / 'mysql-4.1.7-4.RHEL4.1.i386.rpm'))

        lst = [r1, r2, r3, r4, r5, r6]
        lst.sort(reverse=True)

        assert lst[0] == r5
        assert lst[1] == r4
        assert lst[2] == r3
        assert lst[3] == r2
        assert lst[4] == r1
        assert lst[5] == r6

        r1 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-5.EL.i386.rpm'))
        r2 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-5.0.3.EL.i386.rpm'))
        r3 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-5.0.5.EL.i386.rpm'))
        r4 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-11.EL.i386.rpm'))
        r5 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-22.EL.i386.rpm'))
        r6 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-22.0.1.EL.i386.rpm'))
        r7 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-22.0.2.EL.i386.rpm'))
        r8 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-34.EL.i386.rpm'))
        r9 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-34.0.1.EL.i386.rpm'))
        r10 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-34.0.2.EL.i386.rpm'))
        r11 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.EL.i386.rpm'))
        r12 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.0.2.EL.i386.rpm'))
        r13 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.0.3.EL.i386.rpm'))
        r14 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.0.8.EL.i386.rpm'))
        r15 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-42.0.10.EL.i386.rpm'))
        r16 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-55.EL.i386.rpm'))
        r17 = rpmtool.RPM(str(cachedir / 'kernel-2.6.9-55.0.2.EL.i386.rpm'))
        r18 = rpmtool.RPM(str(cachedir / 'kernel-2.6.18-1.2798.fc6.i386.rpm'))
        r19 = rpmtool.RPM(str(cachedir / 'kernel-2.6.20-1.2952.fc6.i386.rpm'))
        r20 = rpmtool.RPM(str(cachedir / 'kernel-2.6.20-1.2962.fc6.i386.rpm'))
       
        lst = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10,
               r11, r12, r13, r14, r15, r16, r17, r18, r19, r20]
        lst.sort(reverse=True)

        assert lst[0] == r20
        assert lst[1] == r19
        assert lst[2] == r18
        assert lst[3] == r17
        assert lst[4] == r16
        assert lst[5] == r15
        assert lst[6] == r14
        assert lst[7] == r13
        assert lst[8] == r12
        assert lst[9] == r11
        assert lst[10] == r10
        assert lst[11] == r9
        assert lst[12] == r8
        assert lst[13] == r7
        assert lst[14] == r6
        assert lst[15] == r5
        assert lst[16] == r4
        assert lst[17] == r3
        assert lst[18] == r2
        assert lst[19] == r1



class TestRPMToolMockRPM:
    """Test for mock RPM object that isn't created by a rpm file"""
    def testgetName(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r = rpmtool.RPM(name=r.getName(), version=r.getVersion(), 
                        release=r.getRelease(), epoch=r.getEpoch(),
                        arch=r.getArch())

        assert r.getName() == 'openoffice.org-xsltfilter'

    def testgetVersion(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r = rpmtool.RPM(name=r.getName(), version=r.getVersion(), 
                        release=r.getRelease(), epoch=r.getEpoch(),
                        arch=r.getArch())

        assert r.getVersion() == '2.0.4'
    
    def testgetRelease(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r = rpmtool.RPM(name=r.getName(), version=r.getVersion(), 
                        release=r.getRelease(), epoch=r.getEpoch(),
                        arch=r.getArch())

        assert r.getRelease() == '5.4.17.1'

    def testgetEpoch(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r = rpmtool.RPM(name=r.getName(), version=r.getVersion(), 
                        release=r.getRelease(), epoch=r.getEpoch(),
                        arch=r.getArch())
        
        # This rpm has epoch == 1
        # rpm -qp --qf="%{epoch}\n}" openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm
        assert r.getEpoch() == 1

        r = rpmtool.RPM(str(cachedir / 'php-ldap-5.1.6-11.el5.i386.rpm'))
        r = rpmtool.RPM(name=r.getName(), version=r.getVersion(), 
                        release=r.getRelease(), epoch=r.getEpoch(),
                        arch=r.getArch())
        
        assert r.getEpoch() == 0

    def testgetArch(self):
        r = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r = rpmtool.RPM(name=r.getName(), version=r.getVersion(), 
                        release=r.getRelease(), epoch=r.getEpoch(),
                        arch=r.getArch())
        assert r.getArch() == 'i386'

        r = rpmtool.RPM(str(cachedir / 'php5-sqlite-5.2.0-14.x86_64.rpm'))
        r = rpmtool.RPM(name=r.getName(), version=r.getVersion(), 
                        release=r.getRelease(), epoch=r.getEpoch(),
                        arch=r.getArch())
        assert r.getArch() == 'x86_64'

    def testEqual(self):
        r1 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r1 = rpmtool.RPM(name=r1.getName(), version=r1.getVersion(), 
                         release=r1.getRelease(), epoch=r1.getEpoch(),
                         arch=r1.getArch())
 
        assert r1 == r1

    def testLessThan(self):
        r1 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r1 = rpmtool.RPM(name=r1.getName(), version=r1.getVersion(), 
                         release=r1.getRelease(), epoch=r1.getEpoch(),
                         arch=r1.getArch())
        r2 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.2.i386.rpm'))
        r2 = rpmtool.RPM(name=r2.getName(), version=r2.getVersion(), 
                        release=r2.getRelease(), epoch=r2.getEpoch(),
                        arch=r2.getArch())
        
        assert r1 < r2

    def testGreaterThan(self):
        r1 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r1 = rpmtool.RPM(name=r1.getName(), version=r1.getVersion(), 
                         release=r1.getRelease(), epoch=r1.getEpoch(),
                         arch=r1.getArch())
        r2 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.2.i386.rpm'))
        r2 = rpmtool.RPM(name=r2.getName(), version=r2.getVersion(), 
                        release=r2.getRelease(), epoch=r2.getEpoch(),
                        arch=r2.getArch())
 
        assert r2 > r1

    def testNotEqual(self):
        r1 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.1.i386.rpm'))
        r1 = rpmtool.RPM(name=r1.getName(), version=r1.getVersion(), 
                         release=r1.getRelease(), epoch=r1.getEpoch(),
                         arch=r1.getArch())
        r2 = rpmtool.RPM(str(cachedir / 'openoffice.org-xsltfilter-2.0.4-5.4.17.2.i386.rpm'))
        r2 = rpmtool.RPM(name=r2.getName(), version=r2.getVersion(), 
                        release=r2.getRelease(), epoch=r2.getEpoch(),
                        arch=r2.getArch())
        
        assert r1 != r2




