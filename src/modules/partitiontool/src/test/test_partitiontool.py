#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool Test Cases.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import math
import tempfile
import subprocess
from lvm import *
import kusu.hardware.probe
from os.path import basename, exists
from kusu.util.errors import *
import unittest

def runCommand(cmd):
    p = subprocess.Popen(cmd,
                     shell=True,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
    out, err = p.communicate()
    print '"%s" stdout: %s stderr: %s' %(cmd, out, err)


class DiskProfileTestCase(unittest.TestCase):
    """Test cases for the DiskProfile class.
       Create an empty loopback device.
    """
    def setUp(self):
        print 'Making loopback device /dev/loop0 of 1GB'
        size = 1024 * 1024 * 1024
        self.tmpfile = tempfile.mktemp
        cmd = 'head -c %d < /dev/zero > %s' % (size, self.tmpfile)
        runCommand(cmd)
        cmd = 'losetup /dev/loop0 %s' % self.tmpfile
        runCommand(cmd)
        self.dp = DiskProfile(True, 'loop0')

    def tearDown(self):
        cmd = 'losetup -d /dev/loop0'
        runCommand(cmd)
        pass

    def testRead(self):
        keys = sorted(self.dp.disk_dict.keys())
        assert keys[0] == 'loop0', "Didn't detect disks correctly."

    def testMakePart(self):
        self.dp.newPartition
        pass

class DiskTestCase(unittest.TestCase):
    """"""

class PartitionTestCase(unittest.TestCase):
    """"""

