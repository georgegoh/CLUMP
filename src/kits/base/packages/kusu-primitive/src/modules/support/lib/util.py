#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
""" This module contains miscellaneous utilities that don't
really fit anywhere else."""
import md5
import sha
from errors import DeviceNotFoundException
from errors import MountPointException
from errors import InvalidMacAddressException
from primitive.core.errors import ModuleException
from path import path
from types import StringType
try:
    import subprocess
except:
    from popen5 import subprocess

def runCommand(cmd):
    """ Run one command only, when you don't want to bother setting up
        the Popen stuff.
    """
    try:
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError,e:
        raise ModuleException, 'RunCommand failed due to OSError %s' % e
    if p.returncode:
        raise ModuleException,'Command %s failed with return code %d : %s' % (cmd , p.returncode, err)
    return out, err

def pollCommand(command):
    """ This shows the output of a subprocess as it happens.
    """
    import sys
    currentProcess = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdOutdata = []
    stdErrData = []
    while True:
        processLine = currentProcess.stdout.readline()
        if processLine == '' and currentProcess.poll() != None:
            break
        stdOutdata.append(processLine)        
        sys.stdout.write(processLine)
        sys.stdout.flush()
    stdErrData.append(currentProcess.stderr.read())
    return (stdOutdata, stdErrData)
 
def MD5SUM(infile):
    """ Get a file's MD5SUM."""
    f = open(infile)
    m = md5.new()
    buf = f.read(8096)
    while buf:
        m.update(buf)
        buf = f.read(8096)
    return m.hexdigest()

def SHASUM(infile):
    """ Get a file's SHA1SUM."""
 
    f = open(infile)
    m = sha.new()
    buf = f.read(8096)
    while buf:
        m.update(buf)
        buf = f.read(8096)
    return m.hexdigest()

def convertUUIDToStr(bytes):
    """ Takes a UUID expressed in bytes and returns as a formatted string."""
    s = ('%02x'*16) % tuple(map(ord, bytes))
    return '%s-%s-%s-%s-%s' % (s[:8], s[8:12], s[12:16], s[16:20], s[20:])


def getFstype(dev):
    p = subprocess.Popen('file %s | grep -i squashfs' % dev,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode == 0:
        return 'squashfs'
    else:
        return 'others'


def mountLoop(dev, mntpath):
    """ Attempts to mount a given device to a path using loopback."""
    if not path(dev).exists():
        raise DeviceNotFoundException, \
              'Given device path %s is not valid.' % str(dev)

    mp = path(mntpath)
    if not mp.exists() or not mp.isdir():
        raise MountPointException, \
              'Given mount point is not an existing directory.'

    fstype = getFstype(dev)
    if fstype == 'squashfs':
        cmd = ['mount', '-o', 'loop', '-t', 'squashfs', dev, mntpath]
    else:
        cmd = ['mount', '-o', 'loop', dev, mntpath]

    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    retcode = p.returncode
    return (retcode, stdout, stderr)


def unmount(mntpnt):
    """ Attempts to unmount a given mountpoint."""
    mp = path(mntpnt)
    if not mp.exists() or not mp.isdir():
        raise MountPointException, \
              'Given mount point is not an existing directory.'

    p = subprocess.Popen(['umount', mntpnt],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    retcode = p.returncode
    return (retcode, stdout, stderr)

def convertStrMACAddresstoInt(mac):
    """ Returns integer form of hexadecimal MAC address string of the form 01:23:45:67:89:ab.

        Raises InvalidMacAddressException if the MAC address is not a colon separated, hexadecimal like string.
    """
    if type(mac) != StringType:
        raise InvalidMacAddressException, 'Input MAC address is not of string form.'

    try:
        return int(mac.replace(':', ''), 16)
    except ValueError:
        raise InvalidMacAddressException, 'Input MAC address provided could not be converted to integer form.'
