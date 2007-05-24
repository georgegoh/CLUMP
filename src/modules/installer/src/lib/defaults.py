#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import kusu.util.log as kusulog
from kusu.util.errors import *

from path import path

logger = kusulog.getKusuLog('installer.defaults')

def setupDiskProfile(disk_profile, schema=None):
    """Set up a disk profile based on a given schema."""
    # check that no partitions have been created.
    for disk in disk_profile.disk_dict.itervalues():
        if disk.partition_dict:
            raise DiskProfileNotEmptyError, 'Disk Profile is not empty.'
    # check for consistency in LVM dicts.
    if disk_profile.pv_dict or disk_profile.lvg_dict or disk_profile.lv_dict:
        raise DiskProfileNotEmptyError, 'LVM entities still exist.'

    if not schema:
        return True
    else: # do the schema stuff.
        pass
