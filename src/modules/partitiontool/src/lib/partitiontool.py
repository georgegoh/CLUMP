#!/usr/bin/env python
# $Id: partitiontool.py 268 2007-04-12 02:29:30Z ggoh $
#
# Kusu Text Installer Partition Tool Mockup.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
"""This mockup is a stub for the real partitioner tool module. The following
   describes the model of this tool.

   The tool keeps track of the following entities in a system:
      a) physical disks (ie, /dev/sda, /dev/hda, ...)
      b) partitions (sda1, hda1, ...)
      c) logical volume groups
      d) logical volumes
      e) mountpoints

   DISKS -
   In the first instance, the only information we can get about the machine is
   about the physical disks in the system (partitions/LVM volumes are schemas
   that we apply to the physical disks in time). Thus, the mockup starts with a
   mock list of physical disks, and builds up from there.

   PARTITIONS -
   When we have the disk info, the next step is to create the partitions,
   defining their size, fs type, and mountpoint(if applicable). When creating
   partitions, the tool needs to be aware of:
      a) whether we have enough disk space available to allocate to this 
         partition;
      b) mountpoint collisions with an existing volume; and
      c) any special provisions to make this a primary, or extended partition.

   LOGICAL VOLUME GROUPS -
   If we have specified at least one partition on our disk(s) to be an LVM
   physical volume, then we are able to specify LVM Logical Volume Groups. When
   creating a Logical Volume Group(LVG), the tool needs to be aware of:
      a) name collisions with an existing LVG; and
      b) partition collisions with an existing LVG.

   LOGICAL VOLUMES -
   If there is an existing Logical Volume Group, then we are able to create a
   Logical Volume (LV). when creating a LV, the tool needs to be aware of:
      a) whether there is enough space available in the LVG;
      b) name collisions with an existing LV; and
      c) mountpoint collisions with an existing volume.

   MOUNTPOINTS -
   A mountpoint corresponds to a line in the /etc/fstab file. See man page for
   /etc/fstab for details about /etc/fstab.

   EXCEPTIONS -
   From the above, the following exceptions are noted:
      a) OutOfSpaceError
      b) DuplicateNameError
      c) DuplicateMountpointError

"""
__version__ = "$Revision: 268 $"
import math
import logging
import commands
import parted
import exceptions


class KusuError(exceptions.Exception): pass
class OutOfSpaceError(KusuError): pass
class DuplicateNameError(KusuError): pass
class DuplicateMountpointError(KusuError): pass
class NameNotFoundError(KusuError): pass
class UnknownPartitionTypeError(KusuError): pass
class PartitionSizeTooLargeError(KusuError): pass

fsTypes = {}
fs_type = parted.file_system_type_get_next ()
while fs_type:
    fsTypes[fs_type.name] = fs_type
    fs_type = parted.file_system_type_get_next (fs_type)

partitionTypes = {
    'BOOT' : parted.PARTITION_BOOT,
    'EXTENDED' : parted.PARTITION_EXTENDED,
    'FIRST_FLAG' : parted.PARTITION_FIRST_FLAG,
    'FREESPACE' : parted.PARTITION_FREESPACE,
    'HIDDEN' : parted.PARTITION_HIDDEN,
    'HPSERVICE' : parted.PARTITION_HPSERVICE,
    'LAST_FLAG' : parted.PARTITION_LAST_FLAG,
    'LBA' : parted.PARTITION_LBA,
    'LOGICAL' : parted.PARTITION_LOGICAL,
    'LVM' : parted.PARTITION_LVM,
    'METADATA' : parted.PARTITION_METADATA,
    'MSFT_RESERVED' : parted.PARTITION_MSFT_RESERVED,
    'PALO' : parted.PARTITION_PALO,
    'PREP' : parted.PARTITION_PREP,
    'PRIMARY' : parted.PARTITION_PRIMARY,
    'PROTECTED' : parted.PARTITION_PROTECTED,
    'RAID' : parted.PARTITION_RAID,
    'ROOT' : parted.PARTITION_ROOT,
    'SWAP' : parted.PARTITION_SWAP
}


class DiskProfile(object):
    """DiskProfile contains all information about the disks in a machine.

       Object variables:
       disk_dict - a dictionary referencing physical disks in a system. The key
                   is the device name, and the value is the Disk object. For
                   example, to get the first disk on the SCSI bus, we do this:

                      disk = diskProfile.disk_dict['sda']
    """
    disk_dict = {}
    mountpoints = {}
    lv_groups = {} # not implemented yet.
    logi_vol = {} # not implemented yet.
    fsType_dict = { 'ext2' : fsTypes['ext2'],
                    'ext3' : fsTypes['ext3'],
                    'physical volume' : None,
                    'software RAID' : None,
                    'swap' : fsTypes['linux-swap'],
                    'vfat' : fsTypes['fat32']
                  }
    partitionType_dict = { 'ext2' : partitionTypes['PRIMARY'],
                           'ext3' : partitionTypes['PRIMARY'],
                           'physical volume' : partitionTypes['LVM'],
                           'software RAID' : partitionTypes['RAID'],
                           'swap' : partitionTypes['SWAP'],
                           'vfat' : partitionTypes['PRIMARY']
                         }


    def __init__(self, fresh):
        fdisk_out = commands.getoutput("/sbin/fdisk -l 2>/dev/null | grep 'Disk' | awk '{ print $2 }'")
        # Output is in the form of "/dev/XXX:\n/dev/YYY", so massage it into a usable form.

        disks_str = fdisk_out.split('\n')
        for disk_str in disks_str:
            if disk_str:
                self.disk_dict[disk_str[5:-1]] = Disk(disk_str[:-1], self, fresh)


    def newPartition(self, disk_id, size, fixed_size, fs_type, mountpoint):
        """Create a new partition."""
        # sanity check
        if mountpoint in self.mountpoints.keys():
            raise DuplicateMountpointError, 'Assigned mountpoint already exists.'

        disk = self.disk_dict[disk_id]
        logging.debug('Add New Partition to Disk ID: ' + disk_id)
        if fs_type:
            new_partition = disk.addPartition(size, fsTypes[fs_type], mountpoint)
        else:
            new_partition = disk.addPartition(size, None, mountpoint)

        if mountpoint:
            self.mountpoints[mountpoint] = new_partition

        return new_partition

    def editPartition(self, part_id, size, fixed_size, fs_type, mountpoint):
        """Edit an existing partition.""
        partition = partitions[part_id]
        disk = disks[partition.disk_id]

        # sanity check
        if size > partition.size:
            additional_size_required = size - partition.size
            free_space_sector = disk.lookForFreeSpace(additional_size_required,
                                                      partition.start_sector)
            if free_space_sector != partition.end_sector + 1:
                raise OutOfSpaceError, _('Not enough space to expand partition to desired size')
        if mountpoint in mountpoints.keys():
            raise DuplicateMountpointError, _('Assigned mountpoint already exists.')

        partition.size = size
        partition.fixed_size = fixed_size
        partition.fs_type = fs_type
        partition.setMountpoint(mountpoint)
"""

    def deletePartition(self, partition_obj):
        """Delete an existing partition by name. E.g., to delete the first
           partition of the first disk(sda), the argument would be 'sda1'.
        """
        # sanity check for LVM - raise error if currently in a Logical VG.
#        for lv_id, lv_grp in self.lv_groups.iteritems():
#            if part_id in self.lv_grp.physical_volume_ids:
#                raise KusuError, _('Remove %s from %s first') % (part_id, lv_id)

        partition_obj.disk.delPartition(partition_obj)
        if partition_obj.mountpoint in self.mountpoints.keys():
            self.mountpoints.pop(partition_obj.mountpoint)


    def newLogicalVolume(self, name, vol_grp_id, size, fs_type, mountpoint):
        """Create a new logical volume."""
        # sanity checks
        if name in logi_vol.keys():
            raise DuplicateNameError, _('Logical Volume name already exists.')
        if mountpoint in mountpoints.keys():
            raise DuplicateMountpointError, _('Assigned mountpoint already exists.')

        logical_vol_grp = lv_groups[vol_grp_id]
        proposed_lv = logical_vol_grp.proposeLogicalVolume(int(size),
                                                           fs_type, mountpoint)

        logical_vol_grp.logical_volume_ids.append(name)
        logi_vol[name] = proposed_lv
        proposed_lv.vol_group_id = vol_grp_id
        mountpoints[mountpoint] = name


    def editLogicalVolume(self, lv_id, name, vol_grp_id, size, fs_type, mountpoint):
        """Edit an existing logical volume."""
        lv = logi_vol[lv_id]
        lv_grp = lv_groups[lv.vol_group_id]

        # sanity checks
        if lv_id != name:
            if name in logi_vol.keys():
                raise DuplicateNameError, 'Logical Volume name already exists.'
        if size > lv.size:
            additional_size_required = size - lv.size
            if additional_size_required > lv_grp.availableSize():
                raise OutOfSpaceError, _('Not enough free space on volume group.')
        if mountpoint in mountpoints.keys():
            raise DuplicateMountpointError, 'Assigned mountpoint already exists.'

        # passed sanity checks, now do it!
        lv.size = size
        lv.fs_type = fs_type
        lv.mountpoint = mountpoint
        if lv_id != name:
            logi_vol[name] = lv
            logi_vol.pop(lv_id)
            lv_grp.logical_volume_ids.append(name)
            lv_grp.logical_volume_ids.remove(lv_id)


    def deleteLogicalVolume(self, lv_id):
        """Delete an existing logical volume."""
        lv = logi_vol[lv_id]
        # remove from vol_group
        lv_grp = lv_groups[lv.vol_group_id]
        lv_grp.logical_volume_ids.remove(lv_id)
        # remove from mountpoints
        mountpoints.pop(lv.mountpoint)
        # remove from logi_vol
        logi_vol.pop(lv_id)


    def newLogicalVolumeGroup(self, name, phys_extent, phys_vol_ids):
        """Create a new logical volume group."""
        _phys_extent = int(phys_extent)
        # sanity checks
        if name in lv_groups.keys():
            raise DuplicateNameError, 'Logical Volume Group name already exists.'
        if _phys_extent not in range(2,513) or _phys_extent % 2:
            raise KusuError, 'Volume Group physical extent must be a multiple ' + \
                               'of 2, between 2-512.'

        # passed sanity checks, now do it!
        new_vol_group = VolGroup(phys_extent, phys_vol_ids)
        lv_groups[name] = new_vol_group


    def editLogicalVolumeGroup(self, lvg_id, name, phys_vol_ids):
        """Edit an existing logical volume group."""
        lvg = lv_groups[lvg_id]
        # sanity checks
        if lvg_id != name:
            if name in lv_groups.keys():
                raise DuplicateNameError, _('Proposed name already exists.')
        if sorted(phys_vol_ids) != sorted(lvg.physical_volume_ids):
            if lvg.logical_volume_ids:
                raise KusuError, 'Remove all logical volumes in this group ' + \
                                 'before modifying the list of physical volumes.'
        # passed sanity checks, now do it!
        if lvg_id != name:
            for lv in lvg.itervalues():
                lv.vol_group_id = name
            lv_groups.pop(lvg_id)
            lv_groups[name] = lvg

        if sorted(phys_vol_ids) != sorted(lvg.physical_volume_ids):
            lvg.physical_volume_ids = phys_vol_ids
        

    def deleteLogicalVolumeGroup(self, lvg_id):
        """Delete an existing logical volume group."""
        lvg = lv_groups[lvg_id]
        # sanity checks
        if lvg.logical_volume_ids:
            raise KusuError, 'All logical volumes in this group must be ' + \
                             'removed before the group can be deleted.'
        lv_groups.pop(lvg_id)

    def commit(self):
        for disk in self.disk_dict.itervalues():
            disk.commit()

    def formatAll(self):
        for disk in self.disk_dict.itervalues():
            disk.formatAll()

        
class Disk(object):
    """Disk class represents a physical disk in the system.
       Attributes:
          a. profile - reference to the DiskProfile object that owns this disk.
          b. pedDisk - encapsulated instance of parted.PedDisk.
          c. partitions_dict - dictionary of partitions on this disk.
       A PedDisk instance encapsulates an instance of parted.PedDevice, and thus
       Disk has the following additional(hidden) attributes, which can be 
       read(-only) :
          a. length
          b. model
          c. path
          d. sector_size
          e. type
          f. heads
          g. sectors
          h. cylinders
    """
    profile = None
    pedDisk = None
    partitions_dict = None
    __getattr_dict = { 'length' : 'self.pedDevice.length',
                       'model' : 'self.pedDevice.model',
                       'path' : 'self.pedDevice.path',
                       'sector_size' : 'self.pedDevice.sector_size',
                       'type' : 'self.pedDevice.type',
                       'heads' : 'self.pedDevice.heads',
                       'sectors' : 'self.pedDevice.sectors',
                       'cylinders' : 'self.pedDevice.cylinders',
                       'pedDevice' : 'self.pedDisk.dev'
                     }

    def __init__(self, path, profile, fresh=False):
        self.profile = profile
        self.partitions_dict = {}
        pedDevice = parted.PedDevice.get(path)
        if fresh:
            pedDiskType = pedDevice.disk_probe()
            self.pedDisk = pedDevice.disk_new_fresh(pedDiskType)
        else:
            try:
                self.pedDisk = parted.PedDisk.new(pedDevice)
                for i in range(self.pedDisk.get_last_partition_num()):
                    pedPartition = self.pedDisk.get_partition(i+1)
                    self.__appendToPartitionDict(pedPartition)
            except parted.error, e:
                if str(e).endswith('unrecognised disk label.'):
                    pedDiskType = parted.disk_type_get('msdos')
                    self.pedDisk = pedDevice.disk_new_fresh(pedDiskType)

    def __getattr__(self, name):
        if name in self.__getattr_dict.keys():
            return eval(self.__getattr_dict[name])
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (__class__, name)

    def __appendToPartitionDict(self, pedPartition, mountpoint=None):
        new_partition = Partition(self, pedPartition, mountpoint)
        self.partitions_dict[pedPartition.num] = new_partition
        return new_partition
        
    def addPartition(self, size, fs_type=None, mountpoint=None):
        """Add a partition to this disk.
           Parameters:
              1. size in bytes.
              2. type of partition(see partitionTypes).
              3. optional fs type(defaults to None).
        """
        next_partition_type = self.__getNextPartitionType()
        start_sector, end_sector = self.__getStartEndSectors(size)
        new_pedPartition = None

        try:
            constraint = self.pedDevice.constraint_any()

            if next_partition_type == 'PRIMARY':
                new_pedPartition = self.pedDisk.partition_new(partitionTypes['PRIMARY'],
                                                          fs_type,
                                                          start_sector,
                                                          end_sector)

            elif next_partition_type == 'EXTENDED':
                # create and add extended partition to fill the rest of the disk.
                extended_pedPartition = self.pedDisk.partition_new(
                                            partitionTypes['EXTENDED'],
                                            None,
                                            start_sector,
                                            self.length-1)
                self.pedDisk.add_partition(extended_pedPartition, constraint)
                self.__appendToPartitionDict(extended_pedPartition, None)
                # create logical partition.
                new_pedPartition = self.pedDisk.partition_new(
                                        partitionTypes['LOGICAL'],
                                        fs_type,
                                        start_sector,
                                        end_sector)

            elif next_partition_type == 'LOGICAL':
                # create logical partition.
                new_pedPartition = self.pedDisk.partition_new(
                                        partitionTypes['LOGICAL'],
                                        fs_type,
                                        start_sector,
                                        end_sector)

            else:
                raise UnknownPartitionTypeError

        except parted.error, msg:
            raise KusuError, msg
    
        self.pedDisk.add_partition(new_pedPartition, constraint)
        new_partition = self.__appendToPartitionDict(new_pedPartition, mountpoint)
        return new_partition

    def delPartition(self, partition_obj):
        """Remove a partition from this disk. Argument is the Partition object
           itself.
        """
        del self.partitions_dict[partition_obj.num]
        self.pedDisk.delete_partition(partition_obj.pedPartition)


    def __getNextPartitionType(self):
        """Get the next assignable partition number, and whether it should be an
           extended partition or not.
        """
        last_partition_num = self.pedDisk.get_last_partition_num()
        if last_partition_num == 3:
            next_partition_num = 5
            return 'EXTENDED'
        elif last_partition_num > 4:
            return 'LOGICAL'
        else:
            return 'PRIMARY'

    def __getStartEndSectors(self, size):
        """For a given size(in bytes), return a tuple of (start_sector, end_sector)
           that will accommodate this new partition.
        """
        last_part_num = self.pedDisk.get_last_partition_num()
        if last_part_num < 1: # no partitions found
            start_sector = 0
        else:
            lastPart = self.pedDisk.get_partition(last_part_num)
            if lastPart.type == parted.PARTITION_FREESPACE:
                start_sector = lastPart.geom.start
            else:
				start_sector = lastPart.geom.end + 1
        start_sector = self.__alignStartSector(start_sector)

        end_sector = start_sector + (size / self.pedDisk.dev.sector_size) - 1
        end_sector = self.__alignEndSector(end_sector)

        # Not actually making a new partition, but using parted to catch any
        # size errors.
        try:
            new_part = self.pedDisk.partition_new(parted.PARTITION_PRIMARY,
                                                  fsTypes['ext3'],
                                                  start_sector,
                                                  end_sector)
        except parted.error, msg:
            if msg.__str__().startswith("Error: Can't have a partition outside the disk!"):
                msg = "Requested partition size is too large to fit into " + \
                      "the remaining space available on the disk."
            raise PartitionSizeTooLargeError, msg

        return (start_sector, end_sector)

    def convertStartSectorToCylinder(self, start_sector):
         cylinder = int(math.floor(
                        (float(start_sector) /
                        (self.pedDisk.dev.heads * self.pedDisk.dev.sectors)) + 1))
         return cylinder       

    def convertEndSectorToCylinder(self, end_sector):
        cylinder = int(math.ceil(float(end_sector + 1) /
                           (self.pedDisk.dev.heads * self.pedDisk.dev.sectors)))
        return cylinder

    def __alignStartSector(self, start_sector):
        """'A well-known claim says that partitions should start and end at
            cylinder boundaries.'
              -(http://tldp.org/HOWTO/Large-Disk-HOWTO-6.html#ss6.2)

           While the kernel may have no problems with partitions that break this
           claim, we can never fully guarantee that the user's tools won't flag
           this as a (non-)error. So let's keep everybody happy.
        """
        cylinder = self.convertStartSectorToCylinder(start_sector)

        sector = long((cylinder - 1) * 
                      (self.pedDisk.dev.heads * self.pedDisk.dev.sectors))
        return sector

    def __alignEndSector(self, end_sector):
        """'A well-known claim says that partitions should start and end at
            cylinder boundaries.'
              -(http://tldp.org/HOWTO/Large-Disk-HOWTO-6.html#ss6.2)

           While the kernel may have no problems with partitions that break this
           claim, we can never fully guarantee that the user's tools won't flag
           this as a (non-)error. So let's keep everybody happy.
        """
        cylinder = self.convertEndSectorToCylinder(end_sector)

        sector = long((cylinder) *
                      (self.pedDisk.dev.heads * self.pedDisk.dev.sectors) - 1)
        return sector

    def commit(self):
        self.pedDisk.commit()

    def formatAll(self):
        for partition in self.partitions_dict.itervalues():
            partition.format()


class Partition(object):
    """A Partition object represents a partition residing on a disk in the
       system.
       Attributes:
          a. disk - reference to the Disk object that this partition is on.
          b. pedPartition - the instance of parted.PedPartition that this class
                            encapsulates.
          c. mountpoint
       A Partition instance encapsulates an instance of parted.PedPartition, and
       thus has the following additional(hidden) attributes, which can be 
       read(-only):
          a. start_sector
          b. end_sector
          c. length
          d. part_type
          e. fs_type
          f. path
          g. num (e.g., num=1 for sda1, num=3 for sda3)
          h. start_cylinder
          i. end_cylinder
          j. type
    """
    disk = None
    pedPartition = None
    mountpoint = None
    __getattr_dict = { 'start_sector' : 'self.pedPartition.geom.start',
                       'end_sector' : 'self.pedPartition.geom.end',
                       'length' : 'self.pedPartition.geom.length',
                       'part_type' : 'self.pedPartition.type_name',
                       'path' : 'self.disk.path + str(self.num)',
                       'num' : 'self.pedPartition.num',
                       'start_cylinder' : 'self.disk.convertStartSectorToCylinder(self.start_sector)',
                       'end_cylinder' : 'self.disk.convertEndSectorToCylinder(self.end_sector)',
                       'type' : 'self.pedPartition.type_name'
                      }
    __setattr_dict = { 'start_sector' : "self.pedPartition.geom.set_start(long('%s'))",
                       'end_sector' : "self.pedPartition.geom.set_end(long('%s'))"
                     }

    def __init__(self, disk, pedPartition, mountpoint=None):
        self.disk = disk
        self.pedPartition = pedPartition
        self.mountpoint = mountpoint

    def __getattr__(self, name):
        if name == 'fs_type':
            if self.pedPartition.fs_type:
                return self.pedPartition.fs_type.name
            else:
                return None
        elif name in self.__getattr_dict.keys():
            return eval(self.__getattr_dict[name])
        else:
            raise AttributeError, "Partition instance has no attribute '%s'" % name

    def __setattr__(self, name, value):
        if name in self.__setattr_dict.keys():
            eval(self.__setattr_dict[name] % str(value))
        else:
            object.__setattr__(self, name, value)

    def size(self):
        return self.disk.sector_size * self.length

    def format(self):
        if self.fs_type == 'ext2':
            print commands.getoutput('mkfs.ext2 %s' % self.path)
        elif self.fs_type == 'ext3':
            print commands.getoutput('mkfs.ext3 %s' % self.path)
        elif self.fs_type == 'swap':
            print commands.getoutput('mkswap %s' % self.path)


import unittest
class DiskProfileTestCase(unittest.TestCase):
    """Test cases for the DiskProfile class.

       Note: We are assuming that our machine has 2 SCSI disks:
          /dev/sda: 250 GB (250 * 10^9)
          /dev/sdb: 250 GB (250 * 10^9)
    """
    def setUp(self):
        self.dp = DiskProfile()

    def tearDown(self):
        pass

    def testRead(self):
        keys = sorted(self.dp.disk_dict.keys())
        assert keys[0] == 'sda', "Didn't detect disks correctly."
        assert keys[1] == 'sdb', "Didn't detect disks correctly."

class DiskTestCase(unittest.TestCase):
    """"""

class PartitionTestCase(unittest.TestCase):
    """"""

class VolGrp:
    name = None
    lpart = []
    llv = []

    def __init__(self, name, lpart):
        self.name = name
        self.lpart = lpart

    def addLv(self, name, size, partition_id):
        lv = LogVol(name, size, partition_id)
        lv.setVolGrpName(self.name)
        self.llv.append(lv)

    def getLv(self, name=None):
        if name:
            for lv in self.llv:
                if lv.name == name:
                    return lv
            return None
        else:
            return self.llv

    def getPart(self):
        return self.lpart
    
class LogVol:
    name = None
    volgrp_name = None
    part_id = None

    def __init__(self, name,size,part_id):
        self.name = name
        self.size = size
        self.part_id = part_id

    def setVolGrpName(self, name):
        self.volgrp_name = name

    def getVolGrpName(self):
        return self.volgrp_name

class Vol:
    mntpoint = None
    label = None
    fstype = None
    format = None

    def __init__(self, obj, mntpoint, label, fstype, format):
        self.obj = obj
        self.mntpoint = mntpoint
        self.label = label
        self.fstype = fstype
        self.format = format

         
    
#if __name__ == '__main__':

