#!/usr/bin/env python
# $Id: test_partitiontool.py 476 2008-01-25 12:36:55Z hirwan $
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
from nose import SkipTest
from socket import gethostname

class TestDiskProfile:
    """Test cases for the DiskProfile class.
       Create an empty loopback device.
    """
    def setup(self):
        if not gethostname() == 'dizzy.int.osgdc.org':
            raise SkipTest, 'Test only runs on dizzy.int.osgdc.org(Internal machine)'
        size = 1024 * 1024 * 1024
        self.loopback, self.tmpfile = createLoopbackDevice(size)
        self.dp = DiskProfile(True, basename(self.loopback))

    def teardown(self):
        cmd = 'losetup -d %s' % self.loopback
        runCommand(cmd)
        cmd = 'rm -f %s' % self.tmpfile
        runCommand(cmd)

    def makePartitions(self):
        # Create 4 partitions.
        disk_id = basename(self.loopback)
        self.dp.newPartition(disk_id, 100, False, 'ext3', '/boot')
        self.dp.newPartition(disk_id, 300, False, 'ext3', '/')
        self.dp.newPartition(disk_id, 100, False, 'ext3', '/var')
        # Will create an extended and logical partition.
        self.dp.newPartition(disk_id, 500, False, 'ext3', '/data')
        assert len(self.dp.disk_dict) == 1
        self.disk = self.dp.disk_dict.values()[0]
        assert len(self.disk.partition_dict) == 5
        self.p1 = self.disk.partition_dict[1]
        self.p2 = self.disk.partition_dict[2]
        self.p3 = self.disk.partition_dict[3]
        self.p4 = self.disk.partition_dict[4]
        self.p5 = self.disk.partition_dict[5]
 
    def testRead(self):
        keys = sorted(self.dp.disk_dict.keys())
        assert keys[0] == basename(self.loopback), "Didn't detect disks correctly."
        assert len(keys) == 1, "Too many disks detected."

    def testMakePartitions(self):
        self.makePartitions()
        assert self.p1.size_MB > 90 and self.p1.size_MB < 110,\
                "Wrong partition size %d." % self.p1.size_MB
        assert self.p1.num == 1, "Wrong partition number 1."
        assert self.p1.path == self.loopback + 'p1', "Wrong path."

        assert self.p2.size_MB > 290 and self.p2.size_MB < 310,\
                "Wrong partition size %d." % self.p2.size_MB
        assert self.p2.num == 2, "Wrong partition number 2."
        assert self.p2.path == self.loopback + 'p2', "Wrong path."

        assert self.p3.size_MB > 90 and self.p3.size_MB < 110,\
                "Wrong partition size %d." % self.p3.size_MB
        assert self.p3.num == 3, "Wrong partition number 3."
        assert self.p3.path == self.loopback + 'p3', "Wrong path."

        assert self.p4.size_MB > 490 and self.p4.size_MB < 510,\
                "Wrong partition size %d." % self.p4.size_MB
        assert self.p4.num == 4, "Wrong partition number 4."
        assert self.p4.path == self.loopback + 'p4', "Wrong path."

        assert self.p5.size_MB > 490 and self.p5.size_MB < 510,\
                "Wrong partition size %d." % self.p5.size_MB
        assert self.p5.num == 5, "Wrong partition number 5."
        assert self.p5.path == self.loopback + 'p5', "Wrong path."

    def testDeletePart(self):
        raise SkipTest, 'This test causes segfaults on some machines.'
        self.makePartitions()
        self.dp.delete(self.p1)
        assert len(self.disk.partition_dict) == 3,\
            "Length (%d) wasn't 3 as expected. %s" %\
            (len(self.disk.partition_dict), str(self.disk.partition_dict.keys()))
        assert Set(self.disk.partition_dict.keys()) == Set([1,2,3]),\
                'Unexpected keys found: %s' % str(self.disk.partition_dict.keys())

        p1 = self.disk.partition_dict[1]
        p2 = self.disk.partition_dict[2]
        p3 = self.disk.partition_dict[3]
        self.dp.delete(p1, keep_in_place=True)
        assert len(self.disk.partition_dict) == 2,\
            "Length (%d) wasn't 2 as expected. %s" %\
            (len(self.disk.partition_dict), str(self.disk.partition_dict.keys()))
        assert Set(self.disk.partition_dict.keys()) == Set([2,3]), \
                'Unexpected keys found: %s' % str(self.disk.partition_dict.keys())

    def testResizePart(self):
        self.makePartitions()
        p5 = self.dp.editPartition(self.p5, 200, False, 'ext3', '/data')
        assert p5 == self.disk.partition_dict[5], "Edited object is different from dictionary object."
        assert p5.size_MB > 190 and p5.size_MB < 210,\
            "Edited size is incorrect(%d) from 200" % p5.size_MB

    def testChangePartFs(self):
        self.makePartitions()
        p2 = self.dp.editPartition(self.p2, self.p2.size_MB, False, 'ext2', self.p2.mountpoint)
        assert p2 == self.disk.partition_dict[2], "Edited object is different from dictionary object."
        assert p2.fs_type == 'ext2', 'FS type not changed.'


class FakeMountableDevice:
    def mount(self, **kwargs):
        pass
    def unmount(self):
        pass

class TestReadFstab:
    """Test cases for reading fstab."""
    def setUp(self):
        if not gethostname() == 'dizzy.int.osgdc.org':
            raise SkipTest, 'Test only runs on dizzy.int.osgdc.org(Internal machine)'
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
       # Dirty comment here... we're all
#over
    # the place, but shouldn't be picked up.
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

class TestLVM:
    """
        Test for LVM parts. ONLY RUNS ON DIZZY.
        Assumptions for dizzy:
            - Has an unused /dev/sdb with at least 10GB.
    """
    def setup(self):
        if not gethostname() == 'dizzy.int.osgdc.org':
            raise SkipTest, 'Test only runs on dizzy.int.osgdc.org(Internal machine)'
        self.dp = DiskProfile(True, probe_fstab=False)
        assert self.dp.disk_dict.has_key('sdb'), "dizzy must have a /dev/sdb!"
        sdb = self.dp.disk_dict['sdb']
        size_GB = sdb.length * sdb.sector_size / 1024 / 1024 / 1024
        assert size_GB >= 10, "/dev/sdb must be larger than 10GB."

    def makePartitions(self): 
        self.dp.newPartition('sdb', 100, False, 'ext3', '/boot')
        self.dp.newPartition('sdb', 1000, False, 'swap', None)
        pv = self.dp.newPartition('sdb', 8000, False, 'physical volume', None)

        nosey = self.dp.newLogicalVolumeGroup('NOSEY', '32M', [pv])
        self.dp.newLogicalVolume('PICKY', nosey, size_MB=3000, fs_type='ext3',
                                 mountpoint='/')
        self.dp.newLogicalVolume('BOGEY', nosey, size_MB=4000, fs_type='ext3',
                                 mountpoint='/data', fill=True)
