#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.hardware import drive, net

def getDisks():
    """Probes for a disk type device. CDROMs and portable
       usb storage devices(flash drives/portable hardisks) 
       are not included.

       Returns a dictionary of dictionaries. Sample code:
          disks = getDisks()
          hda = disks['hda']
          print hda['model'] # prints model name of first IDE hard disk.
    """
 
    d = drive.getIDE('disk')
    d.update(drive.getSCSI('disk'))

    return d

def getCDROM():
    """Probes for cdrom devices.

       Returns a dictionary of dictionaries. Sample code:
            cdroms = getCDROM()
            hdc = cdroms['hdc']
            print hdc['model'] # prints model name of cdrom.
    """

    d = drive.getIDE('cdrom')
    d.update(drive.getSCSI('cdrom'))

    return d

def getPortableUSB():
    """Returns a dictionary of portable usb storage disks

       Returns a dictionary of dictioanries. Sample code:
            usbs = getPortableUSB()
            sdb = usbs['sdb']
            print sdb['model'] # prints model name of usb flash drive
    """
    return drive.getSCSI('usb-storage')

def getAllDisks():
    """Returns a dictionary of all disks"""

    d = getDisks()
    d.update(getPortableUSB())

    return d

def getAllInterfaces():
    """Returns a dictionary of all network interfaces"""
    return net.getAllInterfaces()

def getPhysicalInterfaces():
    """Returns a dictionary of all physical network interfaces"""
    return net.getPhysicalInterfaces()
