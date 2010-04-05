#!/usr/bin/env python
# $Id: util_test.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
"""
Tests for the Primitive support.util module.
"""
from sets import Set
from path import path
from tempfile import mkdtemp
from nose.tools import assert_raises
from primitive.support.util import runCommand
from primitive.support.util import mountLoop
from primitive.support.util import unmount
from primitive.support.util import convertStrMACAddresstoInt
from primitive.fetchtool.commands import FetchCommand
from primitive.support.errors import InvalidMacAddressException

from nose.tools import assert_raises
 
TESTMOUNT_IMG1 = 'http://www.osgdc.org/pub/build/tests/modules/primitive/support/mounttest.img'
TESTMOUNT_IMG1_DIRS = ['a', 'b']
TESTMOUNT_IMG1_FILES = ['apple', 'bear']

def testRunCommandStdOut():
    ''' runCommand called with regular arguments and output on stdout.'''
    out, err = runCommand('echo "Hello World"')
    assert out.strip() == 'Hello World'


def testRunCommandStdErr():
    ''' runCommand called with regular arguments and output on stderr.'''
    out, err = runCommand('echo "Hello World" >&2')
    assert err.strip() == 'Hello World'


def testConvertStrMACAddresstoInt():
    ''' convertStrMACAddresstoInt called with string mac address'''
    intMAC = convertStrMACAddresstoInt('00:0c:29:6e:0d:c1')
    assert intMAC == 52234685889


def testConvertStrMACAddresstoIntException():
    ''' convertStrMACAddresstoInt called with non-string input and non-integer like string'''
    assert_raises(InvalidMacAddressException, convertStrMACAddresstoInt, 123)
    assert_raises(InvalidMacAddressException, convertStrMACAddresstoInt, 'ZY:XW:VU:TS:RQ:PO')


def testMountUnmountLoop():
    ''' mounting and unmounting of a loopback device.'''
    dest_dir = path(mkdtemp(prefix='TestMountLoop-'))
    mnt_dir = path(mkdtemp(prefix='TestMountLoop-Mntdir-'))
    fc = FetchCommand(uri=TESTMOUNT_IMG1, fetchdir=False,
                      destdir=dest_dir, overwrite=True)
    mountLoop(fc.execute()[1], mnt_dir)
    # verify directory and file list are present after mount.
    d = [x.basename() for x in mnt_dir.dirs()]
    assert Set(d) == Set(TESTMOUNT_IMG1_DIRS)
    f = [x.basename() for x in mnt_dir.files()]
    assert Set(f) == Set(TESTMOUNT_IMG1_FILES)

    unmount(mnt_dir)
    # verify empty directory after unmount.
    d = [x.basename() for x in mnt_dir.dirs()]
    assert not d
    f = [x.basename() for x in mnt_dir.files()]
    assert not f
    dest_dir.rmtree()
    mnt_dir.rmtree()
