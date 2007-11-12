#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from kusu.util.errors import *
from path import path
from kusu.hardware.pci import PCI

# General utility
def readFile(filename):
    if os.path.exists(filename):
        f = open(filename, 'r')
        content = f.read()
        f.close()

        # Remove any \n 
        content = content.strip()

        if content:
            return content
        else:
            return None # Don't return '' 
        
    else:
        return None


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
        raise UnknownTypeError, 'Unknown type'

    ide_path = path('/proc/ide')

    d = {}
    if ide_path.exists():
        for hd in ide_path.listdir('hd*'):
            media = hd / 'media'
            
            if readFile(media) == type:
                d[hd.basename()] = {'model': readFile(hd / 'model'), \
                                    'vendor': readFile(hd / 'vendor')}
    
    return d

# SCSI
def getSCSI(type):
    """Probes for a specific type of SCSI device(disk, cdrom, floppy or usb-storage).
       Returns a dictionary of dictionaries. Sample code:
          disks = getIDE('disk')
          sda = disks['sda']
          print sda['model'] # prints model name of first SCSI hard disk.
          print sda['vendor'] # prints vendor name of first SCSI hard disk.
    """
 
    # Based on scsi.h, scsi.c(kudzu) 
    # usb-storage is really just a disk
    # but on the usb bus. 
    type_map = {'disk': [0x00, 0x07, 0x0e], \
                'cdrom': [0x04, 0x05], \
                'floppy': [0x06], \
                'usb-storage': [0x00, 0x07, 0x0e] }             

    if type not in type_map.keys():
        raise UnknownTypeError, 'Unknown type'

    scsi_path = path('/sys/bus/scsi/devices')

    d = {}

    if scsi_path.exists():
        for s in scsi_path.listdir():
            if (s / 'type').exists() and \
                int(readFile(s / 'type')) in type_map[type]:

                dev = s.listdir('block:*')
            
                # block:<dev> exists
                if dev: 
                    dev = dev[0].realpath()
                else: # block exists
                    dev = (s / 'block').realpath()

                removable = dev.realpath() / 'removable'
                if type in ['disk']:
                    # Exclude removable drives, including usb cdrom/thumbdrive
                    # usb portable hardrive are not excluded here when type is
                    # 'disk'
                    if removable.exists() \
                        and int(readFile(removable)): continue

                    # Checks for usb devices that presents itself as scsi
                    # such as usb portable hardrive which removable=0
                    idx = (dev / 'device').realpath().find('usb')
                    if idx != -1: # part of the usb bus
                        usb = path((dev / 'device').realpath()[idx:])

                        # And yes, the block device matches back
                        if (path('/sys/bus/usb/devices') / usb / 'block').realpath().basename() == dev.basename():
                            continue
                        elif (path('/sys/bus/usb/devices') / usb / 'block:' + dev.basename()).realpath().basename() == dev.basename():
                            continue
 
                elif type in ['usb-storage']:
                    # Exclude non-removable disks if type is 'usb-storage'
                    # Removable=0 even when it is a usb portable hdd drives (those 
                    # mobile 2.5" or 3.5" drive)
                    if removable.exists() \
                       and not int(readFile(removable)) \
                       and (dev / 'device').realpath().find('usb') == -1: continue

                dev = dev.basename()
                d[dev] = {}
                d[dev]['vendor'] = readFile(s / 'vendor')
                d[dev]['model'] = readFile(s / 'model')
                    
    sys_block = path('/sys/block')
    cciss_dev = {}
    if sys_block.exists():
        # treating cciss as non-removable and disk type
        for s in sys_block.listdir('cciss!*'): 
            # Handle cciss!c0d0 in /sys/block
            dev = s.basename()
            if dev.find('cciss!') != -1:
                dev = dev.replace('!', os.sep)

            s = s / 'device'
            cciss_dev[dev] = {}
            cciss_dev[dev]['vendor'] = readFile(s / 'vendor')

            if (s / 'model').exists():
                cciss_dev[dev]['model'] = readFile(s / 'model')
            elif (s / 'device').exists():
                cciss_dev[dev]['model'] = readFile(s / 'device')
            else:
                cciss_dev[dev]['model'] = None

            if cciss_dev[dev]['vendor'] and cciss_dev[dev]['vendor'].startswith('0x'):
                vendor = cciss_dev[dev]['vendor'][2:].strip()
                pci = PCI([vendor])
                if pci.ids.has_key(vendor):
                    cciss_dev[dev]['vendor'] = pci.ids[vendor]['NAME']   

                    if cciss_dev[dev]['model'] and cciss_dev[dev]['model'].startswith('0x'):
                        device = cciss_dev[dev]['model'][2:].strip()
                        if pci.ids[vendor]['DEVICE'].has_key(device):
                            cciss_dev[dev]['model'] = pci.ids[vendor]['DEVICE'][device]['NAME']
   


    d.update(cciss_dev)
    return d 


