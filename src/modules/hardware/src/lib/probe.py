#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
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
    """Returns a dictionary of disks """
    #d = drive.getIDE('cdrom')
    #d.update(drive.getSCSI('cdrom'))
    pass

def getPortableUSB():
    """Returns a dictionary of portable usb storage disks"""
    pass

def getAllInterfaces():
    """Returns a dictionary of all network interfaces"""
    return net.getAllInterfaces()

def getPhysicalInterfaces():
    """Returns a dictionary of all physical network interfaces"""
    return net.getPhysicalInterfaces()
