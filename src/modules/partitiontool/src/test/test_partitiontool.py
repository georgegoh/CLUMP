#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool Test Cases.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import tempfile
import subprocess
from kusu.partitiontool.partitiontool import DiskProfile
from os import stat
from os.path import basename

def runCommand(cmd):
    p = subprocess.Popen(cmd,
                     shell=True,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
    out, err = p.communicate()
    print '"%s" stdout: %s stderr: %s' %(cmd, out, err)
    return out, err

class TestDiskProfile:
    """Test cases for the DiskProfile class.
       Create an empty loopback device.
    """
    def setUp(self):
        out, err = runCommand('losetup -f')
        self.loopback = out.strip()
        print 'free loopback device: %s' % self.loopback
        assert self.loopback, "No free loopback device."

        print 'Creating 1GB tempfile. This may take a while...'
        size = 1024 * 1024 * 1024
        self.tmpfile = tempfile.mktemp()
        cmd = 'head -c %d < /dev/zero > %s' % (size, self.tmpfile)
        runCommand(cmd)
        assert stat(self.tmpfile).st_size == size, "Didn't create tempfile of right size."

        cmd = 'losetup %s %s' % (self.loopback, self.tmpfile)
        runCommand(cmd)

        cmd = 'losetup %s' % self.loopback
        out, err = runCommand(cmd)
        loopback_file = out.split()[-1].strip('()')
        assert loopback_file == self.tmpfile, "loopback file doesn't match tempfile."

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

