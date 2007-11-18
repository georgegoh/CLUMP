#!/usr/bin/env python
# $Id$
#
# Kusu Partition tool nodes test cases.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
from kusu.partitiontool.nodes import *
from nose import SkipTest
from path import path

class TestNodes:
    """
    Test cases for node.py
    Device numbers taken from
    http://www.lanana.org/docs/device-list/devices-2.6+.txt
    """
    def setup(self):
        pass

    def teardown(self):
        pass

    def testHandleCCISS_positive(self):
        p = path('/dev/cciss/c0d0')
        major, minor = handleCCISS(p)
        assert major == 104
        assert minor == 0
        p = path('/dev/cciss/c0d0p1')
        major, minor = handleCCISS(p)
        assert major == 104
        assert minor == 1
        p = path('/dev/cciss/c7d15')
        major, minor = handleCCISS(p)
        assert major == 111
        assert minor == 240
        p = path('/dev/cciss/c7d15p15')
        major, minor = handleCCISS(p)
        assert major == 111
        assert minor == 255

    def testHandleCCISS_negative(self):
        raise SkipTest, "Work in progress"
        try:
            p = path('/dev/cciss/c0d0p0')
            handleCCISS(p)
            p = path('/dev/cciss/c0d0p16')
            handleCCISS(p)
            p = path('/dev/cciss/c8d0')
            handleCCISS(p)
            p = path('/dev/cciss/c0d16')
            handleCCISS(p)
            raise Exception, "Should have thrown exception here"
        except AssertionError:
            return

    def testGetMinorNumOffset_positive(self):
        p = path('/dev/hda')
        assert getMinorNumOffset(p) == 0
        p = path('/dev/sda1')
        assert getMinorNumOffset(p) == 1
        p = path('/dev/sdb10')
        print getMinorNumOffset(p)
        assert getMinorNumOffset(p) == 10

    def testGetMinorNumOffset_negative(self):
        raise SkipTest, "Work in progress"

    def testHandleCDROM(self):
        raise SkipTest, "Work in progress"

    def testHandleSCSIDisk(self):
        raise SkipTest, "Work in progress"

    def testHandleIDEDisk(self):
        raise SkipTest, "Work in progress"

    def testHandleLoopDevice(self):
        raise SkipTest, "Work in progress"
