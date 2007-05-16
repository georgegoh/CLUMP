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
    d = drive.getIDE('disk')
    d.update(drive.getSCSI('disk'))

    return d

def getCDROM():
    #d = drive.getIDE('cdrom')
    #d.update(drive.getSCSI('cdrom'))
    pass

def getPortableUSB():
    pass

def getAllInterfaces():
    pass

def getPhysicalInterfaces():
    pass
