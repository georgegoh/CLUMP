#!/usr/bin/env python
# $Id: installcommand_kickstart_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
""" Tests for generating Anaconda Kickstart files."""
import filecmp
import urlparse
from path import path
from tempfile import mkdtemp
from primitive.support.type import Struct
from primitive.fetchtool.commands import FetchCommand
from primitive.installtool.commands import GenerateAutoInstallScriptCommand

def testKickstart():
    template_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/kickstart.tmpl'
    verified_result_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/gen_ks.cfg'

    testAutoinstGen_dir = path(mkdtemp(prefix='TestKickstartGen'))
    gen_autoinst = testAutoinstGen_dir / 'myks.cfg'

    # fetch the verified result.
    protocol = urlparse.urlparse(verified_result_uri)[0]
    fc = FetchCommand(uri=verified_result_uri, fetchdir=False,
                      destdir=testAutoinstGen_dir, overwrite=True)
    fc.execute()

    verified_result = testAutoinstGen_dir / 'gen_ks.cfg'

    networkprofile = {'interfaces': {'eth0': {'configure': True,
                                              'use_dhcp': False,
                                              'ip_address': '192.168.1.99',
                                              'netmask': '255.255.255.0',
                                              'active_on_boot': False},
                                     'eth1': {'configure': True,
                                              'use_dhcp': True,
                                              'active_on_boot': True}},
                      'gw_dns_use_dhcp': False,
                      'fqhn_use_dhcp': False}
    packages = ['@ admin-tools',
                '@ system-tools',
                '@ text-internet',
                '@ compat-arch-support',
                '@ server-cfg',
                '@ development-tools',
                'lvm2',
                'kernel-devel',
                'e2fsprogs',
                'kernel']

    ic = GenerateAutoInstallScriptCommand(os={'name': 'centos', 'version': '4'},
                                          diskprofile=None,
                                          networkprofile=networkprofile,
                                          installsrc='http://10.10.10.171:8080/centos4/',
                                          rootpw='$1$R0u07JQv$LDKTlairsxqxnAxC5Yfbe/',
                                          tz='Asia/Singapore',
                                          tz_utc=False,
                                          lang='en_US',
                                          keyboard='us',
                                          packageprofile=packages,
                                          diskorder=[],
                                          template_uri=template_uri,
                                          outfile=gen_autoinst)

    ic.execute()
#    assert filecmp.cmp(gen_autoinst, verified_result)
    testAutoinstGen_dir.rmtree()


def testRHEL5Kickstart():
    template_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/kickstart.tmpl'
    verified_result_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/gen_rhel5_ks2.cfg'

    testAutoinstGen_dir = path(mkdtemp(prefix='TestKickstartGen'))
    gen_autoinst = testAutoinstGen_dir / 'myks.cfg'

    # fetch the verified result.
    protocol = urlparse.urlparse(verified_result_uri)[0]
    fc = FetchCommand(uri=verified_result_uri, fetchdir=False,
                      destdir=testAutoinstGen_dir, overwrite=True)
    fc.execute()

    verified_result = testAutoinstGen_dir / 'gen_rhel5_ks2.cfg'

    networkprofile = {'interfaces': {'eth0': {'configure': True,
                                              'use_dhcp': False,
                                              'ip_address': '192.168.1.99',
                                              'netmask': '255.255.255.0',
                                              'active_on_boot': False},
                                     'eth1': {'configure': True,
                                              'use_dhcp': True,
                                              'active_on_boot': True}},
                      'gw_dns_use_dhcp': False,
                      'fqhn_use_dhcp': False}
    packages = ['@ admin-tools',
                '@ system-tools',
                '@ text-internet',
                '@ server-cfg',
                '@ development-tools',
                'lvm2',
                'kernel-devel',
                'e2fsprogs',
                'kernel']

    ic = GenerateAutoInstallScriptCommand(os={'name': 'rhel', 'version': '5'},
                                          diskprofile=None,
                                          networkprofile=networkprofile,
                                          installsrc='http://10.10.10.171:8080/centos4/',
                                          rootpw='$1$R0u07JQv$LDKTlairsxqxnAxC5Yfbe/',
                                          tz='Asia/Singapore',
                                          tz_utc=False,
                                          lang='en_US',
                                          keyboard='us',
                                          packageprofile=packages,
                                          diskorder=[],
                                          instnum='',
                                          template_uri=template_uri,
                                          outfile=gen_autoinst)

    ic.execute()
#    assert filecmp.cmp(gen_autoinst, verified_result)
    testAutoinstGen_dir.rmtree()


def testRHEL5KickstartWithPartitionRules():
    template_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/kickstart_with_part.cfg'
    verified_result_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/gen_rhel5_ks_with_part.cfg'

    testAutoinstGen_dir = path(mkdtemp(prefix='TestKickstartGen'))
    gen_autoinst = testAutoinstGen_dir / 'myks.cfg'

    # fetch the verified result.
    protocol = urlparse.urlparse(verified_result_uri)[0]
    fc = FetchCommand(uri=verified_result_uri, fetchdir=False,
                      destdir=testAutoinstGen_dir, overwrite=True)
    fc.execute()

    verified_result = testAutoinstGen_dir / 'gen_rhel5_ks2.cfg'

    networkprofile = {'interfaces': {'eth0': {'configure': True,
                                              'use_dhcp': False,
                                              'ip_address': '192.168.1.99',
                                              'netmask': '255.255.255.0',
                                              'active_on_boot': False},
                                     'eth1': {'configure': True,
                                              'use_dhcp': True,
                                              'active_on_boot': True}},
                      'gw_dns_use_dhcp': False,
                      'fqhn_use_dhcp': False}
    packages = ['@ admin-tools',
                '@ system-tools',
                '@ text-internet',
                '@ server-cfg',
                '@ development-tools',
                'lvm2',
                'kernel-devel',
                'e2fsprogs',
                'kernel']

    partitionrules = [Struct(mntpnt='/boot',fstype='ext3',size=100,options=None),
                      Struct(mntpnt=None,fstype='linux-swap',size=2000,options=None),
                      Struct(mntpnt='/',fstype='ext2',size=12000,options=None),
                      Struct(mntpnt='fake',fstype=None,size=100,options='fill')]

    ic = GenerateAutoInstallScriptCommand(os={'name': 'rhel', 'version': '5'},
                                          diskprofile=None,
                                          partitionrules=partitionrules,
                                          networkprofile=networkprofile,
                                          installsrc='http://10.10.10.171:8080/centos4/',
                                          rootpw='$1$R0u07JQv$LDKTlairsxqxnAxC5Yfbe/',
                                          tz='Asia/Singapore',
                                          tz_utc=False,
                                          lang='en_US',
                                          keyboard='us',
                                          packageprofile=packages,
                                          diskorder=[],
                                          instnum='',
                                          template_uri=template_uri,
                                          outfile=gen_autoinst)

    ic.execute()
#    assert filecmp.cmp(gen_autoinst, verified_result)
    testAutoinstGen_dir.rmtree()
