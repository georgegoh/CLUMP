#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
import math
import parted
import subprocess
from common import *
import kusu.hardware.probe
import kusu.util.log as kusulog
from os.path import basename, exists
from kusu.util.errors import *
from partitiontool import checkAndMakeNode

logger = kusulog.getKusuLog('partitiontool.disk')

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
            try:
                pedDiskType = pedDevice.disk_probe()
            except parted.error:
                pedDiskType = parted.disk_type_get('msdos')
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
        
    def createPartition(self, size, fs_type=None, mountpoint=None, fill=None):
        """Add a partition to this disk.
           Parameters:
              1. size in bytes.
              2. type of partition(see partitionTypes).
              3. optional fs type(defaults to None).
           Returns an instance of Partition that represents the partition just
           created.
        """
        start_sector, end_sector, next_partition_type = self.__getStartEndSectors(size, fill)
        new_pedPartition = None

        try:
            constraint = self.pedDevice.constraint_any()
            if next_partition_type == 'PRIMARY':
                logger.debug('Creating new primary partition size=%d, fs=%s, mntpt=%s' %
                             (size, fs_type, mountpoint))
                new_pedPartition = self.pedDisk.partition_new(partitionTypes['PRIMARY'],
                                                          fs_type,
                                                          start_sector,
                                                          end_sector)

            elif next_partition_type == 'EXTENDED':
                # create and add extended partition to fill the rest of the disk.
                logger.debug('Creating new extended partition size=%d, fs=%s, mntpt=%s' %
                             (size, fs_type, mountpoint))
                extended_pedPartition = self.pedDisk.partition_new(
                                            partitionTypes['EXTENDED'],
                                            None,
                                            start_sector,
                                            self.length-1)
                self.pedDisk.add_partition(extended_pedPartition, constraint)
                self.__appendToPartitionDict(extended_pedPartition, None)
                # create logical partition.
                logger.debug('Creating new logical partition size=%d, fs=%s, mntpt=%s' %
                             (size, fs_type, mountpoint))
                new_pedPartition = self.pedDisk.partition_new(
                                        partitionTypes['LOGICAL'],
                                        fs_type,
                                        start_sector,
                                        end_sector)

            elif next_partition_type == 'LOGICAL':
                # create logical partition.
                logger.debug('Creating new logical partition size=%d, fs=%s, mntpt=%s' %
                             (size, fs_type, mountpoint))
                new_pedPartition = self.pedDisk.partition_new(
                                        partitionTypes['LOGICAL'],
                                        fs_type,
                                        start_sector,
                                        end_sector)

            else:
                raise UnknownPartitionTypeError, 'Cannot create unknown partition type'

        except parted.error, e:
            raise KusuError, e
    
        self.pedDisk.add_partition(new_pedPartition, constraint)
        new_partition = self.__appendToPartitionDict(new_pedPartition,
                                                     mountpoint)
        return new_partition

    def delPartition(self, partition_obj, keep_in_place=False):
        """Remove a partition from this disk. Argument is the Partition object
           itself.
        """
        if partition_obj.type == 'extended':
            last_part_num = len(self.partition_dict)
            logger.debug('Delete extended partition - total partitions: %d' % last_part_num)
            if self.__getPartitionType(last_part_num) == 'LOGICAL':
                raise CannotDeleteExtendedPartitionError, 'Logical Partition still exists.'

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
                partitions_to_move.append((partition.size_MB,
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
        """Get the type of partition for a given partition number. This applies
           to MSDOS-type partition tables.
        """
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

    def __getStartEndSectors(self, size, fill=False):
        """For a given size(in bytes), return a tuple of (start_sector,
           end_sector) that will accommodate this new partition.
        """
        selected_partition_num = 1
        last_part_num = self.pedDisk.get_last_partition_num()
        if last_part_num < 1: # no partitions found
            start_sector = 0
            if fill: size = disk.size - 1
        else:
            if last_part_num > self.pedDisk.get_primary_partition_count():
                pedPartition = self.pedDisk.next_partition()
                while pedPartition.num < last_part_num:
                    logger.debug('Iterating partition num: ' + \
                                 str(pedPartition.num))
                    # is this an unused partition?
                    if pedPartition.num == -1:
                        start_sector = pedPartition.geom.start
                        end_sector = start_sector + (size / \
                                     self.pedDisk.dev.sector_size) - 1
                        end_sector = self.__alignEndSector(end_sector)
                        logger.debug('Checking if the current partition is big enough.')
                        if end_sector <= pedPartition.geom.end:
                            if fill:
                                end_sector = pedPartition.geom.end
                                end_sector = self.__alignEndSector(end_sector)
                            return (start_sector, end_sector,
                                    self.__getPartitionType(selected_partition_num))
                        logger.debug('Current partition is not big enough for proposed size.')
                    # check for space between this and the next partition
                    logger.debug('Checking between partition %d and %d' % \
                                 (selected_partition_num, selected_partition_num+1))
                    this_end_sector = pedPartition.geom.end + 1
                    next_start_sector = self.pedDisk.next_partition(pedPartition).geom.start
                    start_sector = self.__alignStartSector(this_end_sector)
                    end_sector = start_sector + (size / \
                                 self.pedDisk.dev.sector_size) - 1
                    end_sector = self.__alignEndSector(end_sector)
                    if end_sector < next_start_sector:
                        if fill:
                            end_sector = self.__alignEndSector(next_start_sector - 1)
                        return (start_sector, end_sector,
                                self.__getPartitionType(selected_partition_num + 1))
                    
                    pedPartition = self.pedDisk.next_partition(pedPartition)
                    selected_partition_num = selected_partition_num + 1

            # is the last partition unused?
            lastPart = self.pedDisk.get_partition(last_part_num)
            if lastPart.type == parted.PARTITION_FREESPACE:
                start_sector = lastPart.geom.start
                selected_partition_num = last_part_num
                if fill:
                    end_sector = lastPart.geom.end
            else:
                start_sector = lastPart.geom.end + 1
                selected_partition_num = last_part_num + 1
                if fill:
                    end_sector = self.length - (self.heads * self.sectors) + 1
        start_sector = self.__alignStartSector(start_sector)
        if not fill:
            end_sector = start_sector + (size / self.sector_size) - 1
        end_sector = self.__alignEndSector(end_sector)
        # Not actually making a new partition, but using parted to catch any
        # size errors.
        try:
            new_part = self.pedDisk.partition_new(parted.PARTITION_PRIMARY,
                                                  fsTypes['ext3'],
                                                  start_sector,
                                                  end_sector)
        except parted.error, msg:
            if str(msg).startswith("Error: Can't have a partition " + \
                                        "outside the disk!"):
                if fill:
                    try:
                        end_sector = start_sector + (size / self.pedDisk.dev.sector_size) - 1
                        end_sector = self.__alignEndSector(end_sector)
                        new_part = self.pedDisk.partition_new(parted.PARTITION_PRIMARY,
                                                  fsTypes['ext3'],
                                                  start_sector,
                                                  end_sector)
                    except parted.error, msg:
                        if str(msg).startswith("Error: Can't have a partition " + \
                                               "outside the disk!"):
                            msg = "Requested partition size is too large to fit into " + \
                                  "the remaining space available on the disk."
                            raise PartitionSizeTooLargeError, msg
                else:
                    msg = "Requested partition size is too large to fit into " + \
                          "the remaining space available on the disk."
                    raise PartitionSizeTooLargeError, msg
 
        return (start_sector, end_sector,
                self.__getPartitionType(selected_partition_num))

    def convertStartSectorToCylinder(self, start_sector):
         cylinder = int(math.floor(
                        (float(start_sector) /
                        (self.pedDisk.dev.heads * self.pedDisk.dev.sectors)) \
                        + 1))
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
            try:
                self.pedDisk.commit()
            except parted.error, e:
                msg = str(e)
                if not msg.startswith('Warning: The kernel was unable ' + \
                                      'to re-read the partition table'):
                    raise e
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
    __getattr_dict = { 'start_sector' : 'self.pedPartition.geom.start',
                       'end_sector' : 'self.pedPartition.geom.end',
                       'length' : 'self.pedPartition.geom.length',
                       'part_type' : 'self.pedPartition.type_name',
                       'path' : 'self.getpath()',
                       'num' : 'self.pedPartition.num',
                       'start_cylinder' : 'self.disk.convertStartSectorToCylinder(self.start_sector)',
                       'end_cylinder' : 'self.disk.convertEndSectorToCylinder(self.end_sector)',
                       'type' : 'self.pedPartition.type_name',
                       'boot_flag' : 'self.pedPartition.get_flag(parted.PARTITION_BOOT)',
                       'lvm_flag' : 'self.pedPartition.get_flag(parted.PARTITION_LVM)',
                       'root_flag' : 'self.pedPartition.get_flag(parted.PARTITION_ROOT)',
                       'swap_flag' : 'self.pedPartition.get_flag(parted.PARTITION_SWAP)',
                       'raid_flag' : 'self.pedPartition.get_flag(parted.PARTITION_RAID)',
                       'size' : 'self.disk.sector_size * self.length',
                       'size_MB' : 'self.size / (1024 * 1024)'
                      }
    __setattr_dict = { 'start_sector' : "self.pedPartition.geom.set_start(long('%s'))",
                       'end_sector' : "self.pedPartition.geom.set_end(long('%s'))",
                       'boot_flag' : "self.pedPartition.set_flag(parted.PARTITION_BOOT, int('%s'))",
                       'lvm_flag' : "self.pedPartition.set_flag(parted.PARTITION_LVM, int('%s'))",
                       'root_flag' : "self.pedPartition.set_flag(parted.PARTITION_ROOT, int('%s'))",
                       'swap_flag' : "self.pedPartition.set_flag(parted.PARTITION_SWAP, int('%s'))",
                       'raid_flag' : "self.pedPartition.set_flag(parted.PARTITION_RAID, int('%s'))",
                       'fs_type' : "self.pedPartition.set_system(fsTypes['%s'])"
                     }

    def __init__(self, disk, pedPartition, mountpoint=None):
        self.disk = disk
        self.pedPartition = pedPartition
        self.mountpoint = mountpoint
        self.leave_unchanged = False
        self.on_disk = False
        self.do_not_format = False

    def getpath(self):
        """Get this partition's path by appending it's number to the disk's path.
           If the disk's path ends with a digit, then append a 'p' to the disk's
           path before appending the number.
        """
        if self.disk.path[-1].isdigit():
            return self.disk.path + 'p' + str(self.num)
        else:
            return self.disk.path + str(self.num)

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
        elif name in ['disk', 'pedPartition', 'mountpoint', 'leave_unchanged',
                      'on_disk', 'do_not_format']:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError, "%s instance does not have or cannot " + \
                                  "modify attribute '%s'" % \
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
            
        p = subprocess.Popen('mount -t %s %s %s %s' % (self.fs_type,
                                                       self.path,
                                                       mountpoint,
                                                       args),
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

        checkAndMakeNode(self.path)

        if self.fs_type == 'ext2':
            logger.info('FORMAT %s: Making ext2 fs on %s' % \
                        (self.path, self.path))
            mkfs = subprocess.Popen('mkfs.ext2 %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
        elif self.fs_type == 'ext3':
            logger.info('FORMAT %s: Making ext3 fs on %s' % \
                        (self.path, self.path))
            mkfs = subprocess.Popen('mkfs.ext3 %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()

            tune2fs = subprocess.Popen('tune2fs -c0 -i0 -O dir_index -ouser_xattr,acl %s' % self.path,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            tune2fs_out, status = tune2fs.communicate()
        elif self.fs_type == 'linux-swap':
            logger.info('FORMAT %s: Making swap fs on %s' % \
                        (self.path, self.path))
            mkfs = subprocess.Popen('mkswap %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
        elif self.lvm_flag:
            # do the lvm thing
            pass

