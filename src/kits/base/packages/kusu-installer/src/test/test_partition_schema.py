#!/usr/bin/env python
#
# $Id: test_partition_schema.py 1757 2008-11-06 22:31:19Z mblack $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# This tests the setup disk profile.
from os.path import basename
from socket import gethostname
from kusu.util.testing import *
from kusu.installer.defaults import *
from primitive.system.hardware.partitiontool import DiskProfile
import primitive.system.hardware.disk as disk
from nose import SkipTest

class PartedPartition(object):
    def __init__(self, parted_str):
        parsed = parted_str.split()
        self.num = parsed[0]
        self.size = parsed[3]
        self.type = parsed[4]


class TestDiskProfileSchema:
    """
    Test cases for schemata.
    Limitation: can only test straightforward schemas. This means
    that LVM must still be tested by hand.
    """
    def setUp(self):
        if gethostname() == 'dizzy.int.osgdc.org':
            self.dp = DiskProfile(False, probe_fstab=False)
        else:
            raise SkipTest
            size = 1024 * 1024 * 1024
            self.loopback, self.tmpfile = createLoopbackDevice(size)
            self.dp = DiskProfile(True, basename(self.loopback))

    def tearDown(self):
        if gethostname() != 'dizzy.int.osgdc.org':
            cmd = 'losetup -d %s' % self.loopback
            runCommand(cmd)
            cmd = 'rm -f %s' % self.tmpfile
            runCommand(cmd)

    def readPartedOutput(self):
        schema = self.generateSchema()
        setupDiskProfile(self.dp, schema)
        self.dp.commit()
        self.dp.formatAll()
        if gethostname() == 'dizzy.int.osgdc.org':
            out, err = runCommand('parted /dev/sda print')
        else:
            out, err = runCommand('parted %s print' % self.loopback)
        lines = out.splitlines()
        starting_line_index = 0
        for i,v in enumerate(lines):
            stripped = v.strip()
            if stripped.startswith('Number'):
                starting_line_index = i + 1
        parts = lines[starting_line_index:-5]
        part_schema = []
        for part in parts:
            part_schema.append(PartedPartition(part))
        return part_schema

    def testSchema(self):
        schema = self.readPartedOutput()
        self.schemaAssertions(schema)

 
    def generateSchema(self):
        """This is a plain vanilla schema that contains 4 physical partitions:
              a. /boot - ext3, 100:
              b. swap - 200M
              c. / - 200M
              d. /depot - 300M (fill)
        """
        # define the physical disk and partitions first
        d1 = Disk()

        # /boot
        d1p1 = Partition()
        d1p1.size_MB = 100
        d1p1.fs = 'ext3'
        d1p1.mountpoint = '/boot'
        d1p1.fill = False
        d1.addPartition(d1p1)

        # swap
        d1p2 = Partition()
        d1p2.size_MB = 200
        d1p2.fs = 'linux-swap'
        d1p2.mountpoint = None
        d1p2.fill = False
        d1.addPartition(d1p2)

        # /
        d1p3 = Partition()
        d1p3.size_MB = 200
        d1p3.fs = 'ext3'
        d1p3.mountpoint = '/'
        d1p3.fill = False
        d1.addPartition(d1p3)

        # /depot
        d1p4 = Partition()
        d1p4.size_MB = 300
        d1p4.fs = 'ext3'
        d1p4.mountpoint = '/depot'
        d1p4.fill = True
        d1.addPartition(d1p4)

        disks = DiskCollection()
        disks.addDisk(d1)
        return PartitionSchema(disks=disks)

    def schemaAssertions(self, part_schema):
        assert part_schema[0].type == 'primary'
        assert part_schema[1].type == 'primary'
        assert part_schema[2].type == 'primary'
        assert part_schema[3].type == 'extended'
        assert part_schema[4].type == 'logical'


class TestSchemaLVM(TestDiskProfileSchema):
    def generateSchema(self):
        """This is a plain vanilla schema that contains 4 physical partitions:
              a. /boot - ext3, 100:
              b. swap - 200M
              c. LVM PV - 6000M (fill)
              d. LVM VG - PV
              e. LVM LV - / - 2000M
              f. LVM LV - /data - 4000M
        """
        # define the physical disk and partitions first
        d1 = Disk()

        # /boot
        d1p1 = Partition()
        d1p1.size_MB = 100
        d1p1.fs = 'ext3'
        d1p1.mountpoint = '/boot'
        d1p1.fill = False
        d1.addPartition(d1p1)

        # swap
        d1p2 = Partition()
        d1p2.size_MB = 200
        d1p2.fs = 'linux-swap'
        d1p2.mountpoint = None
        d1p2.fill = False
        d1.addPartition(d1p2)

        d1p3 = Partition()
        d1p3.size_MB = 6000
        d1p3.fs = 'physical volume'
        d1p3.mountpoint = None
        d1p3.fill = True
        d1.addPartition(d1p3)

        disks = DiskCollection()
        disks.addDisk(d1)

        volgroup00 = LVMGroup()
        volgroup00.name = 'VolGroup00'
        volgroup00.extent_size = '32M'
        volgroup00.pv_span = True
        volgroup00.addPV(disk='N', partition='N')

        root = LVMLogicalVolume()
        root.name = 'ROOT'
        root.size_MB = 2000
        root.fs = 'ext3'
        root.mountpoint = '/'
        root.fill = False
        volgroup00.addLV(root)

        data = LVMLogicalVolume()
        data.name = 'DATA'
        data.size_MB = 4000
        data.fs = 'ext3'
        data.mountpoint = '/data'
        data.fill = True
        volgroup00.addLV(data)

        lvm = LVMCollection()
        lvm.addVG(volgroup00)

        preserve_types = disk.Partition.native_type_dict.values()
        preserve_fs = DiskProfile.fsType_dict.keys()
        preserve_mntpnt = []
        return PartitionSchema(disks=disks, lvm=lvm, preserve_types=preserve_types,
                              preserve_fs=preserve_fs, preserve_mntpnt=preserve_mntpnt)


    def schemaAssertions(self, part_schema):
        assert part_schema[0].type == 'primary'
        assert part_schema[1].type == 'primary'
        assert part_schema[2].type == 'primary'
        assert part_schema[3].type == 'extended'
        assert part_schema[4].type == 'logical'

    def testSchema(self):
        if gethostname() != 'dizzy.int.osgdc.org':
            raise SkipTest
        schema = self.readPartedOutput()
        self.schemaAssertions(schema)
