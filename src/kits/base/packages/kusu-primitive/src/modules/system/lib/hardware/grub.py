#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
def generateDeviceMapEntries(diskProfile):
    disk_order = diskProfile.getBIOSDiskOrder()
    out = []
    for i,d in enumerate(disk_order):
        out.append('(hd%d)\t/dev/%s' % (i,d))
    return out
