#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
# This testsuite exercises the NodeInstaller class. Requires ksvalidator from the pykickstart
# package for the full test run.
#

from kusu.nodeinstaller import NodeInstaller, KickstartFromNIIProfile, adaptNIIPartition, translatePartitionOptions
from cStringIO import StringIO
from nose import SkipTest
import subprocess
import tempfile
from path import path
import os
from kusu.partitiontool import DiskProfile, Disk, Partition
from kusu.installer.defaults import Disk as SchemaDisk
from kusu.installer.defaults import Partition as SchemaPartition
from kusu.installer.defaults import LVMGroup as SchemaLVMGroup
from kusu.installer.defaults import LVMLogicalVolume as SchemaLVMLogicalVolume
from kusu.installer.defaults import DiskCollection, LVMCollection, PartitionSchema
from kusu.util.structure import Struct
from socket import gethostname

class FakePartition(object):
    def __init__(self):
        self.path='/dev/asd'

class TestDefaultPreserve:
    def testRules(self):
        raise SkipTest

class TestNIIPartition:
    """
    Test for standard partition schema:
        1. /boot 100M  ext3 no-preserve
        2. /swap 1000M swap no-preserve
        3. /     6000M ext3 no-preserve
    """

    def setUp(self):
        if not gethostname() == 'dizzy.int.osgdc.org':
            raise SkipTest, 'Test only runs on dizzy.int.osgdc.org(Internal machine)'
        self.tmpdir = path(tempfile.mkdtemp(dir='/tmp'))
        niidata = """\
<?xml version="1.0"?>
<nii>
<debug>
Dump NII: 1 
State:  
Dump CFM: 0 
Node: node0000 
</debug>
<nodeinfo name="node0000" installers="10.1.10.1" repo="/mirror/fc6/i386/os" ostype="fedora" installtype="package" nodegrpid="2">
    <nicinfo device="eth0" ip="10.1.10.10" subnet="255.255.255.0" network="10.1.10.0" suffix="" gateway="10.1.10.1" dhcp="0" options="" boot="1"/>
    <partition device="1" mntpnt="/boot" fstype="ext3" size="100" options="" partition="1" preserve="0"/>
    <partition device="1" mntpnt="" fstype="linux-swap" size="1000" options="" partition="2" preserve="0"/>
    <partition device="1" mntpnt="/" fstype="ext3" size="6000" options="fill" partition="3" preserve="0"/>
    <component>component-base-node</component>
    <appglobals name="ClusterName" value="BadBoy"/>
    <appglobals name="DNSZone" value="myzone.company.com"/>
    <appglobals name="DNSForwarders" value="172.16.1.5,172.16.1.8"/>
    <appglobals name="DNSSearch" value="myzone.company.com company.com corp.company.com"/>
    <appglobals name="NASServer" value="172.25.243.2"/>
    <appglobals name="Timezone_zone" value="Asia/Singapore"/>
    <appglobals name="Timezone_utc" value="1"/>
    <appglobals name="NISDomain" value="engineering"/>
    <appglobals name="NISServers" value="172.25.243.4,172.25.243.14"/>
    <appglobals name="CFMSecret" value="GF5SEVTHJ589TNT45NTEYST78GYBG5GVYGT84NTV578TEB46"/>
    <appglobals name="InstallerServeDNS" value="True"/>
    <appglobals name="InstallerServeNIS" value="True"/>
    <appglobals name="InstallerServeNFS" value="True"/>
    <appglobals name="InstallerServeNTP" value="True"/>
    <appglobals name="PrimaryInstaller" value="installer0"/>
    <appglobals name="DHCPLeaseTime" value="2400"/>
    <appglobals name="InstallerServeSMTP" value="False"/>
    <appglobals name="Language" value="en_US.UTF-8"/>
    <appglobals name="Keyboard" value="us"/>        
    <appglobals name="RootPassword" value="badrootpassword"/>    
    <appglobals name="SMTPServer" value="mailserver.myzone.company.com"/>
    <appglobals name="CFMBaseDir" value="/opt/kusu/cfm"/>
</nodeinfo>
</nii>
"""
       # make niisource more file-like
        self.niisource = StringIO(niidata)
        invalidniidata = """\
        <nii>
        <noodleinfo>
        evil nii data
        </noodleinfo>
        </nii>
        """
        self.invalidnii = StringIO(invalidniidata)

    def tearDown(self):
        self.niisource = None
        if self.tmpdir.exists(): self.tmpdir.rmtree()


    def testKickstartFromNIIProfile(self):
        """ Test to validate ksprofile.  
        """

        ni = NodeInstaller(self.niisource)
        ni.parseNII()
        ksprofile = KickstartFromNIIProfile()

        # validate disk schema
        dp = DiskProfile(fresh=True)
        adaptedSchema = adaptNIIPartition(ni.partitions, dp)[0]
        expected = self.partitionSchema()
        assert expected == adaptedSchema, """
expected disk_dict:\n%s\nadapted disk_dict:\n%s\n
expected vg_dict:\n%s\nadapted vg_dict:\n%s\n
expected pres_fs:\n%s\nadapted pres_fs:\n%s\n
expected mntpnt: %s, adapted mntpnt: %s
""" % \
    (str(expected.disk_dict), str(adaptedSchema['disk_dict']),
     str(expected.vg_dict), str(adaptedSchema['vg_dict']),
     str(expected.preserve_fs), str(adaptedSchema['preserve_fs']),
     expected.preserve_mntpnt, adaptedSchema['preserve_mntpnt'])


    def testTranslatePartitionOptions(self):
        """ Test to validate translatePartitionOptions. """

        options0 = ''
        options1 = 'fill;label=My Volume'
        options2 = 'fill'
        options3 = 'vg;extent=32M'
        options4 = 'pv;vg=VolGroup00'
        options5 = 'lv;vg=VolGroup00'

        # blank options
        assert translatePartitionOptions(options0,'fill')[0] is False

        # check for fill is true
        assert translatePartitionOptions(options1,'fill')[0] is True
        assert translatePartitionOptions(options2,'fill')[0] is True

        # check for label
        assert translatePartitionOptions(options1,'label')[0] is True
        assert translatePartitionOptions(options1,'label')[1] == 'My Volume'
        assert translatePartitionOptions(options2,'label')[0] is False

        # check for vg
        assert translatePartitionOptions(options3,'extent')[0] is True
        assert translatePartitionOptions(options3,'extent')[1] == '32M'        
        assert translatePartitionOptions(options1,'extent')[0] is False

        # check for pv
        assert translatePartitionOptions(options4,'pv')[0] is True
        assert translatePartitionOptions(options4,'pv')[1] == 'VolGroup00'
        assert translatePartitionOptions(options1,'pv')[0] is False

        # check for lv
        assert translatePartitionOptions(options5,'lv')[0] is True
        assert translatePartitionOptions(options5,'lv')[1] == 'VolGroup00'
        assert translatePartitionOptions(options1,'lv')[0] is False      


    def partitionSchema(self):
        d1 = SchemaDisk()

        d1p1 = SchemaPartition()
        d1p1.size_MB = 100
        d1p1.fs = 'ext3'
        d1p1.mountpoint = '/boot'
        d1p1.fill = False
        d1.addPartition(d1p1)

        d1p2 = SchemaPartition()
        d1p2.size_MB = 1000
        d1p2.fs = 'linux-swap'
        d1p2.fill = False
        d1.addPartition(d1p2)

        d1p3 = SchemaPartition()
        d1p3.size_MB = 6000
        d1p3.fs = 'ext3'
        d1p3.fill = True
        d1.addPartition(d1p3)

        disks = DiskCollection()
        disks.addDisk(d1)

        preserve_types = Partition.native_type_dict.values()
        preserve_fs = DiskProfile.fsType_dict.keys()
        preserve_mntpnt = []
        return PartitionSchema(disks=disks, preserve_types=preserve_types,
                           preserve_fs=preserve_fs, preserve_mntpnt=preserve_mntpnt)



class TestNIIPartitionPreserve(TestNIIPartition):
    """
    Test for standard partition schema:
        1. /boot 100M  ext3 no-preserve
        2. /swap 1000M swap no-preserve
        3. /     6000M ext3 preserve
    """

    def setUp(self):
        if not gethostname() == 'dizzy.int.osgdc.org':
            raise SkipTest, 'Test only runs on dizzy.int.osgdc.org(Internal machine)'
        self.tmpdir = path(tempfile.mkdtemp(dir='/tmp'))
        niidata = """\
<?xml version="1.0"?>
<nii>
<debug>
Dump NII: 1 
State:  
Dump CFM: 0 
Node: node0000 
</debug>
<nodeinfo name="node0000" installers="10.1.10.1" repo="/mirror/fc6/i386/os" ostype="fedora" installtype="package" nodegrpid="2">
    <nicinfo device="eth0" ip="10.1.10.10" subnet="255.255.255.0" network="10.1.10.0" suffix="" gateway="10.1.10.1" dhcp="0" options="" boot="1"/>
    <partition device="1" mntpnt="/boot" fstype="ext3" size="100" options="" partition="1" preserve="0"/>
    <partition device="1" mntpnt="" fstype="linux-swap" size="1000" options="" partition="2" preserve="0"/>
    <partition device="1" mntpnt="/" fstype="ext3" size="6000" options="fill" partition="3" preserve="1"/>
    <component>component-base-node</component>
    <appglobals name="ClusterName" value="BadBoy"/>
    <appglobals name="DNSZone" value="myzone.company.com"/>
    <appglobals name="DNSForwarders" value="172.16.1.5,172.16.1.8"/>
    <appglobals name="DNSSearch" value="myzone.company.com company.com corp.company.com"/>
    <appglobals name="NASServer" value="172.25.243.2"/>
    <appglobals name="Timezone_zone" value="Asia/Singapore"/>
    <appglobals name="Timezone_utc" value="1"/>
    <appglobals name="NISDomain" value="engineering"/>
    <appglobals name="NISServers" value="172.25.243.4,172.25.243.14"/>
    <appglobals name="CFMSecret" value="GF5SEVTHJ589TNT45NTEYST78GYBG5GVYGT84NTV578TEB46"/>
    <appglobals name="InstallerServeDNS" value="True"/>
    <appglobals name="InstallerServeNIS" value="True"/>
    <appglobals name="InstallerServeNFS" value="True"/>
    <appglobals name="InstallerServeNTP" value="True"/>
    <appglobals name="PrimaryInstaller" value="installer0"/>
    <appglobals name="DHCPLeaseTime" value="2400"/>
    <appglobals name="InstallerServeSMTP" value="False"/>
    <appglobals name="Language" value="en_US.UTF-8"/>
    <appglobals name="Keyboard" value="us"/>        
    <appglobals name="RootPassword" value="badrootpassword"/>    
    <appglobals name="SMTPServer" value="mailserver.myzone.company.com"/>
    <appglobals name="CFMBaseDir" value="/opt/kusu/cfm"/>
</nodeinfo>
</nii>
"""
        # make niisource more file-like
        self.niisource = StringIO(niidata)
        invalidniidata = """\
        <nii>
        <noodleinfo>
        evil nii data
        </noodleinfo>
        </nii>
        """
        self.invalidnii = StringIO(invalidniidata)

    def partitionSchema(self):
        d1 = SchemaDisk()

        d1p1 = SchemaPartition()
        d1p1.size_MB = 100
        d1p1.fs = 'ext3'
        d1p1.mountpoint = '/boot'
        d1p1.fill = False
        d1.addPartition(d1p1)

        d1p2 = SchemaPartition()
        d1p2.size_MB = 1000
        d1p2.fs = 'linux-swap'
        d1p2.fill = False
        d1.addPartition(d1p2)

        d1p3 = SchemaPartition()
        d1p3.size_MB = 6000
        d1p3.fs = 'ext3'
        d1p3.mountpoint = '/'
        d1p3.fill = True
        d1.addPartition(d1p3)

        disks = DiskCollection()
        disks.addDisk(d1)

        preserve_types = Partition.native_type_dict.values()
        preserve_fs = DiskProfile.fsType_dict.keys()
        preserve_mntpnt = []
        return PartitionSchema(disks=disks, preserve_types=preserve_types,
                           preserve_fs=preserve_fs, preserve_mntpnt=preserve_mntpnt)


class TestNIIPartitionLVM(TestNIIPartition):
    """
    Test for standard partition schema:
        1. /boot 100M  ext3            preserve
        2. /swap 1000M swap            no-preserve
        3.       6000M physical volume fill,pv,vg=VolGroup00
        3. /     2000M ext3            preserve Logical Volume
        4. /data 4000M ext3            preserve Logical Volume
    """

    def setUp(self):
        if not gethostname() == 'dizzy.int.osgdc.org':
            raise SkipTest, 'Test only runs on dizzy.int.osgdc.org(Internal machine)'
        self.tmpdir = path(tempfile.mkdtemp(dir='/tmp'))
        niidata = """\
<?xml version="1.0"?>
<nii>
<debug>
Dump NII: 1 
State:  
Dump CFM: 0 
Node: node0000 
</debug>
<nodeinfo name="node0000" installers="10.1.10.1" repo="/mirror/fc6/i386/os" ostype="fedora" installtype="package" nodegrpid="2">
    <nicinfo device="eth0" ip="10.1.10.10" subnet="255.255.255.0" network="10.1.10.0" suffix="" gateway="10.1.10.1" dhcp="0" options="" boot="1"/>
    <partition device="1" mntpnt="/boot" fstype="ext3" size="100" options="" partition="1" preserve="0"/>
    <partition device="1" mntpnt="" fstype="linux-swap" size="1000" options="" partition="2" preserve="0"/>
    <partition device="N" mntpnt="" fstype="physical volume" size="6000" options="fill;pv;vg=VolGroup00" partition="0" preserve="0"/>
    <partition device="VolGroup00" mntpnt="" fstype="" size="0" options="vg;extent=32M" partition="" preserve="0"/>
    <partition device="ROOT" mntpnt="/" fstype="ext3" size="2000" options="lv;vg=VolGroup00" preserve="0"/>
    <partition device="DATA" mntpnt="/data" fstype="ext3" size="6000" options="lv;vg=VolGroup00;fill" preserve="0"/>
    <component>component-base-node</component>
    <appglobals name="ClusterName" value="BadBoy"/>
    <appglobals name="DNSZone" value="myzone.company.com"/>
    <appglobals name="DNSForwarders" value="172.16.1.5,172.16.1.8"/>
    <appglobals name="DNSSearch" value="myzone.company.com company.com corp.company.com"/>
    <appglobals name="NASServer" value="172.25.243.2"/>
    <appglobals name="Timezone_zone" value="Asia/Singapore"/>
    <appglobals name="Timezone_utc" value="1"/>
    <appglobals name="NISDomain" value="engineering"/>
    <appglobals name="NISServers" value="172.25.243.4,172.25.243.14"/>
    <appglobals name="CFMSecret" value="GF5SEVTHJ589TNT45NTEYST78GYBG5GVYGT84NTV578TEB46"/>
    <appglobals name="InstallerServeDNS" value="True"/>
    <appglobals name="InstallerServeNIS" value="True"/>
    <appglobals name="InstallerServeNFS" value="True"/>
    <appglobals name="InstallerServeNTP" value="True"/>
    <appglobals name="PrimaryInstaller" value="installer0"/>
    <appglobals name="DHCPLeaseTime" value="2400"/>
    <appglobals name="InstallerServeSMTP" value="False"/>
    <appglobals name="Language" value="en_US.UTF-8"/>
    <appglobals name="Keyboard" value="us"/>        
    <appglobals name="RootPassword" value="badrootpassword"/>    
    <appglobals name="SMTPServer" value="mailserver.myzone.company.com"/>
    <appglobals name="CFMBaseDir" value="/opt/kusu/cfm"/>
</nodeinfo>
</nii>
"""
        # make niisource more file-like
        self.niisource = StringIO(niidata)
        invalidniidata = """\
        <nii>
        <noodleinfo>
        evil nii data
        </noodleinfo>
        </nii>
        """
        self.invalidnii = StringIO(invalidniidata)

    def partitionSchema(self):
        d1 = SchemaDisk()

        d1p1 = SchemaPartition()
        d1p1.size_MB = 100
        d1p1.fs = 'ext3'
        d1p1.mountpoint = '/boot'
        d1p1.fill = False
        d1.addPartition(d1p1)

        d1p2 = SchemaPartition()
        d1p2.size_MB = 1000
        d1p2.fs = 'linux-swap'
        d1p2.fill = False
        d1.addPartition(d1p2)

        d1p3 = SchemaPartition()
        d1p3.size_MB = 6000
        d1p3.fs = 'physical volume'
        d1p3.mountpoint = None
        d1p3.fill = True
        d1.addPartition(d1p3)

        disks = DiskCollection()
        disks.addDisk(d1)

        volgroup00 = SchemaLVMGroup()
        volgroup00.name = 'VolGroup00'
        volgroup00.extent_size = '32M'
        volgroup00.pv_span = True
        volgroup00.addPV(disk='N', partition='N')

        root = SchemaLVMLogicalVolume()
        root.name = 'ROOT'
        root.size_MB = 2000
        root.fs = 'ext3'
        root.mountpoint = '/'
        root.fill = False
        volgroup00.addLV(root)

        depot = SchemaLVMLogicalVolume()
        depot.name = 'DATA'
        depot.size_MB = 4000
        depot.fs = 'ext3'
        depot.mountpoint = '/data'
        depot.fill = True
        volgroup00.addLV(depot)

        lvm = LVMCollection()
        lvm.addVG(volgroup00)

        preserve_types = Partition.native_type_dict.values()
        preserve_fs = DiskProfile.fsType_dict.keys()
        preserve_mntpnt = []
        return PartitionSchema(disks=disks, lvm=lvm, preserve_types=preserve_types,
                           preserve_fs=preserve_fs, preserve_mntpnt=preserve_mntpnt)
