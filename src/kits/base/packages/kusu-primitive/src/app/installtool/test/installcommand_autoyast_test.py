#!/usr/bin/env python
# $Id: installcommand_autoyast_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
""" Tests for generating Autoyast configuration files."""
import filecmp
import urlparse
from path import path
from tempfile import mkdtemp
from primitive.support.type import Struct
from primitive.fetchtool.commands import FetchCommand
from primitive.system.hardware.partitiontool import DiskProfile
from primitive.installtool.commands import GenerateAutoInstallScriptCommand

def testAutoyast():
    template_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/minimal-autoinst.tmpl'
    verified_result_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/gen_autoinst.xml'

    testAutoinstGen_dir = path(mkdtemp(prefix='TestAutoinstGen'))
    gen_autoinst = testAutoinstGen_dir / 'myautoinst.xml'

    # fetch the verified result.
    protocol = urlparse.urlparse(verified_result_uri)[0]
    fc = FetchCommand(uri=verified_result_uri, fetchdir=False,
                      destdir=testAutoinstGen_dir, overwrite=True)
    fc.execute()

    verified_result = testAutoinstGen_dir / 'gen_autoinst.xml'

    networkprofile = {'default_gw': '192.168.1.1',
                      'fqhn_host': 'master',
                      'fqhn_domain': 'kusu',
                      'interfaces': {'eth0': {'configure': True,
                                              'use_dhcp': False,
                                              'ip_address': '192.168.1.99',
                                              'netmask': '255.255.255.0',
                                              'active_on_boot': False,
                                              'hwaddr': '00:11:22:33:44:55'},
                                     'eth1': {'configure': True,
                                              'use_dhcp': True,
                                              'active_on_boot': True,
                                              'hwaddr': '11:22:33:44:55:66'}}}

    packages = ['giflib',
                'libnl',
                'fontconfig',
                'perl-Digest-MD4',
                'yast2-trans-en_US',
                'perl-Compress-Zlib',
                'limal-nfs-server',
                'perl-Date-Calc',
                'libicu',
                'boost',
                'dbus-1-mono',
                'mono-web',
                'dbus-1-python',
                'libzypp-zmd-backend',
                'zypper',
                'libxml2-python',
                'mpt-firmware',
                'perl-Bootloader',
                'python',
                'tcl',
                'perl-URI',
                'update-alternatives',
                'limal-nfs-server-perl',
                'libgdiplus',
                'perl-X500-DN',
                'glib',
                'perl-Config-IniFiles',
                'pciutils-ids',
                'mono-winforms',
                'perl-Carp-Clan',
                'perl-Config-Crontab',
                'perl-Digest-SHA1',
                'perl-Parse-RecDescent',
                'perl-gettext',
                'perl-XML-Parser',
                'perl-Crypt-SmbHash',
                'perl-Bit-Vector',
                'perl-XML-Writer',
                'xorg-x11-libs']
 
    ic = GenerateAutoInstallScriptCommand(os={'name': 'sles', 'version': '10'},
                                          diskprofile=None,
                                          networkprofile=networkprofile,
                                          installsrc='http://10.10.11.218',
                                          rootpw='system',
                                          tz='Asia/Singapore',
                                          tz_utc=False,
                                          lang='en_US',
                                          keyboard='english-us',
                                          packageprofile=packages,
                                          diskorder=[],
                                          template_uri=template_uri,
                                          outfile=gen_autoinst)

    ic.execute()
# COMMENTED OUT BECAUSE BLOWFISH WILL RETURN A DIFFERENT PASSWORD STRING
#   assert filecmp.cmp(gen_autoinst, verified_result)
    testAutoinstGen_dir.rmtree()


def testAutoyastWithPartitioning():
    template_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/autoinst.tmpl'
    verified_result_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/gen_autoinst_partitioning.xml'

    testAutoinstGen_dir = path(mkdtemp(prefix='TestAutoinstGenWithPartitioning'))
    gen_autoinst = testAutoinstGen_dir / 'myautoinst.xml'

    # fetch the verified result.
    protocol = urlparse.urlparse(verified_result_uri)[0]
    fc = FetchCommand(uri=verified_result_uri, fetchdir=False,
                      destdir=testAutoinstGen_dir, overwrite=True)
    fc.execute()

    verified_result = testAutoinstGen_dir / 'gen_autoinst_partitioning.xml'

    networkprofile = {'default_gw': '192.168.1.1',
                      'fqhn_host': 'master',
                      'fqhn_domain': 'kusu',
                      'interfaces': {'eth0': {'configure': True,
                                              'use_dhcp': False,
                                              'ip_address': '192.168.1.99',
                                              'netmask': '255.255.255.0',
                                              'active_on_boot': False,
                                              'hwaddr': '00:11:22:33:44:55'},
                                     'eth1': {'configure': True,
                                              'use_dhcp': True,
                                              'active_on_boot': True,
                                              'hwaddr': '11:22:33:44:55:66'}}}

    packages = ['giflib',
                'libnl',
                'fontconfig',
                'perl-Digest-MD4',
                'yast2-trans-en_US',
                'perl-Compress-Zlib',
                'limal-nfs-server',
                'perl-Date-Calc',
                'libicu',
                'boost',
                'dbus-1-mono',
                'mono-web',
                'dbus-1-python',
                'libzypp-zmd-backend',
                'zypper',
                'libxml2-python',
                'mpt-firmware',
                'perl-Bootloader',
                'python',
                'tcl',
                'perl-URI',
                'update-alternatives',
                'limal-nfs-server-perl',
                'libgdiplus',
                'perl-X500-DN',
                'glib',
                'perl-Config-IniFiles',
                'pciutils-ids',
                'mono-winforms',
                'perl-Carp-Clan',
                'perl-Config-Crontab',
                'perl-Digest-SHA1',
                'perl-Parse-RecDescent',
                'perl-gettext',
                'perl-XML-Parser',
                'perl-Crypt-SmbHash',
                'perl-Bit-Vector',
                'perl-XML-Writer',
                'xorg-x11-libs']
 
    # construct a mock DiskProfile object.
    dp = Struct(disk_dict=Struct())
    dp.disk_dict.sda = Struct(path='/dev/sda')
    dp.disk_dict.sda.partition_dict = Struct({1:Struct(pedPartition=Struct()),
                                              2:Struct(pedPartition=Struct()),
                                              3:Struct(pedPartition=Struct())})
    # boot partition
    dp.disk_dict.sda.partition_dict[1].on_disk = False
    dp.disk_dict.sda.partition_dict[1].fs_type = 'ext2'
    dp.disk_dict.sda.partition_dict[1].do_not_format = False
    dp.disk_dict.sda.partition_dict[1].mountpoint = '/boot'
    dp.disk_dict.sda.partition_dict[1].pedPartition.native_type = 130
    dp.disk_dict.sda.partition_dict[1].num = 1
    dp.disk_dict.sda.partition_dict[1].size = 100000000
    # swap partition
    dp.disk_dict.sda.partition_dict[2].on_disk = False
    dp.disk_dict.sda.partition_dict[2].fs_type = 'linux-swap'
    dp.disk_dict.sda.partition_dict[2].do_not_format = False
    dp.disk_dict.sda.partition_dict[2].mountpoint = None
    dp.disk_dict.sda.partition_dict[2].pedPartition.native_type = 131
    dp.disk_dict.sda.partition_dict[2].num = 2
    dp.disk_dict.sda.partition_dict[2].size = 2000000000
    # root partition
    dp.disk_dict.sda.partition_dict[3].on_disk = False
    dp.disk_dict.sda.partition_dict[3].fs_type = 'ext3'
    dp.disk_dict.sda.partition_dict[3].do_not_format = False
    dp.disk_dict.sda.partition_dict[3].mountpoint = '/'
    dp.disk_dict.sda.partition_dict[3].pedPartition.native_type = 130
    dp.disk_dict.sda.partition_dict[3].num = 3
    dp.disk_dict.sda.partition_dict[3].size = 20000000000

    ic = GenerateAutoInstallScriptCommand(os={'name': 'sles', 'version': '10'},
                                          diskprofile=dp,
                                          networkprofile=networkprofile,
                                          installsrc='http://10.10.11.218',
                                          rootpw='system',
                                          tz='Asia/Singapore',
                                          tz_utc=False,
                                          lang='en_US',
                                          keyboard='english-us',
                                          packageprofile=packages,
                                          diskorder=[],
                                          template_uri=template_uri,
                                          outfile=gen_autoinst)

    ic.execute()
    # Note that the actual hashed password is not included in the test template
    # as well as the verified result file. This is because hashing of passwords
    # uses a salt value that is generated randomly at runtime and the resulting
    # hashed password will be different every time.
    assert filecmp.cmp(gen_autoinst, verified_result)
    testAutoinstGen_dir.rmtree()

def testAutoyastWithPartitioningLVM():
    template_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/autoinstLVM.tmpl'
    verified_result_uri = 'http://www.osgdc.org/pub/build/tests/modules/primitive/installtool/gen_autoinstLVM.xml'

    testAutoinstGen_dir = path(mkdtemp(prefix='TestAutoinstGenWithPartitioning'))
    gen_autoinst = testAutoinstGen_dir / 'myautoinst.xml'

    # fetch the verified result.
    protocol = urlparse.urlparse(verified_result_uri)[0]
    fc = FetchCommand(uri=verified_result_uri, fetchdir=False,
                      destdir=testAutoinstGen_dir, overwrite=True)
    fc.execute()

    verified_result = testAutoinstGen_dir / 'gen_autoinstLVM.xml'

    networkprofile = {'default_gw': '192.168.1.1',
                      'fqhn_host': 'master',
                      'fqhn_domain': 'kusu',
                      'interfaces': {'eth0': {'configure': True,
                                              'use_dhcp': False,
                                              'ip_address': '192.168.1.99',
                                              'netmask': '255.255.255.0',
                                              'active_on_boot': False,
                                              'hwaddr': '00:11:22:33:44:55'},
                                     'eth1': {'configure': True,
                                              'use_dhcp': True,
                                              'active_on_boot': True,
                                              'hwaddr': '11:22:33:44:55:66'}}}

    packages = ['giflib',
                'libnl',
                'fontconfig',
                'perl-Digest-MD4',
                'yast2-trans-en_US',
                'perl-Compress-Zlib',
                'limal-nfs-server',
                'perl-Date-Calc',
                'libicu',
                'boost',
                'dbus-1-mono',
                'mono-web',
                'dbus-1-python',
                'libzypp-zmd-backend',
                'zypper',
                'libxml2-python',
                'mpt-firmware',
                'perl-Bootloader',
                'python',
                'tcl',
                'perl-URI',
                'update-alternatives',
                'limal-nfs-server-perl',
                'libgdiplus',
                'perl-X500-DN',
                'glib',
                'perl-Config-IniFiles',
                'pciutils-ids',
                'mono-winforms',
                'perl-Carp-Clan',
                'perl-Config-Crontab',
                'perl-Digest-SHA1',
                'perl-Parse-RecDescent',
                'perl-gettext',
                'perl-XML-Parser',
                'perl-Crypt-SmbHash',
                'perl-Bit-Vector',
                'perl-XML-Writer',
                'xorg-x11-libs']
 
    dp = createMockDiskProfile()
    ic = GenerateAutoInstallScriptCommand(os={'name': 'sles', 'version': '10'},
                                          diskprofile=dp,
                                          networkprofile=networkprofile,
                                          installsrc='http://10.10.11.218',
                                          rootpw='system',
                                          tz='Asia/Singapore',
                                          tz_utc=False,
                                          lang='en_US',
                                          keyboard='english-us',
                                          packageprofile=packages,
                                          diskorder=[],
                                          template_uri=template_uri,
                                          outfile=gen_autoinst)

    ic.execute()
    # Note that the actual hashed password is not included in the test template
    # as well as the verified result file. This is because hashing of passwords
    # uses a salt value that is generated randomly at runtime and the resulting
    # hashed password will be different every time.
    assert filecmp.cmp(gen_autoinst, verified_result)
    testAutoinstGen_dir.rmtree()

def createMockDiskProfile():
    # construct a mock DiskProfile object.
    dp = Struct(disk_dict=Struct(), pv_dict=Struct(), lvg_dict=Struct())
    dp.disk_dict.sda = Struct(path='/dev/sda', profile=dp)
    dp.disk_dict.sda.partition_dict = Struct({1:Struct(pedPartition=Struct()),
                                              2:Struct(pedPartition=Struct()),
                                              3:Struct(pedPartition=Struct())})
    # boot partition
    dp.disk_dict.sda.partition_dict[1].on_disk = False
    dp.disk_dict.sda.partition_dict[1].path = '/dev/sda1'
    dp.disk_dict.sda.partition_dict[1].disk = dp.disk_dict.sda
    dp.disk_dict.sda.partition_dict[1].fs_type = 'ext2'
    dp.disk_dict.sda.partition_dict[1].type = 'primary'
    dp.disk_dict.sda.partition_dict[1].do_not_format = False
    dp.disk_dict.sda.partition_dict[1].mountpoint = '/boot'
    dp.disk_dict.sda.partition_dict[1].pedPartition.native_type = 130
    dp.disk_dict.sda.partition_dict[1].num = 1
    dp.disk_dict.sda.partition_dict[1].size = 100000000
    # swap partition
    dp.disk_dict.sda.partition_dict[2].on_disk = False
    dp.disk_dict.sda.partition_dict[2].path = '/dev/sda2'
    dp.disk_dict.sda.partition_dict[2].disk = dp.disk_dict.sda
    dp.disk_dict.sda.partition_dict[2].fs_type = 'linux-swap'
    dp.disk_dict.sda.partition_dict[2].type = 'primary'
    dp.disk_dict.sda.partition_dict[2].do_not_format = False
    dp.disk_dict.sda.partition_dict[2].mountpoint = None
    dp.disk_dict.sda.partition_dict[2].pedPartition.native_type = 131
    dp.disk_dict.sda.partition_dict[2].num = 2
    dp.disk_dict.sda.partition_dict[2].size = 2000000000
    # root partition
    dp.disk_dict.sda.partition_dict[3].on_disk = False
    dp.disk_dict.sda.partition_dict[3].path = '/dev/sda3'
    dp.disk_dict.sda.partition_dict[3].disk = dp.disk_dict.sda
    dp.disk_dict.sda.partition_dict[3].type = 'primary'
    dp.disk_dict.sda.partition_dict[3].fs_type = 'physical volume'
    dp.disk_dict.sda.partition_dict[3].do_not_format = False
    dp.disk_dict.sda.partition_dict[3].mountpoint = None
    dp.disk_dict.sda.partition_dict[3].pedPartition.native_type = 142
    dp.disk_dict.sda.partition_dict[3].num = 3
    dp.disk_dict.sda.partition_dict[3].size = 20000000000

    pv = Struct(partition=dp.disk_dict.sda.partition_dict[3])
    dp.pv_dict = Struct({'/dev/sda3':pv})
    
    vg = Struct()
    vg.name = 'KusuVolGroup00'
    vg.pv_dict = Struct(sda3=pv)
    vg.extent_size_humanreadable = '32M'
    pv.group = vg
    vg.lv_dict = Struct(VAR=Struct(), ROOT=Struct(), HOME=Struct())

    vg.lv_dict.VAR.size = 1000000
    vg.lv_dict.VAR.fs_type = 'ext3'
    vg.lv_dict.VAR.name = 'VAR'
    vg.lv_dict.VAR.mountpoint = '/var'

    vg.lv_dict.ROOT.size = 1000000
    vg.lv_dict.ROOT.fs_type = 'ext3'
    vg.lv_dict.ROOT.name = 'ROOT'
    vg.lv_dict.ROOT.mountpoint = '/'

    vg.lv_dict.HOME.size = 1000000
    vg.lv_dict.HOME.fs_type = 'ext3'
    vg.lv_dict.HOME.name = 'HOME'
    vg.lv_dict.HOME.mountpoint = '/home'

    dp.lvg_dict=Struct(KusuVolGroup00=vg)
    return dp
