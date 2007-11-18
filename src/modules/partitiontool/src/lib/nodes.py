#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool handle nodes.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import re
from os import *
from path import path
import kusu.util.log as kusulog
logger = kusulog.getKusuLog('partitiontool.nodes')

def checkAndMakeNode(devpath):
    """
    Give me a path to a disk device and I will check if it exists. If it
    doesn't, then I will create it according to the numbering schema
    by lanana.
    """
    logger.info('%s: Checking if node already exists in /dev.' % \
                devpath)
    device_path = path(devpath)

    if device_path.exists():
        logger.info('%s exists. Done' % devpath)
        return

    logger.info('%s does not exist. Creating...' % devpath)

    dev_basename = device_path.basename()

    if device_path.dirname().basename() == 'cciss':
        major,minor = handleCCISS(device_path)
    elif dev_basename.startswith('sr') or dev_basename.startswith('scd'):
        major,minor = handleCDROM(device_path)
    elif dev_basename.startswith('sd'):
        major,minor = handleSCSIDisk(device_path)
    elif dev_basename.startswith('hd'):
        major,minor = handleIDEDisk(device_path)
    elif dev_basename.startswith('loop'):
        major,minor = handleLoopDevice(device_path)
    else:
        raise UnknownDeviceError, "Cannot create %s - don't know the " + \
                                  "major/minor number scheme." % devpath

    logger.info('FORMAT %s: Create block device, major: %s, minor: %s, path: %s' % \
                (devpath, major, minor, devpath))
    raw_dev_num = makedev(major, minor)
    import stat
    mknod(devpath, (stat.S_IFBLK | 0644), raw_dev_num)
    return


def handleCCISS(devpath):
    if not devpath.dirname().exists():
        devpath.dirname().mkdir(mode=755)
    cciss_pat = re.compile('c(\d)d(\d+)p(\d+)')
    m = cciss_pat.match(devpath.basename())
    if m :
        c = int(m.groups()[0])
        d = int(m.groups()[1])
        p = int(m.groups()[2])
        assert p < 16
        major = 104 + c
        minor = d * 16 + p
    else:
        cciss_pat = re.compile('c(\d)d(\d+)')
        m = cciss_pat.match(devpath.basename())
        c = int(m.groups()[0])
        d = int(m.groups()[1])
        major = 104 + c
        minor = d * 16
    assert major < 112
    assert minor < 256
    return major,minor 


def getMinorNumOffset(devpath):
    s = str(devpath)
    if s[-1] in '1234567890':
        num = int(s[-1])
        if s[-2] in '1234567890':
            assert s[-3] not in '1234567890', "Number too large"
            num = int(s[-2:])
    else: num = 0
    return num


def handleCDROM(devpath):
    major = 11
    minor = getMinorNumOffset(devpath)
    return major,minor


def handleSCSIDisk(devpath):
    alpha = 'abcdefghijklmnopqrstuvwxyz'
    li = [ x for x in alpha ]
    major = 8
    num = getMinorNumOffset(devpath)
    if num==0: minor_multiplier = li.index(str(devpath)[-1])
    elif num<10: minor_multiplier = li.index(str(devpath)[-2])
    else: minor_multiplier = li.index(str(devpath)[-3])
    minor = 16 * minor_multiplier + num
    return major,minor


def handleIDEDisk(devpath):
    minor = getMinorNumOffset(devpath)
    # first IDE interface
    if devpath.basename().startswith('hda'):
        major = 3
    elif devpath.basename().startswith('hdb'):
        major = 3
        minor += 64
    # second IDE interface
    elif devpath.basename().startswith('hdc'):
        major = 22
    elif devpath.basename().startswith('hdd'):
        major = 22
        minor += 64
    # third IDE interface
    elif devpath.basename().startswith('hde'):
        major = 33
    elif devpath.basename().startswith('hdf'):
        major = 33
        minor += 64
    # fourth IDE interface
    elif devpath.basename().startswith('hdg'):
        major = 34
    elif devpath.basename().startswith('hdh'):
        major = 34
        minor += 64
    # fifth IDE interface
    elif devpath.basename().startswith('hdi'):
        major = 56
    elif devpath.basename().startswith('hdj'):
        major = 56
        minor += 64
    # sixth IDE interface
    elif devpath.basename().startswith('hdk'):
        major = 57
    elif devpath.basename().startswith('hdl'):
        major = 57
        minor += 64
    return major,minor


def handleLoopDevice(devpath):
    major = 57
    minor = getMinorNumOffset(devpath)
    return major,minor
