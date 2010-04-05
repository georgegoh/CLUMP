#!/usr/bin/env python
#
# $Id$
#
# Original Author: Tsai Li Ming (ltsai@osgdc.org)
# Adapted by: George Goh (ggoh@osgdc.org)
#
# Copyright 2008 Platform Computing Inc.
#
import os
import re
from path import path
from primitive.system.hardware import net
from primitive.system.hardware.pci import PCI
from primitive.support.type import Struct
from primitive.core.errors import UnknownTypeError

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

def getDisks():
    """Probes for a disk type device. CDROMs and portable
       usb storage devices(flash drives/portable hardisks) 
       are not included.

       Returns a dictionary of dictionaries. Sample code:
          disks = getDisks()
          hda = disks['hda']
          print hda['model'] # prints model name of first IDE hard disk.
    """
 
    d = getIDE('disk')
    d.update(getSCSI('disk'))

    return d

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
                if type == 'disk':
                    d[hd.basename()]['partitions'] = getIDEPartitions(hd.basename())
    
    return d

def getIDEPartitions(dev):
    partitions = []
    p = getIDEDriveSysPath(dev)
    if p:
        blkdir = p.listdir('block:*')[0]
        partitions = [x.basename() for x in blkdir.listdir(dev + '*')]
    return partitions

def getIDEDriveSysPath(dev):
    ide_path = path('/sys/bus/ide/devices')
    if ide_path.exists():
        for p in ide_path.listdir():
            if (p / 'drivename').exists() and readFile(p / 'drivename') == dev:
                return p
    return None

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
                elif (s / 'block').exists(): # block exists, rhel4
                    dev = (s / 'block').realpath()
                else:
                    continue

                removable = dev.realpath() / 'removable'
                if type in ['disk']:
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
                    # Do not list non-USB devices
                    if (dev / 'device').realpath().find('usb') == -1: continue
                    # Do not list non removable devices
                    if removable.exists() and not int(readFile(removable)): continue

                device = dev.basename()
                if type in ['cdrom']:
                    # takes care of 50-udev.rules: 
                    # rename sr* to scd*
                    # KERNEL=="sr[0-9]*", BUS=="scsi", NAME="scd%n"

                    pat = re.compile('[0-9]+$')
                    device = dev.basename()

                    if device.startswith('sr'):
                        sr_num = pat.findall(device)[0]
                        scd_device = 'scd' + sr_num
                        if not (path('/dev/') / device).exists() and \
                            (path('/dev/') / scd_device).exists():
                            device = scd_device

                d[device] = {}
                d[device]['vendor'] = readFile(s / 'vendor')
                d[device]['model'] = readFile(s / 'model')
                if type == 'disk':
                    d[device]['partitions'] = getSCSIPartitions(dev)
                
    if type == 'disk':    
        sys_block = path('/sys/block')
        cciss_dev = {}
        if sys_block.exists():
            # treating cciss as non-removable and disk type
            for s in sys_block.listdir('cciss!*'): 
                # Handle cciss!c0d0 in /sys/block
                dev = s.basename()
                if dev.find('cciss!') != -1:
                    dev = dev.replace('!', os.sep)

                cciss_dev[dev] = CCISSDiskHandler(s)

        d.update(cciss_dev)
    return d 

def getSCSIPartitions(path):
    """Retrieves a list of partitions."""
    partitions = []
    if str(path) == '/': return partitions
    for p in path.listdir():
        p_name = p.basename()
        if p_name.startswith(path.basename()):
            partitions.append(p_name)
    return partitions


def CCISSDiskHandler(path):
    """Handles CCISS disks."""
    cciss_dev = Struct(model=None)
    d_path = path / 'device'

    cciss_dev.partitions = getCCISSPartitions(path)

    cciss_dev.vendor = readFile(d_path / 'vendor')
    if not cciss_dev.vendor:
        return dict(cciss_dev)

    if (d_path / 'model').exists():
        cciss_dev.model = readFile(d_path / 'model')
    elif (d_path / 'device').exists():
        cciss_dev.model = readFile(d_path / 'device')

    if cciss_dev.vendor.startswith('0x'):
        vendor = cciss_dev.vendor[2:].strip()
        pci = PCI([vendor])
        if pci.ids.has_key(vendor):
            cciss_dev.vendor = pci.ids[vendor]['NAME']

            if cciss_dev.model and cciss_dev.model.startswith('0x'):
                device = cciss_dev.model[2:].strip()
                if pci.ids[vendor]['DEVICE'].has_key(device):
                    cciss_dev.model = pci.ids[vendor]['DEVICE'][device]['NAME']
                else:
                    cciss_dev.model = None
            else:
                cciss_dev.vendor = None
                cciss_dev.model = None

    return dict(cciss_dev)

def getCCISSPartitions(path):
    """Return a list of partitions in a CCISS disk."""
    partitions = []
    if str(path) == '/': return partitions
    for p in path.listdir():
        p_name = p.basename()
        if p_name.startswith(path.basename()):
            if p_name.find('cciss!') != -1:
                p_name = p_name.replace('!', os.sep)
            partitions.append(p_name)
    return partitions

def getAllInterfaces():
    """Returns a dictionary of all network interfaces"""
    return net.getAllInterfaces()

def getPhysicalInterfaces():
    """Returns a dictionary of all physical network interfaces"""
    return net.getPhysicalInterfaces()

def getCDROM():
    """Probes for cdrom devices.

       Returns a dictionary of dictionaries. Sample code:
            cdroms = getCDROM()
            hdc = cdroms['hdc']
            print hdc['model'] # prints model name of cdrom.
    """

    d = getIDE('cdrom')
    d.update(getSCSI('cdrom'))

    return d
