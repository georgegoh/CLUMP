#!/usr/bin/env python
# $Id: common.py 476 2008-01-25 12:36:55Z hirwan $
#
# Kusu Text Installer Partition Tool.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import parted

fsTypes = {}
fs_type = parted.file_system_type_get_next ()
while fs_type:
    fsTypes[fs_type.name] = fs_type
    fs_type = parted.file_system_type_get_next (fs_type)

diskFlags = {
    'FIRST_FLAG' : parted.PARTITION_FIRST_FLAG,
    'LAST_FLAG' : parted.PARTITION_LAST_FLAG,
}

partitionTypes = {
    'PRIMARY' : parted.PARTITION_PRIMARY,
    'EXTENDED' : parted.PARTITION_EXTENDED,
    'LOGICAL' : parted.PARTITION_LOGICAL,
    'FREESPACE' : parted.PARTITION_FREESPACE,
    'METADATA' : parted.PARTITION_METADATA
}

partitionFlags = {
    'BOOT' : parted.PARTITION_BOOT,
    'ROOT' : parted.PARTITION_ROOT,
    'SWAP' : parted.PARTITION_SWAP,
    'HIDDEN' : parted.PARTITION_HIDDEN,
    'RAID' : parted.PARTITION_RAID,
    'LVM' : parted.PARTITION_LVM,
    'LBA' : parted.PARTITION_LBA,
    'HPSERVICE' : parted.PARTITION_HPSERVICE,
    'PALO' : parted.PARTITION_PALO,
    'PREP' : parted.PARTITION_PREP,
    'MSFT_RESERVED' : parted.PARTITION_MSFT_RESERVED
}


def getPartitions(disk_path):
    import commands
    fdisk_output = commands.getoutput('fdisk -l %s' % disk_path)
    return parseFdisk(fdisk_output)


def parseFdisk(fdisk_output):
    """Parse the output of an fdisk command where the command is:
       'fdisk -l /dev/XXX'.
       Returns a dictionary of info about the partitions on the disk,
       where the key is the path to the partitions.
    """
    result = {}
    for line in fdisk_output.split('\n'):
        if not line.startswith('/'): continue
        parts = line.split()

        inf = {}
        if parts[1] == '*':
            inf['bootable'] = True
            del parts[1]
        else:
            inf['bootable'] = False

        inf['start'] = int(parts[1])
        inf['end'] = int(parts[2])
        inf['blocks'] = int(parts[3].rstrip('+'))
        inf['partition_id'] = int(parts[4], 16)
        inf['partition_id_string'] = ' '.join(parts[5:])

        result[parts[0]] = inf
    return result
