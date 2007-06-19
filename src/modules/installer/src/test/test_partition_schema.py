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

def testSchema():
    """This is a plain vanilla schema that contains 4 physical partitions:
          a. /boot - ext3, 100:
          b. swap - 200M
          c. / - 200M
          d. /depot - 300M (fill)
    """
    # define the physical disk and partitions first
    disk_dict = { 1: { 'partition_dict': {} } }
    disk1_partition_dict = disk_dict[1]['partition_dict']
    disk1_partition_dict[1] = { 'size_MB': 100,
                                'fs': 'ext3',
                                'mountpoint': '/boot',
                                'fill': False}
    disk1_partition_dict[2] = { 'size_MB': 200,
                                'fs': 'linux-swap',
                                'mountpoint': None,
                                'fill': False}
    disk1_partition_dict[3] = { 'size_MB': 200,
                                'fs': 'ext3',
                                'mountpoint': '/',
                                'fill': False}
    disk1_partition_dict[4] = { 'size_MB': 300,
                                'fs': 'ext3',
                                'mountpoint': '/depot',
                                'fill': True}

    schema = {'disk_dict' : disk_dict,
              'vg_dict' : None}

    return schema


class TestDiskProfileSchema:
    """
    Test cases for schemata.
    Limitation: can only test straightforward schemas. This means
    that LVM must still be tested by hand.
    """
    def setUp(self):
        size = 1024 * 1024 * 1024
        self.loopback, self.tmpfile = createLoopbackDevice(size)
        self.dp = DiskProfile(True, basename(self.loopback))

    def tearDown(self):
        cmd = 'losetup -d %s' % self.loopback
        runCommand(cmd)
        cmd = 'rm -f %s' % self.tmpfile
        runCommand(cmd)

    def testVanillaSchema(self):
        schema = testSchema()
        setupDiskProfile(self.dp, schema)
        self.dp.commit()
        self.dp.formatAll()
        out, err = runCommand('parted %s print' % self.loopback)
        lines = out.splitlines()
        parts = lines[6:-5]
        part_schema = []
        for part in parts:
            part_schema.append(part.split())

        assert part_schema[0][4] == 'primary'
        assert part_schema[1][4] == 'primary'
        assert part_schema[2][4] == 'primary'
        assert part_schema[3][4] == 'extended'
        assert part_schema[4][4] == 'logical'
