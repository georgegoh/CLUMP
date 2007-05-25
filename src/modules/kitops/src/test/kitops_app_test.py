#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

import os
import sys
if os.getuid() != 0:
    sys.exit("Test must be run as root.")

import tempfile
import subprocess
from path import path

from kusu.kitops.kitops import KitOps

test_kits = path('/home/mike/kusudev/isos')
saved_kusu_root = None
temp_root = None
temp_mount = None

def setUp():
    global saved_kusu_root
    global temp_root
    global temp_mount

    saved_kusu_root = os.environ.get('KUSU_ROOT', None)
    temp_root = path(tempfile.mkdtemp(prefix='kot'))
    temp_mount = path(tempfile.mkdtemp(prefix='kot'))

    os.environ['KUSU_ROOT'] = str(temp_root)

def tearDown():
    global saved_kusu_root
    global temp_root

    if saved_kusu_root is not None:
        os.environ['KUSU_ROOT'] = saved_kusu_root

    temp_root.rmtree()
    temp_mount.rmtree()

class TestBaseKit:
    def setUp(self):
        global temp_root
        global temp_mount

        self.temp_root = temp_root
        self.temp_mount = temp_mount
        self.depot_dir = self.temp_root / 'depot'
        self.kits_dir = self.depot_dir / 'kits'

        self.kit = test_kits / 'kit-base-0.1-0.noarch.iso'
        self.kit_rpm = 'kit-base-0.1-0.noarch.rpm'
        self.kit_name = 'base'
        self.kit_ver = '0.1'

        mountP = subprocess.Popen('mount -o loop %s %s 2> /dev/null' %
                                  (self.kit, self.temp_mount), shell=True)
        mountP.wait()

    def tearDown(self):
        # wipe out installed files
        if self.depot_dir.exists():
            self.depot_dir.rmtree()

        umountP = subprocess.Popen('umount %s 2> /dev/null' % self.temp_mount,
                                   shell=True)
        umountP.wait()

    def testAddKit(self):
        addP = subprocess.Popen('kitops -a -m %s' % self.kit, shell=True)
        rv = addP.wait()

        assert rv == 0, 'kitops returned error: %s' % rv

        # assert all directories exist
        assert self.depot_dir.exists()
        assert self.kits_dir.exists()
        assert path(self.kits_dir / self.kit_name).exists()
        assert path(self.kits_dir / self.kit_name / self.kit_ver).exists()

        # assert contents are the same
        assert areContentsEqual(self.temp_mount / self.kit_name,
                                self.kits_dir / self.kit_name / self.kit_ver,
                                '*.rpm', [self.kit_rpm])

        # check DB for information

        # verify the kit RPM is installed
        assert isRPMInstalled('kit-' + self.kit_name)

        # clean up after this test
        rpmP = subprocess.Popen('rpm --quiet -e --nodeps kit-%s' %
                                self.kit_name, shell=True)
        self.depot_dir.rmtree()

    def testDeleteKit(self):
        pass

    def testListKits(self):
        pass

def areContentsEqual(src, dest, glob_pattern, omit=[]):
    """
    Compare contents of two directories and returns True if equal.

    Arguments:
    src -- source directory
    dest -- destination directory
    glob_pattern -- pattern of files to look at (ie: if '*.rpm', ls *.rpm)
    omit -- files to ignore in comparison (ie: ls *.rpm | grep -v hi.rpm)
    """

    src_list = [f.basename() for f in src.glob(glob_pattern)]
    dest_list = [f.basename() for f in dest.glob(glob_pattern)]

    for item in omit:
        try:
            src_list.remove(item)
        except ValueError:
            pass

        # to ensure exception from src remove does not preempt dest remove
        try:
            dest_list.remove(item)
        except ValueError:
            pass

    return src_list.sort() == dest_list.sort()

def isRPMInstalled(pattern):
    """
    Return True if RPM matching pattern is currently installed.
    """

    tmp_fd, tmp_fn = tempfile.mkstemp()

    # run the command and store output in temp file
    rpmP = subprocess.Popen('rpm -qa %s' % pattern, shell=True, stdout=tmp_fd)
    rpmP.wait()

    tmp_fn = path(tmp_fn)
    tmp_size = tmp_fn.getsize() # will be zero if no output from rpmP

    os.close(tmp_fd)
    tmp_fn.remove()

    return tmp_size != 0
