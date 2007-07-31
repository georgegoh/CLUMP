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
from kusu.installer.defaults import DiskCollection, PartitionSchema


def partition1():
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
    preserve_fs = DiskProfile.fsType_dict.values()
    preserve_mntpnt = []
    return PartitionSchema(disks=disks, preserve_types=preserve_types,
                           preserve_fs=preserve_fs, preserve_mntpnt=preserve_mntpnt)


class TestNIIPartition:
    """
    Test for standard partition schema:
        1. /boot 100M  ext3 no-preserve
        2. /swap 1000M swap no-preserve
        3. /     6000M ext3 no-preserve
    """
    def setUp(self):
        
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
    <partition device="1" mntpnt="/boot" fstype="ext3" size="100" options="" partition="1" preserve="n"/>
    <partition device="1" mntpnt="" fstype="linux-swap" size="1000" options="" partition="2" preserve="n"/>
    <partition device="1" mntpnt="/" fstype="ext3" size="6000" options="fill" partition="3" preserve="n"/>
/nodeinfo>
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
        
        # additional partitioning profiles from nii
        self.niipartition1 = {
                # /boot - 100M, ext3, disk 1 part 1
                0: {'preserve': u'n', 'fstype': u'ext3', 'device': u'1', 'mntpnt': u'/boot', 'options': u'', 'size': u'100', 'partition':'1'},
                # swap - 1000M, linux-swap, disk 1 part 2
                1: {'preserve': u'n', 'fstype': u'linux-swap', 'device': u'1', 'mntpnt': u'', 'options': u'', 'size': u'1000', 'partition':'2'},
                # / - 6000M(fill), ext3, disk 1 part 3
                2: {'preserve': u'n', 'fstype': u'ext3', 'device': u'1', 'mntpnt': u'/', 'options': u'fill', 'size': u'6000', 'partition':'3'}}


    def tearDown(self):
        self.niisource = None
        if self.tmpdir.exists(): self.tmpdir.rmtree()

        
        
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
        
    
    def testKickstartFromNIIProfile(self):
        """ Test to validate ksprofile.  
        """
        
        ni = NodeInstaller(self.niisource)
        ni.parseNII()
        ksprofile = KickstartFromNIIProfile()

        # validate disk schema
        dp = DiskProfile(fresh=True)
        adaptedSchema = adaptNIIPartition(ni.partitions, dp)
        adaptedSchema == partition1()

