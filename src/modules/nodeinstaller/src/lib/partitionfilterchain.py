#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.partitiontool import DiskProfile
from kusu.partitiontool.disk import Partition
from kusu.installer.defaults import setupDiskProfile
#from kusu.nodeinstaller import NodeInstInfoHandler
from kusu.util.errors import EmptyNIISource, InvalidPartitionSchema, KusuError, MountFailedError
import kusu.util.log as kusulog

logger = kusulog.getKusuLog('nodeinstaller.NodeInstaller')

def translateBoolean(value):
    """ Tries to translate value into boolean"""
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    try:
        if int(value) > 0:
            return True
        else:
            return False
    except ValueError:
        return False
 
def translatePartitionNumber(value):
    """ Translate NII partition number which is a string into
        partitiontool partition number which is an integer
    """
    try:
        retVal = int(value)
    except ValueError:
        if value.strip().lower() == 'n':
            return 'N'
        retVal = 0
    return retVal

def translatePartitionSize(value):
    """ Translate NII partition size which is a string into
        partitiontool partition size which is an integer
    """
    return int(value)

def translateMntPnt(value):
    """ Check if mountpoint is an empty string - translate into None if yes. """
    if value.strip():
        return value
    else:
        return None

def translateFSTypes(fstype):
    """ Translates fstype to something partitiontool can understand. Right now
        only swap fstypes needs to be translated, the rest can be passed through.
    """

    if fstype == 'swap':
        return 'linux-swap'
    elif fstype.strip() == '':
        return None
    else:
        return fstype

def translatePartitionOptions(options, opt):
    """ Translate the options line for the opt value. This method returns
        a tuple (x,y). The first tuple element is a boolean, True if the 
        opt value exists, False if otherwise. The second element is data 
        that is specific to the opt value.

        PARTITION_OPTIONS = [ 'fill', 'pv', 'vg', 'lv', 'label', 
                            'preserve', 'extent']

        An example partitionopts line looks like the following:
            fill;label='My Volume';preserve

        An example partitionopts line for a LVM Volume Group can be defined
        as follows, note that the name of the Volume Group should be defined
        in the device column in the partitions table:
            vg;extent=32M

        An example partitionopts for a LVM Logical Volume can be defined 
        as follows, it needs to belong to a Volume Group, note that the name 
        of the Volume Group will be matched against the device name of an 
        existing Volume Group definition:
            lv;vg=VolGroup00

        An example partitionopts for a LVM Physical Volume can be defined 
        as follows, note that the name  of the Volume Group will be matched 
        against the device name of an existing Volume Group definition:
            pv;vg=VolGroup00    
    """
    optionlist = options.split(';')
    opt_dict = {}
    if optionlist:
        for i in optionlist:
            try:
                opt_dict[i.split('=')[0]] = i.split('=')[1]
            except IndexError:
                opt_dict[i.split('=')[0]] = None

    # fill
    if opt == 'fill' and opt not in opt_dict.keys():
        return (False,None)
        
    if opt == 'fill' and opt in opt_dict.keys():
        return (True,None)

    # extent
    if opt == 'extent' and opt not in opt_dict.keys():
        return (False,None)
        
    if opt == 'extent' and opt in opt_dict.keys():
        return (True,opt_dict[opt])
        
    # label
    if opt == 'label' and opt not in opt_dict.keys():
        return (False,None)

    if opt == 'label' and opt in opt_dict.keys():
        return (True,opt_dict[opt])
        
    # vg
    if opt == 'vg':
        if 'vg' in opt_dict.keys()  and 'extent' in opt_dict.keys():
            return (True, opt_dict['extent'])
        else:
            return (False, None)

    # pv
    if opt == 'pv':
        if 'pv' in opt_dict.keys() and 'vg' in opt_dict.keys():
            return (True, opt_dict['vg'])
        else:
            return (False,None)
        
    # lv
    if opt == 'lv':
        if 'lv' in opt_dict.keys() and 'vg' in opt_dict.keys():
            return (True, opt_dict['vg'])
        else:
            return (False, None)

    # partition ID
    if opt == 'partitionID' and opt not in opt_dict.keys():
        return (False, None)
    if opt == 'partitionID' and opt in opt_dict.keys():
        return (True, opt_dict[opt])


class PartitionEntriesFilterChain(object):
    def __init__(self, filter_list=[]):
        self.filter_list = filter_list

    def prefilter(self, partition_entries, disk_profile):
        """Set the leave_unchanged flag to true for all volumes."""
        for disk in disk_profile.disk_dict.values():
            for partition in disk.partition_dict.values():
                if partition.type != 'extended':
                    partition.leave_unchanged = True

        for lv in disk_profile.lv_dict.values():
            lv.leave_unchanged = True
 
        return disk_profile

    def postfilter(self, partition_entries, disk_profile):
        return disk_profile

    def apply(self, partition_entries, disk_profile):
        disk_profile = self.prefilter(partition_entries, disk_profile)
        for filter in self.filter_list:
            disk_profile = filter.apply(partition_entries, disk_profile)
        disk_profile = self.postfilter(partition_entries, disk_profile)
        return disk_profile


class PartitionEntriesFilter(object):
    def apply(self, partition_entries, disk_profile):
        return disk_profile


class FilterOnMountpoints(PartitionEntriesFilter):
    def apply(self, partition_entries, disk_profile):
        for partinfo in partition_entries:
            mountpoint = translateMntPnt(partinfo['mntpnt'])
            preserve = partinfo['preserve']
            disk_profile = self.__applyPreservation(mountpoint, preserve, disk_profile)
        return disk_profile

    def __applyPreservation(self, mountpoint, preserve, disk_profile):
        if mountpoint and mountpoint in disk_profile.mountpoint_dict.keys():
            vol = disk_profile.mountpoint_dict[mountpoint]
            if preserve == '0':
                vol.leave_unchanged = False
                logger.debug('Unpreserve %s' % vol.path)
            else:
                vol.leave_unchanged = True
                logger.debug('Preserve %s' % vol.path)
        return disk_profile


class FilterOnLogicalVolume(PartitionEntriesFilter):
    def apply(self, partition_entries, disk_profile):
        lv_entries = self.__getLVEntries(partition_entries)
        for lv in lv_entries:
            name = lv['device']
            preserve = lv['preserve']
            disk_profile = self.__applyPreservation(name, preserve, disk_profile)
        return disk_profile

    def __getLVEntries(self, partition_entries):
        lv_entries = []
        for p in partition_entries:
            if translatePartitionOptions(p['options'], 'lv')[0]:
                lv_entries.append(p)
        return lv_entries

    def __applyPreservation(self, lv_name, preserve, disk_profile):
        if not disk_profile.lv_dict.has_key(lv_name): return disk_profile

        vol = disk_profile.lv_dict[lv_name]
        if preserve == '0':
            vol.leave_unchanged = False
        else:
            vol.leave_unchanged = True        
        return disk_profile

class FilterOnFileSystem(PartitionEntriesFilter):
    def __getValidEntries(self, partition_entries):
        retVal = []
        for p in partition_entries:
            if p['device'] in 'nN' and translateFSTypes(p['fstype']):
                retVal.append(p)
        return retVal

    def apply(self, partition_entries, disk_profile):
        valid_entries = self.__getValidEntries(partition_entries)
        for partinfo in valid_entries:
            fs = translateFSTypes(partinfo['fstype'])
            preserve = partinfo['preserve']
            disk_profile = self.__applyPreservation(fs, preserve, disk_profile)
        return disk_profile

    def __applyPreservation(self, fs, preserve, disk_profile):
        vol_list = self.__filterOnFS(fs, disk_profile)
        for vol in vol_list:
            if preserve == '0':
                vol.leave_unchanged = False
                logger.debug('Unpreserve %s' % vol.path)
            else:
                vol.leave_unchanged = True
                logger.debug('Preserve %s' % vol.path)
        return disk_profile

    def __filterOnFS(self, fs, disk_profile):
        all_vols = self.__getAllVolumes(disk_profile)
        if not all_vols: return []
        retVal = []
        for vol in all_vols:
            if vol.fs_type == fs:
                retVal.append(vol)
        return retVal

    def __getAllVolumes(self, disk_profile):
        all_vols = disk_profile.lv_dict.values()
        for disk in disk_profile.disk_dict.values():
            all_vols += disk.partition_dict.values()


class FilterOnPartitionType(PartitionEntriesFilter):
    def apply(self, partition_entries, disk_profile):
        p_list = self.__getAffectedPartitions(partition_entries)
        for p in p_list:
            p_id, p_type = translatePartitionOptions(p['options'], 'partitionID')
            preserve = p['preserve']
            disk_profile = self.__applyPreservation(p_type, preserve, disk_profile)
        return disk_profile

    def __getAffectedPartitions(self, partition_entries):
        retVal = []
        for p in partition_entries:
            p_id_flag, name = translatePartitionOptions(p['options'], 'partitionID')
            if p_id_flag:
                retVal.append(p)
        return retVal

    def __applyPreservation(self, p_type, preserve, disk_profile):
        p_list = self.__getPartitionsOfType(p_type, disk_profile)
        for p in p_list:
            if preserve == '0':
                p.leave_unchanged = False
                logger.debug('Unpreserve %s' % p.path)
            else:
                p.leave_unchanged = True
                logger.debug('Preserve %s' % p.path)
        return disk_profile

    def __getPartitionsOfType(self, p_type, disk_profile):
        retVal = []
        for disk in disk_profile.disk_dict.values():
            for partition in disk.partition_dict.values():
                if partition.native_type == p_type:
                    logger.debug('PType: %s, fs: %s, partition: %s' % (p_type, partition.fs_type, partition.path))
                    retVal.append(partition)
        return retVal
