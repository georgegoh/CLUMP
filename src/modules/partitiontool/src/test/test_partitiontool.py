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
from tempfile import mkstemp
from sets import Set

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

class FakeMountableDevice:
    def mount(self, **kwargs):
        pass
    def unmount(self):
        pass

class TestReadFstab:
    """Test cases for reading fstab."""
    def setUp(self):
        fd, self.fstab_path = mkstemp(text=True)
        self.fstab = open(self.fstab_path, 'w')
        self.fstab.write("""# Test fstab, taken from my system
/dev/VolGroup00/LogVol00    /           ext3    defaults        1 1
LABEL=/boot                 /boot       ext3    defaults        1 2
devpts                      /dev/pts    devpts  gid=5,mode=620  0 0
tmpfs                       /dev/shm    tmpfs   defaults        0 0
proc                        /proc       proc    defaults        0 0
sysfs                       /sys        sysfs   defaults        0 0
/dev/VolGroup00/LogVol01    swap        swap    defaults        0 0
# More from Hirwan's
/dev/sda6                   /hd6        ext3    acl,user_xattr  1 1
# Mike's
/dev/cdroms/cdrom0          /mnt/cdrom  iso9660 noauto,ro       0 0
""")
        self.fstab.flush()
        self.fstab.close()
        self.dp = DiskProfile(True)

    def tearDown(self):
        cmd = 'rm -f %s' % self.fstab_path
        runCommand(cmd)

    def testExtractFstab(self):
        fmd = FakeMountableDevice()
        dev_map = self.dp.extractFstabToDevices(fmd, self.fstab_path)
        expected_keys = Set(['/dev/VolGroup00/LogVol00', '/dev/sda6', 'LABEL=/boot'])
        assert Set(dev_map.keys()) == expected_keys, 'Unexpected keys found: %s' % str(dev_map.keys())
        assert dev_map['/dev/VolGroup00/LogVol00'] == '/', "Key and Value don't match."
        assert dev_map['/dev/sda6'] == '/hd6', "Key and Value don't match."
        assert dev_map['LABEL=/boot'] == '/boot', "Key and Value don't match."
