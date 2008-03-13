#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

from kusu.partitiontool import DiskProfile
from kusu.partitiontool.disk import Partition
from kusu.nodeinstaller import NodeInstInfoHandler
from kusu.util.errors import *
from kusu.nodeinstaller.partitionfilterchain import *
from os.path import basename
from pprint import PrettyPrinter
import kusu.util.log as kusulog
logger = kusulog.getKusuLog('nodeinstaller.NodeInstaller')


def partitionRulesDefaultIsPreserve(rules):
    preserve = False
    for p in rules:
        logger.debug('Checking part_rule for partitionID=*')
        p_id, value = translatePartitionOptions(p['options'], 'partitionID')
        if p_id and value=='*':
            if p['preserve'] == '0':
                logger.debug('Default Preserve set to False(User defined).')
                preserve = False
    return preserve


def adaptNIIPartition(niipartition, diskprofile):
    """ Adapt niipartition into a partitiontool schema. This schema can
        be passed along with a partitiontool diskprofile to setupDiskProfile
        method.

    """
    part_rules = niipartition.values()
    default_preserve = partitionRulesDefaultIsPreserve(part_rules)

    if default_preserve:
        logger.debug('Default Preserve')
        pefc = PartitionEntriesFilterChainDefaultPreserve()
        pefc.filter_list.append(FilterOnFileSystem())
        pefc.filter_list.append(FilterOnPartitionType())
        pefc.filter_list.append(FilterOnLogicalVolume())
        pefc.filter_list.append(FilterOnMountpoints())
        pefc.filter_list.append(AssignMntPntForLV())
    else:
        logger.debug('Default No Preserve')
        pefc = PartitionEntriesFilterChainDefaultNoPreserve()
        pefc.filter_list.append(AssignMntPntForLV())
        pefc.filter_list.append(FilterOnMountpointsNoPreserve())
        pefc.filter_list.append(FilterOnLogicalVolumeNoPreserve())
        pefc.filter_list.append(FilterOnPartitionTypeNoPreserve())
        pefc.filter_list.append(FilterOnFileSystemNoPreserve())

    disk_profile = pefc.apply(part_rules, diskprofile)
    logger.debug('Before cleaning diskprofile:\n%s' % str(disk_profile))
    cleanDiskProfile(disk_profile)
    logger.debug('After cleaning diskprofile:\n%s' % str(disk_profile))

    pp = PrettyPrinter()
    logger.debug('Creating schema using rules:\n%s' % pp.pformat(part_rules))
    schema = createSchema(part_rules, diskprofile)
    return schema, diskprofile
 
def cleanDiskProfile(disk_profile):
    lv_list = disk_profile.lv_dict.values()

    for lv in lv_list:
        if not lv.leave_unchanged:
            disk_profile.delete(lv)

    for vg in disk_profile.lvg_dict.values():
        try:
            disk_profile.delete(vg)
        except CannotDeleteVolumeGroupError:
            logger.debug('VG: %s has PVs with leave unchanged' % vg.name)
            pass
        except PhysicalVolumeStillInUseError:
            logger.debug('VG: %s has LVs remaining.' % vg.name)
            pass

    part_list = []
    extended_partition = None
    for disk in disk_profile.disk_dict.values():
        part_list = []
        extended_partition = None
        for p in disk.partition_dict.values():
            if p.type == 'extended':
                extended_partition = p
            else:
                part_list.append(p)

        for p in part_list:
            if not p.leave_unchanged:
                try:
                    disk_profile.delete(p)
                except PartitionIsPartOfVolumeGroupError:
                    pass

        if extended_partition and not extended_partition.leave_unchanged and \
           disk.partition_dict.has_key(basename(extended_partition.path)):
            try:
                disk_profile.delete(extended_partition)
            except CannotDeleteExtendedPartitionError:
                pass

    disk_profile.executeLVMFifo()
    disk_profile.commit()

def getVGList(part_rules, diskprofile):
    vg_list = []
    for p in part_rules:
        isVG = translatePartitionOptions(p['options'], 'vg')[0]
        if isVG:
            vg_name = p['device']
            vg_list.append(p)
    return vg_list

def getPartList(part_rules, diskprofile):
    """Get the list of partition entries that don't already exist."""
    part_list = []
    for p in part_rules:
        dev = p['device']
        if dev.lower() == 'n':
            vg = translatePartitionOptions(p['options'], 'pv')[1]
            if vg not in diskprofile.lvg_dict.keys():
                part_list.append(p)
                logger.debug('Append to part_list: %s' % p)
        elif dev.isdigit():
            mountpoint = translateMntPnt(p['mntpnt'])
            if mountpoint not in diskprofile.mountpoint_dict.keys():
                part_list.append(p)
                logger.debug('Append to part_list: %s' % p)
    return part_list

def hasPVs(diskprofile):
    for disk in diskprofile.disk_dict.values():
        for p in disk.partition_dict.values():
            if p.lvm_flag:
                return True
    return False

def getLVList(part_rules, diskprofile):
    lv_list = []
    for p in part_rules:
        isLV = translatePartitionOptions(p['options'], 'lv')[0]
        if isLV:
            lv_name = p['device']
            if lv_name not in diskprofile.lv_dict.keys():
                lv_list.append(p)
    return lv_list

    
def createSchema(part_rules, diskprofile):
    """ Adapt niipartition into a partitiontool schema. This schema can
        be passed along with a partitiontool diskprofile to setupDiskProfile
        method.

    """
    schema = {'disk_dict':{},'vg_dict':{}}

    # format for debug printing
    pp = PrettyPrinter(indent=2)
    vg_list = getVGList(part_rules, diskprofile)
    logger.debug('VG List after filtering:\n%s' % pp.pformat(vg_list))
    part_list = getPartList(part_rules, diskprofile)
    logger.debug('Partitions List after filtering:\n%s' % pp.pformat(part_list))
    lv_list = getLVList(part_rules, diskprofile)
    logger.debug('LV List after filtering:\n%s' % pp.pformat(lv_list))
    # create the volume groups first.
    try:
        for vginfo in vg_list:
            vgname = vginfo['device']
            vg_extent_size = translatePartitionOptions(vginfo['options'], 'vg')[1]
            schema['vg_dict'][vgname] = {'pv_list':[], 'lv_dict':{},
                                         'extent_size':vg_extent_size,
                                         'name':vgname}

        # create the normal volumes.
        for partinfo in part_list:
            fs = translateFSTypes(partinfo['fstype'])
            createPartition(partinfo, schema['disk_dict'], schema['vg_dict'])
            pv, vg_name = translatePartitionOptions(partinfo['options'], 'pv')
            if pv: handlePV(partinfo, vg_name, schema['vg_dict'])
        # renumber spanning partitions
        for disk in schema['disk_dict'].itervalues():
            part_dict = disk['partition_dict']
            if part_dict.has_key('N'):
                partition = part_dict['N']
                part_dict[len(part_dict)] = partition
                del part_dict['N']

        # create the logical volumes.
        for lvinfo in lv_list:
            lv, vg_name = translatePartitionOptions(lvinfo['options'],'lv')
            if lv: handleLV(lvinfo, vg_name, schema['vg_dict'])

        attachPVsToVGs(diskprofile, schema['vg_dict'])
        logger.debug('VG dict: %s' % str(schema['vg_dict']))

        preserve_types = Partition.native_type_dict.values() 
        preserve_fs = DiskProfile.fsType_dict.keys() 
        preserve_mntpnt = diskprofile.mountpoint_dict.keys()
        preserve_lv = [lv.name for lv in diskprofile.lv_dict.values()]
        schema['preserve_types'] = preserve_types
        schema['preserve_fs'] = preserve_fs
        schema['preserve_mntpnt'] = preserve_mntpnt
        schema['preserve_lv'] = preserve_lv

    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the lines."

    return schema

def attachPVsToVGs(disk_profile, vg_dict):
    for vg_name,vg in vg_dict.iteritems():
        logger.debug('VG Name: %s' % vg_name)
        pvs_with_vgs = [pv for pv in disk_profile.pv_dict.values() if pv.group]
        for pv in pvs_with_vgs:
            logger.debug('PV, group: %s' % str(pv.group.name))
            if pv.group and pv.group.name == vg_name:
                disk_no = getDiskNumber(pv.partition, disk_profile.disk_dict)
                part_no = pv.partition.num
                if not disk_no: continue
                vg['pv_list'].append({ disk: disk_no, partition: part_no })
                logger.debug('VG PV list: %s' % str(vg['pv_list']))

def getDiskNumber(partition, disk_dict):
    l = sorted(disk_dict.keys())
    for i in xrange(len(disk_dict)):
        k = l[i]
        disk = disk_dict[k]
        if partition.disk is disk:
            return i


def createPartition(partinfo, disk_dict, vg_dict):
    """ Create a new partition and add it to the supplied disk dictionary."""
    try:
        disknum = int(partinfo['device'])
        part_no = translatePartitionNumber(partinfo['partition'])
    except ValueError:
        if partinfo['device'].lower() == 'n':
            handleSpanningPartition(partinfo, disk_dict, vg_dict)
            disknum = 1
            part_no = 'N'
        else:
            logger.debug('Failed to translate disknum: %s, partition: %s' % (partinfo['device'], partinfo['partition']))
            raise InvalidPartitionSchema, "Couldn't translate the disknum/partition number."
    try:
        size = translatePartitionSize(partinfo['size'])
        fs = translateFSTypes(partinfo['fstype'])
        mountpoint = translateMntPnt(partinfo['mntpnt'])
        fill = translatePartitionOptions(partinfo['options'], 'fill')[0]
    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the Partition fields. " + \
                                      "disknum=%s, size=%s, fs=%s, mntpnt=%s, fill=%s, " + \
                                      "part_no=%s" % (partinfo['device'], partinfo['size'], \
                                      partinfo['fstype'], partinfo['mntpnt'], \
                                      partinfo['options'], partinfo['partition'])
 
    if part_no != 'N' and part_no <= 0:
        raise InvalidPartitionSchema, "Partition number cannot be less than 1."
    partition = {'size_MB': size, 'fill': fill,
                 'fs': fs, 'mountpoint': mountpoint}

    if disk_dict.has_key(disknum): disk = disk_dict[disknum]
    else: disk = {'partition_dict': {}}
    disk['partition_dict'][part_no] = partition
    disk_dict[disknum] = disk

def handleSpanningPartition(partinfo, disk_dict, vg_dict):
    is_pv, vg_name = translatePartitionOptions(partinfo['options'], 'pv')
    if not is_pv:
        raise InvalidPartitionSchema, "Partition marked as spanning multiple disks, but not as physical volumes."
    vg_dict[vg_name]['pv_span'] = True

def handlePV(partinfo, vg_name, vg_dict):
    if not vg_name.strip(): raise InvalidPartitionSchema, 'No Volume Group given for Physical Volume.'
    if vg_dict.has_key(vg_name): vg = vg_dict[vg_name]
    else: raise InvalidPartitionSchema, 'Physical Volume belongs to an unspecified Volume Group.'
    try:
        disknum = int(partinfo['device'])
        part_no = translatePartitionNumber(partinfo['partition'])
    except ValueError:
        if partinfo['device'].lower() == 'n':
            disknum = 'N'
            part_no = 'N'
        else:
            raise InvalidPartitionSchema, "Couldn't parse one of the LVM physical volume fields. " + \
                                          "disknum=%s, part_no=%s" % \
                                          (partinfo['device'], partinfo['partition'])

    vg['pv_list'].append({'disk': disknum, 'partition': part_no})

def handleLV(lvinfo, vg_name, vg_dict):
    vg_name = vg_name.strip()
    if not vg_name.strip(): raise InvalidPartitionSchema, 'No Volume Group given for Logical Volume.'
    if vg_dict.has_key(vg_name): vg = vg_dict[vg_name]
    else: raise InvalidPartitionSchema, 'Logical Volume %s belongs to non-existent Volume Group %s.' % \
                                        (lvinfo['device'], vg_name)
    try:
        name = lvinfo['device']
        size_MB = translatePartitionSize(lvinfo['size'])
        fill = translatePartitionOptions(lvinfo['options'], 'fill')[0]
        fs = translateFSTypes(lvinfo['fstype'])
        mountpoint = translateMntPnt(lvinfo['mntpnt'])
    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the LVM logical volume fields."

    vg['lv_dict'][name] = {'size_MB': size_MB, 'fill': fill,
                           'fs': fs, 'mountpoint': mountpoint}
