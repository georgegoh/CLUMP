#!/usr/bin/env python
# $Id$
#
# Common source for tests.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import tempfile
import subprocess
from os import stat
from os.path import basename
import kusu.util.log as kusulog

logger = kusulog.getKusuLog('util.testing')

def runCommand(cmd):
    """
    Run one command only, when you don't want to bother setting up
    the Popen stuff.
    """
    p = subprocess.Popen(cmd,
                     shell=True,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
    out, err = p.communicate()
    print '"%s" stdout: %s stderr: %s' %(cmd, out, err)
    return out, err

def createLoopbackDevice(size):
    """
    Create a loopback device of a given size. Returns a tuple:
    (loopback_path, loopback_file)
    """
    out, err = runCommand('losetup -f')
    loopback = out.strip()
    print 'free loopback device: %s' % loopback
    assert loopback, "No free loopback device."

    print 'Creating tempfile. This may take a while...'
    tmpfile = tempfile.mktemp(prefix='k-u-t-tmp')
    cmd = 'head -c %d < /dev/zero > %s' % (size, tmpfile)
    runCommand(cmd)
    assert stat(tmpfile).st_size == size, "Didn't create tempfile of right size."

    cmd = 'losetup %s %s' % (loopback, tmpfile)
    runCommand(cmd)

    cmd = 'losetup %s' % loopback
    out, err = runCommand(cmd)
    loopback_file = out.split()[-1].strip('()')
    assert loopback_file == tmpfile, "loopback file doesn't match tempfile."

    return loopback, tmpfile
