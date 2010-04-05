#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id: testing.py 3150 2009-10-30 01:38:36Z mike $
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along wit:
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import tempfile
import subprocess
import os
from path import path
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
    assert stat(tmpfile).st_size == size,\
        "Didn't create tempfile of right size(%d vs %d)." % (size, stat(tmpfile).st_size)

    cmd = 'losetup %s %s' % (loopback, tmpfile)
    runCommand(cmd)

    cmd = 'losetup %s' % loopback
    out, err = runCommand(cmd)
    loopback_file = out.split()[-1].strip('()')
    assert loopback_file == tmpfile, "loopback file doesn't match tempfile."

    return loopback, tmpfile

def download(url, dest=os.environ.get('KUSU_TMP', '/tmp')):

    filename = path(url).basename()
    dest = path(dest) / filename

    if dest.exists():
        return

    import urllib2
    f = urllib2.urlopen(url)
    content = f.read()
    f.close()

    f = open(dest, 'w')
    f.write(content)
    f.close()

def isFileExists(filename):
    """Returns True if the given filename exists."""
    try:
        f = open(filename)
        f.close()
    except IOError, e:
        if e.errno == 2:
            return False
        else:
            raise e
    return True

def temp_dir(prefix='kusutest'):
    """
    A decorator providing a temporary directory for a method.

    The temporary directory will always be removed after the method
    terminates. The temporary directory is a path.path() object, and is
    passed to the method as an argument. Stack as many decorators on a
    method as you need. The optional `prefix` argument sets the prefix
    for the temporary directory.

    Example:
    @temp_dir()
    @temp_dir()
    def method(our, regular, arguments, tempdir1, tempdir2):
        # do your thing
        # regardless of how your function terminates,
        # tempdir1 and tempdir2 should be removed
    """

    def _temp_dir(meth):
        def wrapper(*__args, **__kw):
            td = path(tempfile.mkdtemp(prefix=prefix, dir=os.environ.get('KUSU_TMP', '/tmp')))
            __args += (td, )
            try:
                return meth(*__args, **__kw)
            finally:
                if td.ismount():
                    # Let's first unmount this directory, if needed.
                    cmd = ['umount', td]
                    umountP = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    umountPo, umountPe = umountP.communicate()

                    if 0 != umountP.returncode:
                        sys.stderr.write('WARNING: could not `umount %s`, return code: %s\n' % (td, umountP.returncode) +
                                         'stdout:\n%s\nstderr:\n%s\n' % (umountPo, umountPe))

                # It's possible that the function changed td.
                if td.isdir():
                    td.rmtree()
                elif td.isfile():
                    td.remove()

        wrapper.__name__ = meth.__name__
        wrapper.__dict__ = meth.__dict__
        wrapper.__doc__ = meth.__doc__
        return wrapper
    return _temp_dir

