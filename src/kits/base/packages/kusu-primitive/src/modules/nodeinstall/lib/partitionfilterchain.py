#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from primitive.system.hardware.partitiontool import DiskProfile
from primitive.system.hardware.disk import Partition
# NEED TO PORT 
from primitive.nodeinstall.defaults import setupDiskProfile
# XXX
from primitive.nodeinstall.nodeinstall import NodeInstInfoHandler
from primitive.nodeinstall.errors import EmptyNIISource, InvalidPartitionSchema
from primitive.core.errors import ModuleException
import primitive.support.log
logger = logger = primitive.support.log.getPrimitiveLog('nodeinstall.PartFilterChain')


def translateBoolean(value):
    """ Tries to translate value into boolean"""
    try:
        if not value: return False
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
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
    try:
        if value.strip():
            return value
        else:
            return None
    except AttributeError:
        return None

def translateFSTypes(fstype):
    """ Translates fstype to something partitiontool can understand. Right now
        only swap fstypes needs to be translated, the rest can be passed through.
    """
    if fstype == None or fstype.strip() == '': return None
    elif fstype == 'swap': return 'linux-swap'
    else: return fstype

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
    if not options: return (False, None)
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

    def apply(self, partition_entries, disk_profile):
        disk_profile = self.prefilter(partition_entries, disk_profile)
        for filter in self.filter_list:
            disk_profile = filter.apply(partition_entries, disk_profile)
            logger.debug('%s filter, diskprofile:\n%s' % (filter.__class__.__name__, str(disk_profile))) 
        disk_profile = self.postfilter(partition_entries, disk_profile)
        return disk_profile


class PartitionEntriesFilterChainDefaultPreserve(PartitionEntriesFilterChain):
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



class PartitionEntriesFilter(object):
    def apply(self, partition_entries, disk_profile):
        return disk_profile


class FilterOnMountpoints(PartitionEntriesFilter):
    def apply(self, partition_entries, disk_profile):
        for partinfo in partition_entries:
            mountpoint = translateMntPnt(partinfo['mntpnt'])
            preserve = partinfo['preserve']
            disk_profile = self.applyPreservation(mountpoint, preserve, disk_profile)
        return disk_profile

    def applyPreservation(self, mountpoint, preserve, disk_profile):
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
        lv_entries = self.getLVEntries(partition_entries)
        for lv in lv_entries:
            name = lv['device']
            preserve = lv['preserve']
            disk_profile = self.applyPreservation(name, 
                                                  preserve, disk_profile)
        return disk_profile

    def getLVEntries(self, partition_entries):
        lv_entries = []
        for p in partition_entries:
            if translatePartitionOptions(p['options'], 'lv')[0]:
                lv_entries.append(p)
        return lv_entries

    def applyPreservation(self, lv_name, preserve, disk_profile):
        if not disk_profile.lv_dict.has_key(lv_name): return disk_profile

        vol = disk_profile.lv_dict[lv_name]
        if preserve == '0':
            vol.leave_unchanged = False
        else:
            vol.leave_unchanged = True        
        return disk_profile


class AssignMntPntForLV(FilterOnLogicalVolume):
    def apply(self, partition_entries, disk_profile):
        lv_entries = self.getLVEntries(partition_entries)
        for lv in lv_entries:
            name = lv['device']
            mntpnt = translateMntPnt(lv['mntpnt'])
            self.applyMountPoint(name, mntpnt, disk_profile)
        return disk_profile

    def applyMountPoint(self, lv_name, mntpnt, disk_profile):
        logger.debug('Applying mntpnt: %s for log vol: %s' % (mntpnt, lv_name))
        if not disk_profile.lv_dict.has_key(lv_name):
            logger.debug('Disk Profile object does not contain the LV: %s' % lv_name)
            return disk_profile

        lv = disk_profile.lv_dict[lv_name]
        lv.mountpoint = mntpnt
        disk_profile.mountpoint_dict[mntpnt] = lv


class FilterOnFileSystem(PartitionEntriesFilter):
    def getValidEntries(self, partition_entries):
        retVal = []
        for p in partition_entries:
            if p['device'] in 'nN' and translateFSTypes(p['fstype']):
                retVal.append(p)
        return retVal

    def apply(self, partition_entries, disk_profile):
        valid_entries = self.getValidEntries(partition_entries)
        for partinfo in valid_entries:
            fs = translateFSTypes(partinfo['fstype'])
            preserve = partinfo['preserve']
            if fs == 'physical volume':
                vg_name =  translatePartitionOptions(partinfo['options'], 'pv')[1]
                disk_profile = self.applyPreservation(fs, preserve, disk_profile, vg_name)
            else:
                disk_profile = self.applyPreservation(fs, preserve, disk_profile)
        return disk_profile

    def applyPreservation(self, fs, preserve, disk_profile, vg_name=''):
        vol_list = self.filterOnFS(fs, disk_profile)
        for vol in vol_list:
            if preserve == '0':
                vol.leave_unchanged = False
                logger.debug('Unpreserve %s' % vol.path)
            else:
                vol.leave_unchanged = True
                logger.debug('Preserve %s' % vol.path)
        return disk_profile

    def filterOnFS(self, fs, disk_profile):
        all_vols = self.getAllVolumes(disk_profile)
        if not all_vols:
            logger.debug('No Volumes')
            return []
        retVal = []
        logger.debug('filtering on FS...')
        for vol in all_vols:
            logger.debug('vol: %s type: %s' % (vol.path, str(type(vol))))
            if fs == 'physical volume' and type(vol) == Partition and vol.lvm_flag:
                retVal.append(vol)
            if vol.fs_type == fs:
                retVal.append(vol)
        return retVal

    def getAllVolumes(self, disk_profile):
        all_vols = disk_profile.lv_dict.values()
        for disk in disk_profile.disk_dict.values():
            all_vols += disk.partition_dict.values()
            logger.debug('Disk: %s has partitions %s' % (disk.path, str(disk.partition_dict.keys())))
        logger.debug('All Volumes: %s' % all_vols)
        return all_vols

class FilterOnPartitionType(PartitionEntriesFilter):
    def apply(self, partition_entries, disk_profile):
        p_list = self.getAffectedPartitions(partition_entries)
        for p in p_list:
            p_id, p_type = translatePartitionOptions(p['options'], 'partitionID')
            preserve = p['preserve']
            disk_profile = self.applyPreservation(p_type, preserve, disk_profile)
        return disk_profile

    def getAffectedPartitions(self, partition_entries):
        retVal = []
        for p in partition_entries:
            p_id_flag, name = translatePartitionOptions(p['options'], 'partitionID')
            if p_id_flag:
                retVal.append(p)
        return retVal

    def applyPreservation(self, p_type, preserve, disk_profile):
        p_list = self.getPartitionsOfType(p_type, disk_profile)
        for p in p_list:
            if preserve == '0':
                p.leave_unchanged = False
                logger.debug('Unpreserve %s' % p.path)
            else:
                p.leave_unchanged = True
                logger.debug('Preserve %s' % p.path)
        return disk_profile

    def getPartitionsOfType(self, p_type, disk_profile):
        retVal = []
        for disk in disk_profile.disk_dict.values():
            for partition in disk.partition_dict.values():
                if partition.native_type == p_type:
                    logger.debug('PType: %s, fs: %s, partition: %s' % (p_type, partition.fs_type, partition.path))
                    retVal.append(partition)
        return retVal


class PartitionEntriesFilterChainDefaultNoPreserve(PartitionEntriesFilterChain):
    def prefilter(self, partition_entries, disk_profile):
        """Set the leave_unchanged flag to False for all volumes."""
        for disk in disk_profile.disk_dict.values():
            for partition in disk.partition_dict.values():
                partition.leave_unchanged = False

        for lv in disk_profile.lv_dict.values():
            lv.leave_unchanged = False
        logger.debug('%s prefilter, diskprofile:\n%s' % (self.__class__.__name__, str(disk_profile))) 
        return disk_profile

    def postfilter(self, partition_entries, disk_profile):
        return disk_profile


class FilterOnMountpointsNoPreserve(FilterOnMountpoints):
    def applyPreservation(self, mountpoint, preserve, disk_profile):
        if mountpoint and mountpoint in disk_profile.mountpoint_dict.keys():
            vol = disk_profile.mountpoint_dict[mountpoint]
            if preserve == '1':
                vol.leave_unchanged = True
                logger.debug('Unpreserve %s' % vol.path)
            else:
                vol.leave_unchanged = False
                logger.debug('Preserve %s' % vol.path)
        return disk_profile


class FilterOnLogicalVolumeNoPreserve(FilterOnLogicalVolume):
    def apply(self, partition_entries, disk_profile):
        for lv in disk_profile.lv_dict.values():
            lv.leave_unchanged = False
        lv_entries = self.getLVEntries(partition_entries)
        for lv in lv_entries:
            name = lv['device']
            preserve = lv['preserve']
            disk_profile = self.applyPreservation(name, 
                                                  preserve, disk_profile)
        return disk_profile

    def applyPreservation(self, lv_name, preserve, disk_profile):
        if not disk_profile.lv_dict.has_key(lv_name): return disk_profile

        vol = disk_profile.lv_dict[lv_name]
        if preserve == '1':
            vol.leave_unchanged = True
            logger.debug('Preserve %s' % vol.path)
        else:
            vol.leave_unchanged = False
            logger.debug('Unpreserve %s' % vol.path)
        return disk_profile


class FilterOnFileSystemNoPreserve(FilterOnFileSystem):
    def applyPreservation(self, fs, preserve, disk_profile, vg_name=''):
        vol_list = self.filterOnFS(fs, disk_profile)
        for vol in vol_list:
            if fs=='physical volume':
                pv = disk_profile.pv_dict[vol.path]
                self.applyForPhysicalVol(vg_name, pv, preserve)
            else:
                self.applyForFS(vol, preserve)
        return disk_profile

    def applyForPhysicalVol(self, vg_name, vol, preserve):
        if vol.group and vol.group.name==vg_name and preserve=='1':
            vol.partition.leave_unchanged = True
            logger.debug('Preserve %s' % vol.partition.path)
        else:
            vol.partition.leave_unchanged = False
            logger.debug('Preserve %s' % vol.partition.path)

    def applyForFS(self, vol, preserve):
        if preserve == '1':
            vol.leave_unchanged = True
            logger.debug('Preserve %s' % vol.path)
        else:
            vol.leave_unchanged = False
            logger.debug('Unpreserve %s' % vol.path)
 

class FilterOnPartitionTypeNoPreserve(FilterOnPartitionType):
    def applyPreservation(self, p_type, preserve, disk_profile):
        p_list = self.getPartitionsOfType(p_type, disk_profile)
        for p in p_list:
            if preserve == '1':
                p.leave_unchanged = True
                logger.debug('Preserve %s' % p.path)
            else:
                p.leave_unchanged = False
                logger.debug('Unpreserve %s' % p.path)
        return disk_profile
