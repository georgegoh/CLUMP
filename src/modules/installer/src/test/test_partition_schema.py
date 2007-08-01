#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# This tests the setup disk profile.
from os.path import basename
from kusu.util.testing import *
from kusu.installer.defaults import *
from kusu.partitiontool.partitiontool import DiskProfile

class TestDiskProfileSchema:
    """
    Test cases for schemata.
    Limitation: can only test straightforward schemas. This means
    that LVM must still be tested by hand.
    """
 
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


    def setUp(self):
        size = 1024 * 1024 * 1024
        self.loopback, self.tmpfile = createLoopbackDevice(size)
        self.dp = DiskProfile(True, basename(self.loopback))

    def tearDown(self):
        cmd = 'losetup -d %s' % self.loopback
        runCommand(cmd)
        cmd = 'rm -f %s' % self.tmpfile
        runCommand(cmd)

    def testSchema(self):
        schema = self.generateSchema()
        setupDiskProfile(self.dp, schema)
        self.dp.commit()
        self.dp.formatAll()
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
            part_schema.append(part.split())

        assert part_schema[0][4] == 'primary'
        assert part_schema[1][4] == 'primary'
        assert part_schema[2][4] == 'primary'
        assert part_schema[3][4] == 'extended'
        assert part_schema[4][4] == 'logical'
