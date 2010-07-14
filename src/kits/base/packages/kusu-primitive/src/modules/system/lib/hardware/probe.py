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
import subprocess
from path import path
from primitive.system.hardware import net
from primitive.system.hardware import nodes
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


def getPartitions():
    disks = getDisks()
    part_dict = Struct()
    mntpnts = getMountpoints()
    for k,v in disks.iteritems():
        sys_path = path('/sys/block') / k
        if v['label'] == 'loop':
            dev_path = str(path('/dev') / k)
            mntpnt = mntpnts.get(dev_path, Struct(mntpnt='', fstype=''))
            size = getDevSize(sys_path)
            part_dict[dev_path] = Struct(size=size)
            part_dict[dev_path].update(mntpnt)
        else:
            for p in v['partitions']:
                sys_path = path('/sys/block/') / k / p
                dev_path = str(path('/dev') / p)
                mntpnt = mntpnts.get(dev_path, Struct(mntpnt='', fstype=''))
                size = getDevSize(sys_path)
                part_dict[dev_path] = Struct(size=size)
                part_dict[dev_path].update(mntpnt)
    return part_dict
    

def getLVMPhysicalVolumes():
    p = subprocess.Popen(['lvm', 'pvs', '--units', 'b'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    # return empty struct on failure
    if p.wait():
        return Struct()

    pvs = p.stdout.readlines()
    # output includes one line of headers, return empty struct if
    # no other output exists.
    if len(pvs) <= 1:
        return Struct()

    # ignore first line of headers, and tidy up the output.
    pvs = pvs[1:]
    pvs = [l.strip() for l in pvs]

    o = Struct()
    for l in pvs:
        # acceptable output is 'lv_name vg_name lvm_opts size'(4 elements)
        if len(l.split()) != 6:
            continue
        (pv_path, vg_name, fmt, attr, size, free) = l.split()
        o[pv_path] = Struct(vg=vg_name, fmt=fmt, attr=attr,
                            size=long(size[:-1]), free=long(free[:-1]))
    return o


def getLVMLogicalVolumes():
    """Probes for Logical Volumes on the system.
       Output format:
          Struct(python dictionary-compatible)
       Sample output:
          >>> lvs = getLVMLogicalVolumes()
          >>> print lvs
          Struct({'VAR': Struct({'vg': 'KusuVolGroup00',
                                 'options': '-wi-ao',
                                 'size': '1.97G'})})
          >>> print lvs.VAR.size
          '1.97G'
          >>> print lvs['VAR']['size']
          '1.97G'
    """
    p = subprocess.Popen(['lvm', 'lvs', '--units', 'b'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    # return empty struct on failure
    if p.wait():
        return Struct()

    lvs = p.stdout.readlines()
    # output includes one line of headers, return empty struct if
    # no other output exists.
    if len(lvs) <= 1:
        return Struct()

    # ignore first line of headers, and tidy up the output.
    lvs = lvs[1:]
    lvs = [l.strip() for l in lvs]

    o = Struct()
    mntpnts = getMountpoints()
    for l in lvs:
        # acceptable output is 'lv_name vg_name lvm_opts size'(4 elements)
        if len(l.split()) != 4:
            continue
        (lv_name, vg_name, lvm_opts, size) = l.split()
        lv_path = path('/dev') / vg_name / lv_name
        mntpnt = mntpnts.get(str(lv_path), Struct(mntpnt='', fstype=''))
        o[lv_name] = Struct(vg=vg_name, options=lvm_opts, size=long(size[:-1]))
        o[lv_name].update(mntpnt)
    return o



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
                    import parted
                    d[hd.basename()]['partitions'] = getIDEPartitions(hd.basename())
                    devpath = path('/dev/') / hd.basename()
                    nodes.checkAndMakeNode(devpath)
                    if devpath.exists():
                        try:
                            pedDevice = parted.PedDevice.get(devpath)
                            d[hd.basename()]['label'] = pedDevice.disk_probe().name
                        except:
                            pass
    
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
                    import parted
                    d[device]['partitions'] = getSCSIPartitions(dev)
                    devpath = path('/dev/') / device
                    nodes.checkAndMakeNode(devpath)
                    if devpath.exists():
                        try:
                            pedDevice = parted.PedDevice.get(devpath)
                            d[device]['label'] = pedDevice.disk_probe().name
                            d[device]['size'] = getDevSize(dev)
                        except:
                            pass

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

def getMountpoints(fstab='/etc/fstab'):
    rv = Struct()
    fstab = path(fstab)
    if not fstab.exists():
        return rv

    f = fstab.open()
    lines = [l.strip() for l in f.readlines()]
    lines = [l for l in lines if l[0] != '#']
    for l in lines:
        if len(l.split()) > 3:
            (dev, mntpnt, fstype, opts) = l.split(None, 3)
            rv[dev] = Struct(mntpnt=mntpnt, fstype=fstype)
    return rv


def getDevSize(dev_path):
    """Retrieves the size of a device."""
    BLK_SIZE = 512
    p = path(dev_path) / 'size'
    if not p.exists:
        return 0

    f = p.open()
    size = f.read()
    if not size:
        return 0

    size = size.strip()
    return long(size) * BLK_SIZE


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
