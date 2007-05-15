#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.hardware.read import readFile
from path import path

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
