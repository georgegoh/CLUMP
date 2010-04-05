#!/usr/bin/env python
# $Id: grub.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
def generateDeviceMapEntries(diskProfile):
    disk_order = diskProfile.getBIOSDiskOrder()
    out = []
    for i,d in enumerate(disk_order):
        out.append('(hd%d)\t/dev/%s' % (i,d))
    return out
