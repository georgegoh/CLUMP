#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from path import path

# General utility
def readFile(filename):
    f = open(filename, 'r')
    content = f.read()
    f.close()

    return content.strip()


# dmraid
def getDMRAID():
    # list of devices under raid
    #dmraid -b -c 

    dmraidP = subprocess.Popen('dmraid -s -c', 
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = dmraidP.communicate()

    returncode = dmraidP.returncode

    if not returncode:
        return [ str(path('/dev/mapper') / d)for d in out.split() ]

# Linux software raid
def getSoftwareRaid():
    pass    

# IDE
def getIDE(type):
    """Probes for a specific type of IDE device(disk, cdrom, or tape).
       Returns a dictionary of dictionaries. Sample code:
          disks = getIDE('disk')
          hda = disks['hda']
          print hda['model'] # prints model name of first IDE hard disk.
    """
    if type not in ['disk', 'cdrom', 'tape']:
        raise Exception, 'Unknown type'

    ide_path = path('/proc/ide')

    d = {}
    if ide_path.exists():
        for hd in ide_path.listdir('hd*'):
            media = hd / 'media'
            
            if readFile(media) == type:
                model = hd / 'model'
                model = readFile(model)

                d[hd.basename()] = {'model': model}

    return d

# SCSI
def getSCSI(type):
    """Probes for a specific type of SCSI device(disk, cdrom, or floppy).
       Returns a dictionary of dictionaries. Sample code:
          disks = getIDE('disk')
          sda = disks['sda']
          print sda['model'] # prints model name of first SCSI hard disk.
          print sda['vendor'] # prints vendor name of first SCSI hard disk.
    """
 
    # Based on scsi.h, scsi.c(kudzu) 
    type_map = {'disk': [0x00, 0x07, 0x0e], \
                'cdrom': [0x04, 0x05], \
                'floppy': [0x06] }             

    if type not in type_map.keys():
        raise Exception, 'Unknown type'

    scsi_path = path('/sys/bus/scsi/devices')

    d = {}
    for s in scsi_path.listdir():
        if (s / 'type').exists() and \
            int(readFile(s / 'type')) in type_map[type]:

            dev = s.listdir('block:*')
        
            # block:<dev> exists
            if dev: 
                dev = dev[0].realpath()
            else: # block exists
                dev = (s / 'block').realpath()

            # Check for removable, including usb cdrom/thumbdrive
            # usb portable hardrive are not excluded here
            removable = dev.realpath() / 'removable'
            if removable.exists() \
               and int(readFile(removable)) \
               and type in ['disk']: continue

            # Checks for usb devices that presents itself as scsi
            # such as usb portable hardrive which removable=0
            idx = (dev / 'device').realpath().find('usb')
            if idx != -1: # part of the usb bus
                usb = path((dev / 'device').realpath()[idx:])

                # And yes, the block device matches back
                if (path('/sys/bus/usb/devices') / usb / 'block').realpath().basename() == dev.basename() \
                   and type in ['disk']: continue

            dev = dev.basename()
            # Handle cciss!c0d0 in /sys/block
            if dev.find('cciss!') != -1:
                dev = dev.replace('!', os.sep)

            d[dev] = {}
            d[dev]['vendor'] = readFile(s / 'vendor')
            d[dev]['model'] = readFile(s / 'model')
    

    return d 
#


