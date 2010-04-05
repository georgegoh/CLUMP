#!/usr/bin/env python
# $Id: disk_utils.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Kusu Text Installer Utility functions.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import struct
import random

def isDiskOrderAmbiguous(disk_profile):
    """
    Make sure the first disk has a unique MBR signature in the system.
    If it does not, then we cannot be certain that we have got the
    first disk order correct - we need to check with the user.
    """
    disk_order = disk_profile.getBIOSDiskOrder()
    disk0 = disk_profile.disk_dict[disk_order[0]]
    disk0_mbrsig = disk0.mbr_signature

    duplicates = []
    for k in disk_order[1:]:
        d = disk_profile.disk_dict[k]
        if d.mbr_signature == disk0.mbr_signature:
            duplicates.append(k)

    if duplicates:
        return True

    return False

def remarkMBRs(disk_profile):
    disk_order = disk_profile.getBIOSDiskOrder()
        
    mbrsig_to_disk_dict = {}
    for d in disk_profile.disk_dict.itervalues():
        mbrsig = d.mbr_signature
        if mbrsig in mbrsig_to_disk_dict.keys():
            mbrsig_to_disk_dict[mbrsig].append(d)
        else:
            mbrsig_to_disk_dict[mbrsig] = [d]

    # filter out only mbrsigs with duplicates.
    duplicates = [ x for x in mbrsig_to_disk_dict.values() if len(x) > 1 ]

    mbrsig_list = mbrsig_to_disk_dict.keys()
    for dups in duplicates:
        # keep the first item intact, change the duplicates of the first
        for d in dups[1:]:
            # generate the next key. Range doesn't matter, as long as it
            # falls within a 32-bit range and is greater than the maximum
            # possible number of disk devices in a system.
            next_key = random.randint(1,10000)
            while next_key in mbrsig_list:
                next_key = random.randint(1,10000)
            try:
                fh = open(d.path, 'r+')
                fh.seek(d.MBRSIG_OFFSET)
                s = struct.pack('I', next_key)
                fh.write(s)
            finally:
                fh.close()

            mbrsig_list.append(next_key)

