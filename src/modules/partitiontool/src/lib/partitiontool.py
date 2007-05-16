#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
"""This tool keeps track of the following entities in a system:
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
   The first 3 partitions created will be primary. Beyond the third partition,
   an extended partition will be created, and new partitions are added there.
   There will always be only one extended partition on a disk to contain the
   logical partitions. An extended partition cannot be deleted until all
   logical partitions are deleted.

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

"""
import math
import parted
import subprocess
from lvm import *
import kusu.hardware
import kusu.util.log as kusulog
from os.path import basename, exists
from kusu.util.kusuexceptions import *

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

logger = kusulog.getKusuLog('partitiontool')

class DiskProfile(object):
    """DiskProfile contains all information about the disks in a machine.

       Object variables:
       disk_dict - a dictionary referencing physical disks in a system. The key
                   is the device name, and the value is the Disk object. For
                   example, to get the first disk on the SCSI bus, we do this:

                      disk = diskProfile.disk_dict['sda']

       mountpoint_dict - a dictionary of mountpoints in a system. The key is
                          the mountpoint, and the value is the partition or
                          logical volume object that is mounted at the
                          mountpoint. To get the partition or logical volume
                          at a desired mountpoint, do this:

                             volume = diskProfile.mountpoint_dict['/boot']

       pv_dict - a dictionary of physical volumes in a system. The key is the
                 path, and the value is the PhysicalVolume (see LVM module)
                 object that the path refers to. To get the PhysicalVolume
                 object at a desired path, do this:

                    physicalVolume = diskProfile.pv_dict['/dev/sda2']

       lvg_dict - a dictionary of Logical Volume Groups in a system. The key is
                  the Logical Volume Group name, and the value is the
                  LogicalVolumeGroup (see LVM module) object that the name
                  refers to. To get the LogicalVolumeGroup object of a
                  particular name, do this:

                     logicalVolumeGroup = diskProfile.lvg_dict['LogVol00']

       lv_dict - a dictionary of Logical Volumes in a system. The key is the
                 Logical Volume name, and the value is the LogicalVolume
                 (see LVM module) object that the name refers to. To get a
                 LogicalVolume object of a desired name, do this:

                    logicalVolume = diskProfile.lv_dict['Scratch']
    """
    disk_dict = None
    mountpoint_dict = None
    pv_dict = None
    lvg_dict = None
    lv_dict = None
    fsType_dict = { 'ext2' : fsTypes['ext2'],
                    'ext3' : fsTypes['ext3'],
                    'physical volume' : None,
                    'software RAID' : None,
                    'linux-swap' : fsTypes['linux-swap'],
                    'fat32' : fsTypes['fat32']
                  }
    mountable_fsType = { 'ext2' : True,
                         'ext3' : True,
                         'physical volume' : False,
                         'software RAID' : False,
                         'linux-swap' : False,
                         'fat32' : True
                       }

    def __init__(self, fresh):
        """Initialises a DiskProfile object by doing the following:
           
        """
        global cmd_fifo
        self.disk_dict = {}
        self.mountpoint_dict = {}
        self.pv_dict = {}
        self.lvg_dict = {}
        self.lv_dict = {}

        logger.debug('Finding disks.') 
        disks_str = kusu.hardware.probe.getDisks().keys()
        for disk_str in disks_str:
            self.disk_dict[disk_str] = Disk('/dev/'+disk_str, self, fresh)
        logger.debug('Found disks.')

        logger.debug('Finding PVs.')
        # probe the physical volumes
        pv_probe_dict = probePhysicalVolumes()
        logger.debug('Probed PVs.')
        for pv_path, pv_prop_dict in pv_probe_dict.iteritems():
            partition = self.getPartitionFromPath(pv_path)
            partition.lvm_flag = 1
            pv = PhysicalVolume(partition)
            pv.on_disk = True
            pv.group = pv_prop_dict['group']
            self.pv_dict[pv_path] = pv
        logger.debug('Found PVs.')

        logger.debug('Finding LVGs.')
        # probe the logical volume groups
        lvg_probe_dict = probeLogicalVolumeGroups()
        for lvg_name, lvg_prop_dict in lvg_probe_dict.iteritems():
            pv_list = [pv for pv in self.pv_dict.itervalues() if pv.group == lvg_name]
            lvg = LogicalVolumeGroup(lvg_name, lvg_prop_dict['extent_size'], pv_list)
            self.lvg_dict[lvg_name] = lvg
        logger.debug('Found LVGs.')

        logger.debug('Finding LVs.')
        # probe logical volumes
        lv_probe_dict = probeLogicalVolumes()
        for lv_path, lv_prop_dict in lv_probe_dict.iteritems():
            lvg_name = lv_prop_dict['group']
            lvg = self.lvg_dict[lvg_name]
            lv_name = basename(lv_path)
            lv = LogicalVolume(lv_name, lvg, 0)
            lv.extents = lv_prop_dict['extents']
            lvg.lv_dict[lv_name] = lv
            self.lv_dict[lv_name] = lv
        logger.debug('Found LVs.')

    def getPartitionFromPath(self, path_str):
        i = -1
        path = path_str.strip()
        while path[i].isdigit():
            i = i-1
        i = i+1
        disk_path = path[:i]
        disk = self.disk_dict[basename(disk_path)]
        partition_number = int(path[i:])
        partition = disk.partition_dict[partition_number]
        return partition

    def delete(self, deviceObj):
        """Polymorphic delete function."""
        logger.debug('Device %s of type %s' % (str(deviceObj), str(type(deviceObj))))
        if type(deviceObj) is Partition:
            self.deletePartition(deviceObj)
        elif type(deviceObj) is LogicalVolumeGroup:
            self.deleteLogicalVolumeGroup(deviceObj)
        elif type(deviceObj) is LogicalVolume:
            self.deleteLogicalVolume(deviceObj)
        elif type(deviceObj) is Disk:
            raise KusuError, 'Cannot delete the selected device because it is a physical disk in the system.'
        else:
            raise KusuError, 'An internal error has occurred in the program. Please restart.'

    def newPartition(self, disk_id, size, fixed_size, fs_type, mountpoint):
        """Create a new partition."""
        # sanity check
        if mountpoint in self.mountpoint_dict.keys():
            raise DuplicateMountpointError, 'Assigned mountpoint already exists.'

        disk = self.disk_dict[disk_id]
        logger.debug('Add New Partition to Disk ID: ' + disk_id)
        if fs_type:
            logger.debug('FS type specified')
            new_partition = disk.createPartition(size, self.fsType_dict[fs_type], mountpoint)
        else:
            logger.debug('FS type not specified')
            new_partition = disk.createPartition(size, None, mountpoint)

        if mountpoint:
            self.mountpoint_dict[mountpoint] = new_partition
        logger.debug('Created mountpoint')

        # if it's a LVM physical volume, add it to the dict.
        if fs_type == 'physical volume':
            self.pv_dict[new_partition.path] = PhysicalVolume(new_partition, createNew=True)
            new_partition.lvm_flag = 1
        return new_partition

    def editPartition(self, partition_obj, size, fixed_size, fs_type, mountpoint):
        """Edit an existing partition."""
        logger.debug('Edit partition')
        backup_disk_id = basename(partition_obj.disk.path)
        backup_size = partition_obj.size
        backup_fs_type = partition_obj.fs_type
        backup_mountpoint = partition_obj.mountpoint

        self.deletePartition(partition_obj, keep_in_place=True)
        logger.debug('Original partition deleted. Remaining partitions: ' + str(partition_obj.disk.partition_dict.keys()))
        try:
            edited_partition = self.newPartition(backup_disk_id,
                                                 size,
                                                 fixed_size,
                                                 fs_type,
                                                 mountpoint)
            logger.debug('New partition created')

        except PartitionSizeTooLargeError, e:
            logger.debug('Exception raised when trying to edit partition %s' % partition_obj.path)
            logger.debug('There is no contiguous free space on disk to fit new size')
            self.newPartition(backup_disk_id,
                              backup_size,
                              False,
                              backup_fs_type,
                              backup_mountpoint)
            raise KusuError, "Couldn't find a contiguous free space to fit the new size. Try deleting other partitions."

        return edited_partition

    def deletePartition(self, partition_obj, keep_in_place=False):
        """Delete an existing partition."""
        # if partition is a physical volume.
        if partition_obj.path in self.pv_dict.keys():
            physicalVol = self.pv_dict[partition_obj.path]
            if physicalVol.group != None:
                raise PartitionIsPartOfVolumeGroupError, 'Partition cannot be deleted because it is part of a Logical Volume Group.'
            del self.pv_dict[partition_obj.path]

        if partition_obj.mountpoint in self.mountpoint_dict.keys():
            del self.mountpoint_dict[partition_obj.mountpoint]

        partition_obj.disk.delPartition(partition_obj, keep_in_place)


    def newLogicalVolumeGroup(self, name, extent_size, pv_list):
        """Create a new logical volume group."""
        # sanity checks
        if name in self.lvg_dict.keys():
            raise DuplicateNameError, 'Logical Volume Group name already exists.'
        unit = extent_size[-1]
        if unit.upper() != 'M':
            raise InvalidVolumeGroupExtentSizeError, 'Invalid Volume Group Extent Size.'
        _extent_size = int(extent_size[:-1])
        if _extent_size not in range(2, 512+1) and \
           _extent_size % 2:
            raise InvalidVolumeGroupExtentSizeError, 'Invalid Volume Group Extent Size.'

        # passed sanity checks, now do it!
        lvg = LogicalVolumeGroup(name, extent_size, pv_list, createNew=True)
        self.lvg_dict[name] = lvg
        return lvg


    def editLogicalVolumeGroup(self, lvg_obj, pv_obj_list):
        """Edit the list of physical volumes for
           a named existing logical volume group."""
        deleted_pvs = []
        inserted_pvs = []

        # deletetion pass
        for existing_pv in lvg_obj.pv_dict.itervalues():
            if existing_pv not in pv_obj_list:
                lvg.delPhysicalVolume(existing_pv)
        # insertion pass
        for pv in pv_obj_list:
            if pv.name not in lvg_obj.pv_dict.keys():
                lvg_obj.addPhysicalVolume(pv)

        return lvg_obj


    def deleteLogicalVolumeGroup(self, lvg):
        """Delete an existing logical volume group."""
        # sanity checks
        if lvg.lv_dict:
            raise PhysicalVolumeStillInUseError, 'Cannot delete Volume Group. Delete Logical Volumes first.'

        pv_list = lvg.pv_dict.values()

        for pv in pv_list:
            lvg.delPhysicalVolume(pv)

        self.lvg_dict.pop(lvg.name)

        lvg.delete()

    def newLogicalVolume(self, name, lvg, size_MB, fs_type=None, mountpoint=None):
        """Create a new logical volume."""
        # sanity checks
        if name in self.lv_dict.keys():
            raise DuplicateNameError, 'Logical Volume name already exists.'
        if mountpoint in self.mountpoint_dict.keys():
            raise DuplicateMountpointError, 'Assigned mountpoint already exists.'

        new_lv = lvg.createLogicalVolume(name, long(size_MB), fs_type, mountpoint)
        self.lv_dict[name] = new_lv

        if mountpoint:
            self.mountpoint_dict[mountpoint] = new_lv
        return new_lv


    def editLogicalVolume(self, lv, size_MB, fs_type, mountpoint):
        """Edit size for an existing logical volume."""
        size = size_MB * 1024 * 1024
        if size != lv.size:
            lv.resize(size_MB)

        if lv.fs_type == fs_type:
            lv.do_not_format = True
        lv.fs_type = fs_type
        lv.mountpoint = mountpoint


    def deleteLogicalVolume(self, lv):
        """Delete an existing logical volume."""
        if lv.mountpoint in self.mountpoint_dict.keys():
            del self.mountpoint_dict[lv.mountpoint]

        lv.group.delLogicalVolume(lv)


    def commit(self):
        for disk in self.disk_dict.itervalues():
            disk.commit()
        # now the partitions are actually created.
        self.executeLVMFifo()

    def executeLVMFifo(self):
        execFifo()

    def printLVMFifo(self):
        printFifo()

    def formatAll(self):
        for disk in self.disk_dict.itervalues():
            disk.formatAll()
        for lvg in self.lvg_dict.itervalues():
            lvg.formatAll()


class Disk(object):
    """Disk class represents a physical disk in the system.
       Attributes:
          a. profile - reference to the DiskProfile object that owns this disk.
          b. pedDisk - encapsulated instance of parted.PedDisk.
          c. partition_dict - dictionary of partitions on this disk.
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
    partition_dict = None
    leave_unchanged = None

    __getattr_dict = { 'length' : 'self.pedDevice.length',
                       'model' : 'self.pedDevice.model',
                       'path' : 'self.pedDevice.path',
                       'sector_size' : 'self.pedDevice.sector_size',
                       'size' : 'self.length * self.sector_size',
                       'type' : 'self.pedDevice.type',
                       'heads' : 'self.pedDevice.heads',
                       'sectors' : 'self.pedDevice.sectors',
                       'cylinders' : 'self.pedDevice.cylinders',
                       'pedDevice' : 'self.pedDisk.dev'
                     }

    def __init__(self, path, profile, fresh=False):
        self.profile = profile
        self.partition_dict = {}
        pedDevice = parted.PedDevice.get(path)
        self.leave_unchanged = False
        if fresh:
            pedDiskType = pedDevice.disk_probe()
            self.pedDisk = pedDevice.disk_new_fresh(pedDiskType)
        else:
            try:
                self.pedDisk = parted.PedDisk.new(pedDevice)
                for i in range(self.pedDisk.get_last_partition_num()):
                    pedPartition = self.pedDisk.get_partition(i+1)
                    new_partition = self.__appendToPartitionDict(pedPartition)
                    new_partition.on_disk = True
            except parted.error, e:
                if str(e).endswith('unrecognised disk label.'):
                    pedDiskType = parted.disk_type_get('msdos')
                    self.pedDisk = pedDevice.disk_new_fresh(pedDiskType)

    def __getattr__(self, name):
        if name in self.__getattr_dict.keys():
            return eval(self.__getattr_dict[name])
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __appendToPartitionDict(self, pedPartition, mountpoint=None):
        """Private bookkeeping function to create a new Partition object from
           a parted.PedPartition object and add it to the list of partitions on
           this disk.
        """
        new_partition = Partition(self, pedPartition, mountpoint)
        self.partition_dict[pedPartition.num] = new_partition
        return new_partition
        
    def createPartition(self, size, fs_type=None, mountpoint=None):
        """Add a partition to this disk.
           Parameters:
              1. size in bytes.
              2. type of partition(see partitionTypes).
              3. optional fs type(defaults to None).
           Returns an instance of Partition that represents the partition just created.
        """
        start_sector, end_sector, next_partition_type = self.__getStartEndSectors(size)
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

    def delPartition(self, partition_obj, keep_in_place=False):
        """Remove a partition from this disk. Argument is the Partition object
           itself.
        """
        # get ordered list of partition keys.
        partition_nums = sorted(self.partition_dict.keys())

        # delete the object from the dictionary and remove from pedDisk.
        deleted_partition_number = partition_obj.num
        deleted_partition = self.partition_dict[deleted_partition_number]
        del self.partition_dict[deleted_partition_number]
        self.pedDisk.delete_partition(deleted_partition.pedPartition)

        if keep_in_place: return

        partitions_to_move = []
        # partition numbers start from one, so it's a happy coincidence that
        # number of the partition that we want to delete is the index position
        # of the first partition that we want to move. How to move? First, we
        # delete...
        for part_key in partition_nums[deleted_partition_number:]:
            partition = self.partition_dict[part_key]
            if partition.on_disk:
                continue
            if partition.type != 'extended':
                partitions_to_move.append((partition.size,
                                           partition.fs_type,
                                           partition.mountpoint,
                                           partition.lvm_flag
                                          ))
            del self.partition_dict[part_key]
            if partition.type == 'primary' or partition.type == 'extended':
                self.pedDisk.delete_partition(partition.pedPartition)
            if partition.mountpoint in self.profile.mountpoint_dict.keys():
                self.profile.mountpoint_dict.pop(partition.mountpoint)

        # ... then we re-add the partitions.
        for part_details in partitions_to_move:
            new_partition = self.profile.newPartition(disk_id=basename(self.path),
                                                      size=part_details[0],
                                                      fixed_size=False,
                                                      fs_type=part_details[1],
                                                      mountpoint=part_details[2])
            new_partition.lvm_flag = part_details[3]

    def __getPartitionType(self, num):
        """Get the type of partition for a given partition number."""
        if num < 4:
            return 'PRIMARY'
        elif num == 4:
            return 'EXTENDED'
        else:
            return 'LOGICAL'

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
        selected_partition_num = 1
        last_part_num = self.pedDisk.get_last_partition_num()
        if last_part_num < 1: # no partitions found
            start_sector = 0
        else:
            if last_part_num > self.pedDisk.get_primary_partition_count():
                pedPartition = self.pedDisk.next_partition()
                while pedPartition.num < last_part_num:
                    logger.debug('Iterating partition num: ' + str(pedPartition.num))
                    if pedPartition.num == -1:
                        start_sector = pedPartition.geom.start
                        end_sector = start_sector + (size / self.pedDisk.dev.sector_size) - 1
                        end_sector = self.__alignEndSector(end_sector)
                        if end_sector <= pedPartition.geom.end:
                            return (start_sector, end_sector,
                                    self.__getPartitionType(selected_partition_num))
                    pedPartition = self.pedDisk.next_partition(pedPartition)
                    selected_partition_num = selected_partition_num + 1

            lastPart = self.pedDisk.get_partition(last_part_num)
            if lastPart.type == parted.PARTITION_FREESPACE:
                start_sector = lastPart.geom.start
                selected_partition_num = last_part_num
            else:
                start_sector = lastPart.geom.end + 1
                selected_partition_num = last_part_num + 1
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

        return (start_sector, end_sector, self.__getPartitionType(selected_partition_num))

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
        if not self.leave_unchanged:
            self.pedDisk.commit()
            for partition in self.partition_dict.itervalues():
                partition.on_disk = True

    def formatAll(self):
        if not self.leave_unchanged:
            for partition in self.partition_dict.itervalues():
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
          a. start_sector (writeable)
          b. end_sector (writeable)
          c. length
          d. part_type
          e. fs_type
          f. path
          g. num (e.g., num=1 for sda1, num=3 for sda3)
          h. start_cylinder
          i. end_cylinder
          j. type
          k. boot_flag
          l. lvm_flag
          m. root_flag
          n. swap_flag
          o. raid_flag
    """
    disk = None
    pedPartition = None
    mountpoint = None
    leave_unchanged = None
    on_disk = None
    do_not_format = None

    __getattr_dict = { 'start_sector' : 'self.pedPartition.geom.start',
                       'end_sector' : 'self.pedPartition.geom.end',
                       'length' : 'self.pedPartition.geom.length',
                       'part_type' : 'self.pedPartition.type_name',
                       'path' : 'self.disk.path + str(self.num)',
                       'num' : 'self.pedPartition.num',
                       'start_cylinder' : 'self.disk.convertStartSectorToCylinder(self.start_sector)',
                       'end_cylinder' : 'self.disk.convertEndSectorToCylinder(self.end_sector)',
                       'type' : 'self.pedPartition.type_name',
                       'boot_flag' : 'self.pedPartition.get_flag(parted.PARTITION_BOOT)',
                       'lvm_flag' : 'self.pedPartition.get_flag(parted.PARTITION_LVM)',
                       'root_flag' : 'self.pedPartition.get_flag(parted.PARTITION_ROOT)',
                       'swap_flag' : 'self.pedPartition.get_flag(parted.PARTITION_SWAP)',
                       'raid_flag' : 'self.pedPartition.get_flag(parted.PARTITION_RAID)',
                       'size' : 'self.disk.sector_size * self.length'
                      }
    __setattr_dict = { 'start_sector' : "self.pedPartition.geom.set_start(long('%s'))",
                       'end_sector' : "self.pedPartition.geom.set_end(long('%s'))",
                       'boot_flag' : "self.pedPartition.set_flag(parted.PARTITION_BOOT, int('%s'))",
                       'lvm_flag' : "self.pedPartition.set_flag(parted.PARTITION_LVM, int('%s'))",
                       'root_flag' : "self.pedPartition.set_flag(parted.PARTITION_ROOT, int('%s'))",
                       'swap_flag' : "self.pedPartition.set_flag(parted.PARTITION_SWAP, int('%s'))",
                       'raid_flag' : "self.pedPartition.set_flag(parted.PARTITION_RAID, int('%s'))"
                     }

    def __init__(self, disk, pedPartition, mountpoint=None):
        self.disk = disk
        self.pedPartition = pedPartition
        self.mountpoint = mountpoint
        self.leave_unchanged = False
        self.on_disk = False
        self.do_not_format = False

    def __getattr__(self, name):
        if name == 'fs_type':
            if self.pedPartition.fs_type:
                return self.pedPartition.fs_type.name
            else:
                return None
        elif name in self.__getattr_dict.keys():
            return eval(self.__getattr_dict[name])
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __setattr__(self, name, value):
        if name in self.__setattr_dict.keys():
            eval(self.__setattr_dict[name] % str(value))
        elif name in ['disk', 'pedPartition', 'mountpoint', 'leave_unchanged', 'on_disk', 'do_not_format']:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError, "%s instance does not have or cannot modify attribute '%s'" % \
                                  (self.__class__, name)

    def mount(self, mountpoint=None, readonly=False):
        """Mounts this partition. If no mountpoint is given, then the
           default mountpoint is used.
        """
        if not mountpoint:
            mountpoint = self.mountpoint
        args = ''
        if readonly:
            args = args + '-r'

        if not exists(mountpoint):
            err_msg = 'Mount point: %s does not exists' % mountpoint
            raise MountFailedError, err_msg
            
        p = subprocess.Popen('mount -t %s %s %s %s' % (self.fs_type, self.path, mountpoint, args),
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        returncode = p.returncode
        

        if returncode:
            err_msg =  'Unable to mount %s on %s'  % (self.path, mountpoint)
            logger.error(err_msg)
            raise MountFailedError, err_msg
        else:
            logger.info('Mounted %s on %s' % (self.path, mountpoint))

    def unmount(self):
        """Unmounts this partition."""
        p = subprocess.Popen('umount %s' % self.path,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()

    def format(self):
        """Format this partition with the FS type defined."""
        logger.info('FORMAT %s: Starting to format %s.' % (self.path, self.path))
        if self.leave_unchanged or self.do_not_format:
            return

        # temp solution, until ggoh refactor this
        logger.info('FORMAT %s: Checking if node already exists in /dev.' % self.path)
        import stat
        from os import mknod, makedev, path
        if not path.exists(self.path):
            logger.info('FORMAT %s: %s does not exist. Creating...' % (self.path, self.path))
            dev_basename = basename(self.disk.path)
            if dev_basename.startswith('sd'):
                alpha = 'abcdefghijklmnopqrstuvwxyz'
                li = [ x for x in alpha ]
                dev_major_num = 8
                dev_minor_multiplier = li.index(self.disk.path[-1])
                part_minor_num = 16 * dev_minor_multiplier + self.num
                
            elif dev_basename.startswith('hd'):
                if dev_basename.startswith('hda'):
                    dev_major_num = 3
                    part_minor_num = self.num
                elif dev_basename.startswith('hdb'):
                    dev_major_num = 3
                    part_minor_num = 31 + self.num
                elif dev_basename.startswith('hdc'):
                    dev_major_num = 22
                    part_minor_num = self.num
                elif dev_basename.startswith('hdd'):
                    dev_major_num = 22
                    part_minor_num = 31 + self.num
                elif dev_basename.startswith('hde'):
                    dev_major_num = 33
                    part_minor_num = self.num
                elif dev_basename.startswith('hdf'):
                    dev_major_num = 33
                    part_minor_num = 31 + self.num

            logger.info('FORMAT %s: Create block device, major: %s, minor: %s, path: %s' % \
                        (self.path, dev_major_num, part_minor_num, self.path))
            raw_dev_num = makedev(dev_major_num, part_minor_num)
            mknod(self.path, stat.S_IFBLK, raw_dev_num)

        if self.fs_type == 'ext2':
            logger.info('FORMAT %s: Making ext2 fs on %s' % (self.path, self.path))
            mkfs = subprocess.Popen('mkfs.ext2 %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
        elif self.fs_type == 'ext3':
            logger.info('FORMAT %s: Making ext3 fs on %s' % (self.path, self.path))
            mkfs = subprocess.Popen('mkfs.ext3 %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
        elif self.fs_type == 'linux-swap':
            logger.info('FORMAT %s: Making swap fs on %s' % (self.path, self.path))
            mkfs = subprocess.Popen('mkswap %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
        elif self.lvm_flag:
            # do the lvm thing
            pass

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

