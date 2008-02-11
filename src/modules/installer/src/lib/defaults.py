#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import kusu.util.log as kusulog
from kusu.util.errors import *
from kusu.util.structure import Struct
from path import path
from sets import Set
from os.path import basename
import kusu.partitiontool as pt

logger = kusulog.getKusuLog('installer.defaults')

class DiskCollection(Struct):
    def __init__(self):
        Struct.__init__(self)
        self.no_of_disks = 0

    def addDisk(self, disk):
        self.no_of_disks += 1
        self[self.no_of_disks] = disk

    def __len__(self):
        return self.no_of_disks

class Disk(Struct):
    def __init__(self):
        Struct.__init__(self)
        self.no_of_partitions = 0
        self.partition_dict = {}

    def addPartition(self, partition):
        self.no_of_partitions += 1
        self.partition_dict[self.no_of_partitions] = partition


class Partition(Struct):
    def __init__(self):
        Struct.__init__(self)
        self.is_pv = False
        self.id = ''
        self.path = ''

class LVMGroup(Struct):
    def __init__(self):
        Struct.__init__(self)
        self.pv_list = []
        self.lv_dict = {}

    def addPV(self, disk, partition, id=''):
        self.pv_list.append(Struct(disk=disk, partition=partition, id=id))

    def addLV(self, lv):
        self.lv_dict[lv.name] = lv


class LVMLogicalVolume(Struct): pass

class LVMCollection(Struct):
    def __init__(self):
        Struct.__init__(self)

    def addVG(self, vg):
        self[vg.name] = vg


class PartitionSchema(Struct):
    def __init__(self, disks, lvm={}, preserve_types=[], preserve_fs=[], preserve_mntpnt=[], preserve_lv=[]):
        Struct(self)
        self.disk_dict=disks
        self.vg_dict=lvm
        self.preserve_types=preserve_types
        self.preserve_fs=preserve_fs
        self.preserve_mntpnt=preserve_mntpnt
        self.preserve_lv=preserve_lv

    def __eq__(self, other):
        disk_keys = self.disk_dict.keys()
        other_disk_keys = other['disk_dict'].keys()
        if 'no_of_disks' not in other_disk_keys:
            other_disk_keys.append('no_of_disks')
        if Set(disk_keys) != Set(other_disk_keys):
            print 'a'
            return False
        if Set(self.vg_dict.keys()) != Set(other['vg_dict'].keys()):
            print 'b'
            return False
        if Set(self.preserve_types) != Set(other['preserve_types']):
            print 'c'
            return False
        if Set(self.preserve_fs) != Set(other['preserve_fs']):
            print 'd'
            return False
        if Set(self.preserve_mntpnt) != Set(other['preserve_mntpnt']):
            print 'e'
            return False
        if Set(self.preserve_lv) != Set(other['preserve_lv']):
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


def vanillaSchema():
    """This is a plain vanilla schema that contains 4 physical partitions:
          a. /boot - ext3, 100:
          b. swap - 1000M
          c. / - 2000M
          d. /depot - 4000M (fill)
    """
    d1 = Disk()

    # Disk 1 Partition 1.
    d1p1 = Partition()
    d1p1.size_MB = 100
    d1p1.fs = 'ext3'
    d1p1.mountpoint = '/boot'
    d1p1.fill = False
    d1.addPartition(d1p1)

    # Disk 1 Partition 2.
    d1p2 = Partition()
    d1p2.size_MB = 1000
    d1p2.fs = 'linux-swap'
    d1p2.mountpoint = None
    d1p2.fill = False
    d1.addPartition(d1p2)

    # Disk 1 Partition 3.
    d1p3 = Partition()
    d1p3.size_MB = 2000
    d1p3.fs = 'ext3'
    d1p3.mountpoint = '/'
    d1p3.fill = False
    d1.addPartition(d1p3)

    # Disk 1 Partition 4.
    d1p4 = Partition()
    d1p4.size_MB = 4000
    d1p4.fs = 'ext3'
    d1p4.mountpoint = '/depot'
    d1p4.fill = True
    d1.addPartition(d1p4)

    disks = DiskCollection()
    disks.addDisk(d1)
    return PartitionSchema(disks=disks)

def vanillaSchemaLVM():
    """This is a plain vanilla schema that contains 3 physical partitions:
          a. /boot - ext3, 100:
          b. swap - 2000M
          c. LVM physical volume - 29000M (fill)
       The LVM pv makes up a logical volume group'VolGroup00', which contains
       4 logical volumes:
          a. ROOT - ext3, 12000M, mounted on /
          b. DEPOT - ext3, 10000M, mounted on /depot
          c. VAR - ext3, 2000M, mounted on /var
          d. HOME - ext3, 5000M, mounted on /home (fill)
    """
    # Physical Disks.
    d1 = Disk()

    # Disk 1 Partition 1.
    d1p1 = Partition()
    d1p1.size_MB = 100
    d1p1.fs = 'ext3'
    d1p1.mountpoint = '/boot'
    d1p1.fill = False
    d1.addPartition(d1p1)

    # Disk 1 Partition 2.
    d1p2 = Partition()
    d1p2.size_MB = 2000
    d1p2.fs = 'linux-swap'
    d1p2.mountpoint = None
    d1p2.fill = False
    d1.addPartition(d1p2)

    # Disk 1 Partition 3.
    d1p3 = Partition()
    d1p3.size_MB = 29000
    d1p3.fs = 'physical volume'
    d1p3.mountpoint = None
    d1p3.fill = True
    d1p3.is_pv = True
    d1p3.id = 'd1p3'
    d1.addPartition(d1p3)

#    dn = Disk()
#    dnpn = Partition()
#    dnpn.fill = 'N'
#    dn.addPartition(dnpn)

    # Create disk collection and add disk 1 to it.
    disks = DiskCollection()
    disks.addDisk(d1)
#    disks.addDisk(dn)

    # LVM disks.
    volgroup00 = LVMGroup()
    volgroup00.name = 'VolGroup00'
    volgroup00.extent_size = '32M'
    volgroup00.pv_span = True
    volgroup00.addPV(disk=1, partition=3, id='d1p3')
#    volgroup00.addPV(disk='N', partition='N')

    # Root Logical Volume.
    root = LVMLogicalVolume()
    root.name = 'ROOT'
    root.size_MB = 12000
    root.fs = 'ext3'
    root.mountpoint = '/'
    root.fill = False
    volgroup00.addLV(root)

    # /var Logical Volume.
    var = LVMLogicalVolume()
    var.name = 'VAR'
    var.size_MB = 2000
    var.fs = 'ext3'
    var.mountpoint = '/var'
    var.fill = False
    volgroup00.addLV(var)

    # Depot Logical Volume.
    depot = LVMLogicalVolume()
    depot.name = 'DEPOT'
    depot.size_MB = 10000
    depot.fs = 'ext3'
    depot.mountpoint = '/depot'
    depot.fill = False
    volgroup00.addLV(depot)

   # /home Logical Volume.
    home = LVMLogicalVolume()
    home.name = 'HOME'
    home.size_MB = 5000
    home.fs = 'ext3'
    home.mountpoint = '/home'
    home.fill = True
    volgroup00.addLV(home)

    lvm = LVMCollection()
    lvm.addVG(volgroup00)

    return PartitionSchema(disks=disks, lvm=lvm, preserve_types=['Dell Utility'])


def scenario22():
    """This corresponds to Scenario 2.2 of the Client Node Partitioning Report,
       Appendix:
          a. /boot - ext3, 100:
          b. swap - 1000M
          c. / - ext3, 6000M (fill)
    """
    # define the physical disk and partitions first
    disk_dict = { 1: { 'partition_dict': {} } }
    disk1_partition_dict = disk_dict[1]['partition_dict']
    disk1_partition_dict[1] = { 'size_MB': 100,
                                'fs': 'ext3',
                                'mountpoint': '/boot',
                                'fill': False}
    disk1_partition_dict[2] = { 'size_MB': 1000,
                                'fs': 'linux-swap',
                                'mountpoint': None,
                                'fill': False}
    disk1_partition_dict[3] = { 'size_MB': 6000,
                                'fs': 'ext3',
                                'mountpoint': '/',
                                'fill': True}

    schema = {'disk_dict' : disk_dict,
              'vg_dict' : None }

    return schema

def setupPreservedPartitions(disk_profile, schema):
    preserved_types = schema['preserve_types']
    dp = pt.DiskProfile(fresh=False, probe_fstab=False)
    for disk_path,disk in dp.disk_dict.iteritems():
        for p in disk.partition_dict.itervalues():
            if p.native_type:
                logger.debug('Found partition with type: %s' % p.native_type)
                logger.debug('Matching with types %s' % str(preserved_types))
                if p.native_type in preserved_types:
                    logger.debug('Match found!')
                    t = createPartition(disk_path, p, disk_profile)
                    if t:
                        disk_profile.manual_writes.append(t)


def createPartition(disk_path, partition, disk_profile):
    # XXX
    # Hack for transferring the native_type because
    # cannot assign native_type using pyparted
    import struct
    type = partition.pedPartition.native_type
    logger.debug('Partition type to preserve: %s' % type)
    logger.debug('Opening disk /dev/' + disk_path)
    in_p = file('/dev/' + disk_path)
    index = None
    try:
        in_p.seek(400)
        buf = in_p.read(1000)
        s = struct.pack('B', type)
        logger.debug('Looking for %s in %s' % (s, buf))
        if s in buf:
            index = buf.index(s) + 400
            logger.debug('type index found: %d' % index)
    except Exception, e:
        logger.debug(str(e))
        logger.debug('type index not found.')
    in_p.close()
    # XXX

    disk = disk_profile.disk_dict[disk_path]
    p = disk.createPartition(size=partition.size)
    p.pedPartition = partition.pedPartition
    p.start_sector = partition.start_sector
    p.end_sector = partition.end_sector
    p.boot_flag = partition.boot_flag
    p.lvm_flag = partition.lvm_flag
    p.leave_unchanged = True
    p.do_not_format = True
    p.on_disk = True

    # XXX
    # Hack for transferring the native_type because
    # cannot assign native_type using pyparted
    if index:
        if type == 0xde:
            logger.debug("Setting the partition's dellUP_flag to True")
            p.dellUP_flag = True
        return ('/dev/'+disk_path, index, struct.pack('B', type))
    return None
    # XXX

def isDiskFormatted(disk):
    if disk.pedDisk.type.name == 'loop':
        return True
    return False


def setupDiskProfile(disk_profile, schema=None, wipe_existing_profile=True):
    """Set up a disk profile based on a given schema."""
    # clear LVM logical volumes and groups.
    logger.debug('PRESERVE TYPES: ' + str(schema['preserve_types']))
    logger.debug('PRESERVE FS: ' + str(schema['preserve_fs']))
    logger.debug('PRESERVE MNTPNT: ' + str(schema['preserve_mntpnt']))
    logger.debug(str(disk_profile.lv_dict))
    logger.debug(str(disk_profile.lvg_dict))

    preserved_mntpnt = []
    preserved_fs = []
    preserved_lvg = []
    preserved_lv = []
    logger.debug('Wipe Existing Profile: %s' % wipe_existing_profile)
    if wipe_existing_profile:
        preserved_mntpnt, preserved_fs, preserved_lvg, preserved_lv = clearLVM(disk_profile, schema)
        disk_profile.executeLVMFifo()

        # clear partitions that haven't been preserved.
        for disk in disk_profile.disk_dict.itervalues():
            preserved_mntpnt1, preserved_fs1 = clearDisk(disk_profile, disk, schema)
            preserved_mntpnt += preserved_mntpnt1
            preserved_fs += preserved_fs1
        for disk in disk_profile.disk_dict.itervalues():
            logger.debug('Disk %s has partitions %s' % (disk.path, str(disk.partition_dict.keys())))
            logger.debug('mntpnts: %s' % ([p.mountpoint for p in disk.partition_dict.values()]))
        disk_profile.commit()

    if not schema:
        return True
    else: # do the schema stuff.
        if not schema.has_key('disk_dict') or not schema.has_key('vg_dict'):
            raise PartitionSchemaError, 'Schema has no disk and/or LVM description.'

        createPhysicalSchema(disk_profile, schema['disk_dict'], schema['vg_dict'], preserved_mntpnt, preserved_fs)
        if schema['vg_dict']:
            createLVMSchema(disk_profile, schema['vg_dict'], preserved_mntpnt, preserved_fs, preserved_lvg, preserved_lv)

    logger.debug('Disk Profile set up')


def clearLVM(disk_profile, schema):
    preserve_fs = schema['preserve_fs']
    preserve_mntpnt = schema['preserve_mntpnt']
    preserve_lv = schema['preserve_lv']

    preserved_mntpnt = []
    preserved_fs = []
    preserved_lvg = []
    preserved_lv = []

    if disk_profile.lv_dict:
        lv_list = disk_profile.lv_dict.values()
        for lv in lv_list:
            if lv.mountpoint and lv.mountpoint not in preserve_mntpnt or \
               lv.fs_type and lv.fs_type not in preserve_fs or \
               lv.name not in preserve_lv:
                disk_profile.delete(lv)
            else:
                if lv.mountpoint in preserve_mntpnt:
                    preserved_mntpnt.append(lv.mountpoint)
                elif lv.fs_type in preserve_fs:
                    preserved_fs.append(lv.fs_type)
                preserved_lv.append(lv.name)
                lv.leave_unchanged = True

    if disk_profile.lvg_dict:
        lvg_list = disk_profile.lvg_dict.values()
        for lvg in lvg_list:
            try:    
                disk_profile.delete(lvg)
            except PhysicalVolumeStillInUseError, e:
                preserved_lvg.append(lvg.name)
                logger.debug(str(e))
            except CannotDeleteVolumeGroupError, e:
                preserved_lvg.append(lvg.name)
                logger.debug(str(e))
    return preserved_mntpnt, preserved_fs, preserved_lvg, preserved_lv

def clearDisk(disk_profile, disk, schema):
    # separate into logical, extended, and primary partitions.
    primary = []
    extended = None
    logical = []
    preserve_list = schema['preserve_types']
    preserve_fs = schema['preserve_fs']
    preserve_mntpnt = schema['preserve_mntpnt']

    preserved_fs = []
    preserved_mntpnt = []

    for partition in disk.partition_dict.values():
        if partition.part_type == 'primary':
            logger.debug('Partition %s is primary type' % partition.path)
            primary.append(partition)
        elif partition.part_type == 'extended':
            logger.debug('Partition %s is extended type' % partition.path)
            extended = partition
        else:
            logger.debug('Partition %s is logical type' % partition.path)
            logical.append(partition)

    # remove the logical partitions first.
    for partition in reversed(sorted(logical)):
        if partition.mountpoint and partition.mountpoint not in preserve_mntpnt:
            logger.debug('mountpoint %s not preserved.' % partition.mountpoint)
        if partition.fs_type and partition.fs_type not in preserve_fs:
            logger.debug('FS type %s not preserved.' % partition.fs_type)
        if partition.native_type and partition.native_type not in preserve_list:
            logger.debug('partition type %s not preserved.' % partition.native_type)

        if partition.mountpoint and partition.mountpoint not in preserve_mntpnt or \
           partition.fs_type and partition.fs_type not in preserve_fs or \
           partition.native_type and partition.native_type not in preserve_list:
            logger.debug('Delete partition %d from %s' % (partition.num, disk.path))
            try:
                disk_profile.delete(partition, keep_in_place=True)
            except PartitionIsPartOfVolumeGroupError, e:
                if partition.mountpoint in preserve_mntpnt:
                    preserved_mntpnt.append(partition.mountpoint)
                else:
                    preserved_fs.append('physical volume')
                partition.leave_unchanged = True
                logger.debug(str(e))
        else:
            partition.leave_unchanged = True
            extended = None
    # then remove the extended partitions.
    if extended and disk.partition_dict.has_key(basename(extended.path)):
        logger.debug('Removing extended partition')
        disk_profile.delete(extended, keep_in_place=True)
    # finally remove the primary partitions.
    for partition in reversed(sorted(primary)):
        if partition.mountpoint and partition.mountpoint not in preserve_mntpnt:
            logger.debug('mountpoint %s not preserved.' % partition.mountpoint)
        if partition.fs_type and partition.fs_type not in preserve_fs:
            logger.debug('FS type %s not preserved.' % partition.fs_type)
        if partition.native_type and partition.native_type not in preserve_list:
            logger.debug('partition type %s not preserved.' % partition.native_type)

        if partition.mountpoint and partition.mountpoint not in preserve_mntpnt or \
           partition.fs_type and partition.fs_type not in preserve_fs or \
           partition.native_type and partition.native_type not in preserve_list:
            logger.debug('Delete partition %d from %s' % (partition.num, disk.path))
            try:
                disk_profile.delete(partition, keep_in_place=True)
            except PartitionIsPartOfVolumeGroupError, e:
                if partition.mountpoint in preserve_mntpnt:
                    preserved_mntpnt.append(partition.mountpoint)
                else:
                    preserved_fs.append('physical volume')
                partition.leave_unchanged = True
                logger.debug(str(e))
        else:
            partition.leave_unchanged = True
    return preserved_mntpnt, preserved_fs

def createPhysicalSchema(disk_profile, disk_schemata, lvg_schemata, preserved_mntpnt, preserved_fs):
    # check if we have enough disks to fulfill the schema
    if len(disk_profile.disk_dict) < len(disk_schemata):
        raise PartitionSchemaError, 'Schema defines more disks than ' + \
                                    'is physically available on this system.'

    # do the physical disk and partitions first.
    sorted_disk_keys = sorted(disk_profile.disk_dict.keys())
    for i in xrange(len(disk_schemata)):
        # for each disk in the schema.
        schema_disk = disk_schemata[i+1]
        schema_partition_dict = schema_disk['partition_dict']
        try:
            for j in xrange(len(schema_partition_dict)):
                # for each partition in the current disk.
                schema_partition = schema_partition_dict[j+1]
                disk_key = sorted_disk_keys[i]
                size_MB = schema_partition['size_MB']
                fs = schema_partition['fs']
                mountpoint = schema_partition['mountpoint']
                fill = schema_partition['fill']
                if schema_partition.has_key('percent'):
                    disk = disk_profile.disk_dict[disk_key]
                    # The percent calculation below is not precise
                    # due to integer rounding, but should be fine.
                    size_MB = schema_partition.percent * disk.size / 1024 / 1024 / 100
                if mountpoint in preserved_mntpnt or fs in preserved_fs:
                    logger.debug('Partition was preserved. Not creating')
                    continue
                logger.debug('Creating new partition %d for disk %d of size: %d' % (j+1, i, size_MB))
                p = disk_profile.newPartition(disk_key,
                                              size_MB,
                                              False,
                                              fs,
                                              mountpoint,
                                              fill)
                # if new partition is physical volume, then the containing volume group
                # should be updated with its path.
                if fs == 'physical volume' and schema_partition.has_key('id'):
                    logger.debug('Created physical volume, now adjusting volume group reference.')
                    id = schema_partition['id']
                    for vg_schema in lvg_schemata.itervalues():
                        logger.debug('VG name: %s' % vg_schema['name'])
                        pv_schemata = vg_schema['pv_list']
                        for pv_schema in pv_schemata:
                            if pv_schema.has_key('id') and pv_schema['id'] == id:
                                logger.debug('Found PV in VG, assigning path %s' % p.path)
                                pv_schema['path'] = p.path

                logger.debug('Created new partition %d for disk %d of size %d' % (j+1, i, size_MB))
        except IndexError:
            raise PartitionSchemaError, 'Run out of disks.'
        except PartitionSizeTooLargeError:
            raise OutOfSpaceError, 'Available size not enough to fit partition of size %d MB' % \
                                    size_MB


def createLVMSchema(disk_profile, lvm_schemata, preserved_mntpnt, preserved_fs, preserved_lvg, preserved_lv):
    logger.debug('Preserved LV: %s' % str(preserved_lv))
    logger.debug('LVM schema: %s' % str(lvm_schemata))
    for vg_key, vg_schema in lvm_schemata.iteritems():
        sorted_disk_keys = sorted(disk_profile.disk_dict.keys())
        # create the Volume Group first.
        pv_schemata = vg_schema['pv_list']
        pv_list = []
        for pv_schema in pv_schemata:
            disk_id = pv_schema['disk']
            part_id = pv_schema['partition']
            if disk_id.__str__().lower() == 'n' or part_id.__str__().lower() == 'n':
                pv_list.extend(getAllFreePVs(disk_profile))
                break
            if pv_schema.has_key('path'):
                logger.debug('PV has path')
                pv = disk_profile.pv_dict[pv_schema['path']]
            else:
                logger.debug('PV has no path')
                disk_id = int(disk_id)
                part_id = int(part_id)
                disk_key = sorted_disk_keys[disk_id-1]
                disk = disk_profile.disk_dict[disk_key]
                logger.debug('selected disk: %s partitions: %d' % (disk_key, len(disk.partition_dict)))
                partition = disk.partition_dict[part_id]
                pv = disk_profile.pv_dict[partition.path]
            pv_list.append(pv)

        if vg_key in preserved_lvg or vg_key in disk_profile.lvg_dict.keys():
            logger.debug('VG has been preserved')
            vg = disk_profile.lvg_dict[vg_key]
        else:
            if not pv_list:
                s = "No space left to create Volume Group %s, please " % vg_key + \
                    "review and remove some of your current partitions and/or " + \
                    "modify the partition schema for this node group.\n\n" + \
                    "This installation will stop and your system will reboot."
                raise VolumeGroupMustHaveAtLeastOnePhysicalVolumeError, s
            vg = disk_profile.newLogicalVolumeGroup(vg_key,
                                                    vg_schema['extent_size'],
                                                    pv_list)

        # create the Logical Volumes.
        lv_schema = vg_schema['lv_dict']
        last_lv = []
        for lv_name, lv_schema in lv_schema.iteritems():
            if lv_schema['fill']:
                last_lv.append(lv_name)
                last_lv.append(lv_schema)
                continue
            logger.debug('Creating %s' % lv_name)
            size_MB = lv_schema['size_MB']
            if lv_schema.has_key('percent'):
                # The percent calculation below is not precise
                # due to integer rounding, but should be fine.
                logger.debug('Percentage chosen for %s is %d' % (lv_name, lv_schema.percent))
                logger.debug('VG Extents: %d' % vg.extentsTotal())
                extents = lv_schema.percent * vg.extentsTotal() / 100
                logger.debug('%s extents: %d' % (lv_name, extents))
                size_MB = vg.extent_size / 1024 / 1024 * extents
                logger.debug('%s size: %d' % (lv_name, size_MB))
            if lv_schema['mountpoint'] in preserved_mntpnt or \
               lv_schema['fs'] in preserved_fs or lv_name in preserved_lv:
                logger.debug('LV has been preserved')
            else:
                disk_profile.newLogicalVolume(lv_name,
                                              vg,
                                              size_MB,
                                              lv_schema['fs'],
                                              lv_schema['mountpoint'],
                                              lv_schema['fill'])
                logger.debug('Finished creating %s' % lv_name)
        if last_lv and last_lv[1]['mountpoint'] not in preserved_mntpnt and \
           last_lv[1]['fs'] not in preserved_fs and last_lv[0] not in preserved_lv:
            disk_profile.newLogicalVolume(last_lv[0],
                                          vg,
                                          last_lv[1]['size_MB'],
                                          last_lv[1]['fs'],
                                          last_lv[1]['mountpoint'],
                                          last_lv[1]['fill'])
    logger.debug('Create LVM Schema finished')


def getAllFreePVs(disk_profile):
    pv_list = []
    for pv in disk_profile.pv_dict.values():
        if pv.group is None:
            pv_list.append(pv)
    return pv_list

#def getPVsForVG(disk_profile):
    
