#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
"""Partitiontool nodes test cases"""
from primitive.system.hardware.nodes import *
from nose import SkipTest
from nose.tools import assert_raises
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
        ''' handleCCISS returns the correct major/minor number for path'''
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
        ''' handleCCISS raises an AssertionError if given a bad path'''
        assert_raises(AssertionError, handleCCISS,
                                      path('/dev/cciss/c0d0p16'))
        assert_raises(AssertionError, handleCCISS,
                                      path('/dev/cciss/c8d0'))
        assert_raises(AssertionError, handleCCISS,
                                      path('/dev/cciss/c0d16'))

    def testGetMinorNumOffset_positive(self):
        ''' getMinorNumOffset returns the correct minor offset for path'''
        p = path('/dev/hda')
        assert getMinorNumOffset(p) == 0
        p = path('/dev/sda1')
        assert getMinorNumOffset(p) == 1
        p = path('/dev/sdb12')
        print getMinorNumOffset(p)
        assert getMinorNumOffset(p) == 12

    def testGetMinorNumOffset_negative(self):
        ''' getMinorNumOffset raises an AssertionError if given a bad path'''
        assert_raises(AssertionError, getMinorNumOffset,
                                      path('/dev/sda123'))

    def testHandleCDROM(self):
        ''' handleCDROM returns the correct major/minor numbers for path'''
        major, minor = handleCDROM(path('/dev/cdrom'))
        assert major == 11
        assert minor == 0
        major, minor = handleCDROM(path('/dev/hdc'))
        assert major == 11
        assert minor == 0
        major, minor = handleCDROM(path('/dev/cdrom1'))
        assert major == 11
        assert minor == 1

    def testHandleSCSIDisk(self):
        ''' handleSCSIDisk returns the correct major/minor numbers for path'''
        major, minor = handleSCSIDisk(path('/dev/sda'))
        assert major == 8
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sdp'))
        assert major == 8
        assert minor == 240

    def testHandleSCSIDiskExtendedDevices(self):
        raise SkipTest, "Don't test beyond /dev/sdp for now."
        major, minor = handleSCSIDisk(path('/dev/sdq'))
        assert major == 65
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sdaf'))
        assert major == 65
        assert minor == 240
        major, minor = handleSCSIDisk(path('/dev/sdag'))
        assert major == 66
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sdav'))
        assert major == 66
        assert minor == 240
        major, minor = handleSCSIDisk(path('/dev/sdaw'))
        assert major == 67
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sdbl'))
        assert major == 67
        assert minor == 240
        major, minor = handleSCSIDisk(path('/dev/sdbm'))
        assert major == 68
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sdcb'))
        assert major == 68
        assert minor == 240
        major, minor = handleSCSIDisk(path('/dev/sdcc'))
        assert major == 69
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sdcr'))
        assert major == 69
        assert minor == 240
        major, minor = handleSCSIDisk(path('/dev/sdcs'))
        assert major == 70
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sddh'))
        assert major == 70
        assert minor == 240
        major, minor = handleSCSIDisk(path('/dev/sddi'))
        assert major == 71
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sddx'))
        assert major == 71
        assert minor == 240
        major, minor = handleSCSIDisk(path('/dev/sdbm'))
        assert major == 68
        assert minor == 0
        major, minor = handleSCSIDisk(path('/dev/sdcb'))
        assert major == 68
        assert minor == 240


    def testHandleIDEDisk(self):
        raise SkipTest, "Work in progress"

    def testHandleLoopDevice(self):
        raise SkipTest, "Work in progress"
