#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool Test Cases.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import tempfile
import subprocess
from kusu.partitiontool.partitiontool import DiskProfile
from os import stat
from os.path import basename
from kusu.util.testing import *

class TestDiskProfile:
    """Test cases for the DiskProfile class.
       Create an empty loopback device.
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

    def testRead(self):
        keys = sorted(self.dp.disk_dict.keys())
        assert keys[0] == basename(self.loopback), "Didn't detect disks correctly."
        assert len(keys) == 1, "Too many disks detected."

    def testMakePart(self):
        disk_id = basename(self.loopback)
        part_obj = self.dp.newPartition(disk_id, 100, False, 'ext3', '/')
        assert part_obj.size_MB > 96 and part_obj.size_MB < 104, "Wrong partition size."
        assert part_obj.num == 1, "Wrong partition number."
        assert part_obj.path == self.loopback + 'p1', "Wrong path."

