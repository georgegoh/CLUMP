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
                self.__populateInitialPartitions()
            except parted.error, e:
                if str(e).endswith('unrecognised disk label.'):
                    pedDiskType = parted.disk_type_get('msdos')
                    self.pedDisk = pedDevice.disk_new_fresh(pedDiskType)

    def __populateInitialPartitions(self):
        for i in xrange(self.pedDisk.get_last_partition_num()):
            try:
                pedPartition = self.pedDisk.get_partition(i+1)
                new_partition = self.__appendToPartitionDict(pedPartition)
                new_partition.on_disk = True
            except parted.error, e:
                # partition numbers may not follow in sequence. So continue
                # searching and populating, even if some partition nos don't
                # exist.
                if str(e) == 'partition not found':
                    continue
 
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
        
    def createPartition(self, size, fs_type=None, mountpoint=None, fill=False):
        """Add a partition to this disk.
           Parameters:
              1. size in bytes.
              2. type of partition(see partitionTypes).
              3. optional fs type(defaults to None).
           Returns an instance of Partition that represents the partition just
           created.
        """
        start_sector, end_sector, next_partition_type = self.__getStartEndSectors(size)
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
                ext_part_size = (self.length - 1 - start_sector) * self.sector_size
                logger.debug('Creating new extended partition size=%d, fs=%s, mntpt=%s' %
                             (ext_part_size, fs_type, mountpoint))
                logger.debug('start sector %d end sector %d' % (start_sector, self.length-1))
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
                logger.debug('start sector %d end sector %d' % (start_sector, end_sector))
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

            self.pedDisk.add_partition(new_pedPartition, constraint)
            logger.debug('Added new partition to pedDisk')
            new_partition = self.__appendToPartitionDict(new_pedPartition,
                                                         mountpoint)
            if fill:
                self.maximizePartition(new_partition)
                self.__updatePartitionDict()
            return new_partition

        except parted.error, e:
            raise KusuError, e


    def maximizePartition(self, partition):
        logger.debug('Maximizing partition %d of disk %s' % (partition.num, self.path))
        constraint = self.pedDevice.constraint_any()
        self.pedDisk.maximize_partition(partition.pedPartition, constraint)


    def __updatePartitionDict(self):
        """Update this object's partition dictionary."""
        part_list = self.partition_dict.values()
        self.partition_dict.clear()
        for partition in part_list:
            self.partition_dict[partition.num] = partition


    def delPartition(self, partition_obj, keep_in_place=False):
        """Remove a partition from this disk. Argument is the Partition object
           itself.
        """
        if partition_obj.leave_unchanged:
            raise CannotDeleteExtendedPartitionError, 'Leave unchanged flag is set.'

        if partition_obj.type == 'extended':
            last_part_num = len(self.partition_dict)
            logger.debug('Delete extended partition - total partitions: %d' % last_part_num)
            if self.__getPartitionType(last_part_num) == 'LOGICAL':
                raise CannotDeleteExtendedPartitionError, 'Logical Partition still exists.'

        # get ordered list of partition keys.
        partition_nums = sorted(self.partition_dict.keys())

        # delete the object from the dictionary and remove from pedDisk.
#        logger.debug('Delete partition_obj.num = %d' % partition_obj.num)
#        logger.debug('Delete disk partition_dict keys: %s' % str(self.partition_dict.keys()))
        deleted_partition_number = partition_obj.num
        if not self.partition_dict.has_key(deleted_partition_number): return
        deleted_partition = self.partition_dict[deleted_partition_number]
        del self.partition_dict[deleted_partition_number]
        self.pedDisk.delete_partition(deleted_partition.pedPartition)

#        for key in self.partition_dict.iterkeys():
#            logger.debug('After delete, key=%d, part.num=%d' % (key, self.partition_dict[key].num))

        self.__updatePartitionDict()

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
                                                      size_MB=part_details[0],
                                                      fixed_size=False,
                                                      fs_type=part_details[1],
                                                      mountpoint=part_details[2])
            new_partition.lvm_flag = part_details[3]

    def __getPartitionType(self, num):
        """Get the type of partition for a given partition number. This applies
           to MSDOS-type partition tables.
        """
        max_primary_partition_cnt = self.pedDisk.max_primary_partition_count
        if num < max_primary_partition_cnt:
            return 'PRIMARY'
        elif num == max_primary_partition_cnt:
            return 'EXTENDED'
        else:
            return 'LOGICAL'

    def __getNextPartitionType(self):
        """Get the next assignable partition number, and whether it should be an
           extended partition or not.
        """
        last_partition_num = self.pedDisk.get_last_partition_num()
        max_primary_partition_cnt = self.pedDisk.max_primary_partition_count
        if last_partition_num == (max_primary_partition_cnt-1):
            next_partition_num = max_primary_partition_cnt+1
            return 'EXTENDED'
        elif last_partition_num > max_primary_partition_cnt:
            return 'LOGICAL'
        else:
            return 'PRIMARY'

    def __sortBySectors(self, part_list):
        """Bubble sort the partitions by start_sector. A disk will not have
           many partitions, so this algo is alright."""
        pl = list(part_list)
        for i in reversed(xrange(1, len(pl))):
            for j in xrange(i):
                if pl[j].start_sector > pl[i].start_sector:
                    tmp = pl[j]
                    pl[j] = pl[i]
                    pl[i] = tmp
        return pl

    def __sectorIsUsed(self, sector):
        """Check if sector falls in any of the existing primary or logical partitions."""
        partition_list = self.partition_dict.values()
        partition_list = [p for p in partition_list if not p.part_type=='extended']
        partition_list = self.__sortBySectors(partition_list)
        logger.debug('partition list: %s' % str([ p.num for p in partition_list ]))
        for partition in partition_list:
            logger.debug('check sector: %d, part.start: %d part.end: %d' % \
                         (sector, partition.start_sector, partition.end_sector))
            if sector >= partition.start_sector and sector <= partition.end_sector:
                logger.debug('check sector is being used')
                return True
        return False

    def __rangeHasUsedSectors(self, start, end):
        """Check if any current partitions fall(wholly or partially) within
           the given range.
        """
        partition_list = self.partition_dict.values()
        partition_list = [p for p in partition_list if not p.part_type=='extended']
        for p in partition_list:
            if p.start_sector >= start and p.start_sector <= end or \
               p.end_sector >= start and p.end_sector <= end:
                return True
        return False

    def __getStartEndSectors(self, size, fill=False):
        """For a given size(in bytes), return a tuple of (start_sector,
           end_sector, type) that will accommodate this new partition.
        """
        primary = []
        extended = None
        logical = []
        for partition in self.partition_dict.values():
            if partition.part_type == 'primary':
                primary.append(partition)
            elif partition.part_type == 'extended':
                extended = partition
            else:
                logical.append(partition)

        # No writing on the first track.
        start_sector = self.sectors
        end_sector = start_sector + (size / self.sector_size) - 1
        end_sector = self.__alignEndSector(end_sector)
        partition_list = [ p for p in self.partition_dict.values() if p.part_type != 'extended' ]
        partition_list = self.__sortBySectors(partition_list)
        nextPartition = None
        for partition in partition_list:
            if self.__sectorIsUsed(start_sector) or self.__sectorIsUsed(end_sector) or \
               self.__rangeHasUsedSectors(start_sector, end_sector):
                start_sector = self.__alignStartSector(partition.end_sector + 1)
#                logger.debug('sector is in use... using new start %d' % start_sector)
                end_sector = start_sector + (size / self.sector_size) - 1
                end_sector = self.__alignEndSector(end_sector)
                continue
            else:
                nextPartition = partition
                break

        logger.debug('new start: %d end: %d' % (start_sector, end_sector))
        if end_sector > self.length:
            msg = "Requested partition size is too large to fit into " + \
                  "the remaining space available on the disk."
            raise PartitionSizeTooLargeError, msg
 
        if len(primary) < (self.pedDisk.max_primary_partition_count-1):
            return start_sector, end_sector, 'PRIMARY'
        elif not extended:
            return start_sector, end_sector, 'EXTENDED'
        else:
            return start_sector, end_sector, 'LOGICAL'

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
          p. native_type
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
                       'native_type' : 'Partition.native_type_dict[self.pedPartition.native_type]',
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

    def __lt__(self, other):
        return self.num < other.num

    def __le__(self, other):
        return self.num <= other.num

    def __gt__(self, other):
        return self.num > other.num

    def __ge__(self, other):
        return self.num >= other.num

    def __eq__(self, other):
        if not hasattr(other, 'num'):
            return False
        return self.num == other.num

    def __ne__(self, other):
        if not hasattr(other, 'num'):
            return True
        return self.num != other.num

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
        elif name in ['disk', 'pedPartition', 'mountpoint', 'mountedpoint', 'leave_unchanged',
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
            err_msg = 'Mount point: %s does not exist' % mountpoint
            raise MountFailedError, err_msg

        fs_arg = ''
        if self.fs_type: fs_arg = '-t %s' % self.fs_type            
        p = subprocess.Popen('mount %s %s %s %s' % (fs_arg,
                                                       self.path,
                                                       mountpoint,
                                                       args),
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        returncode = p.returncode
        self.mountedpoint = mountpoint

        if returncode:
            err_msg =  'Unable to mount %s on %s'  % (self.path, mountpoint)
            logger.error(err_msg + ' Reason: ' + err)
            raise MountFailedError, err_msg
        else:
            logger.info('Mounted %s on %s' % (self.path, mountpoint))

    def unmount(self):
        """Unmounts this partition."""
        p = subprocess.Popen('umount %s' % self.mountedpoint,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        returncode = p.returncode
        if returncode:
            err_msg =  'Unable to unmount %s from %s'  % (self.path, self.mountedpoint)
            logger.error(err_msg + err)
            raise MountFailedError, err_msg
        else:
            logger.info('Unmounted %s from %s' % (self.path, self.mountedpoint))


    def format(self):
        """Format this partition with the FS type defined."""
        logger.info('FORMAT %s: Starting to format %s.' % (self.path, self.path))
        if self.leave_unchanged or self.do_not_format:
            logger.info('Not formatting %s, respecting flag' % self.path)
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

    native_type_dict = { 0 : 'Empty',
        1 : 'FAT12',
        2 : 'XENIX root',
        3 : 'XENIX usr',
        4 : 'FAT16 <32M',
        5 : 'Extended',
        6 : 'FAT16',
        7 : 'HPFS/NTFS',
        8 : 'AIX',
        9 : 'AIX bootable',
        10 : 'O/S 2 Boot Manager',
        0xb : 'W95 FAT32',
        0xc : 'W95 FAT32 (LBA)',
        0xe : 'W95 FAT16 (LBA)',
        0xf : "W95 Ext'd (LBA)",
        0x10 : 'OPUS',
        0x11 : 'Hidden FAT12',
        0x12 : 'Compaq diagnostic',
        0x14 : 'Hidden FAT16 < 32M',
        0x16 : 'Hidden FAT16',
        0x17 : 'Hidden HPFS/NTFS',
        0x18 : 'AST SmartSleep',
        0x1b : 'Hidden W95 FAT32',
        0x1c : 'Hidden W95 FAT32 (LBA)',
        0x1e : 'Hidden W95 FAT16 (LBA)',
        0x24 : 'NEC DOS',
        0x39 : 'Plan 9',
        0x3c : 'PartitionMagic',
        0x40 : 'Venix 80286',
        0x41 : 'PPC PReP Boot',
        0x42 : 'SFS',
        0x4d : 'QNX4.x',
        0x4e : 'QNX4.x 2nd part',
        0x4f : 'QNX4.x 3rd part',
        0x50 : 'OnTrack DM',
        0x51 : 'OnTrack DM6 Aux',
        0x52 : 'CP/M',
        0x53 : 'OnTrack DM6 Aux',
        0x54 : 'OnTrackDM6',
        0x55 : 'EZ-Drive',
        0x56 : 'Golden Bow',
        0x5c : 'Priam Edisk',
        0x61 : 'SpeedStor',
        0x63 : 'GNU HURD',
        0x64 : 'Novell Netware 286',
        0x65 : 'Novell Netware 386',
        0x70 : 'DiskSecure Multi',
        0x75 : 'PC/IX',
        0x80 : 'Old Minix',
        0x81 : 'Minix',
        0x82 : 'Linux swap',
        0x83 : 'Linux',
        0x84 : 'OS/2 hidden C:',
        0x85 : 'Linux extended',
        0x86 : 'NTFS volume set',
        0x87 : 'NTFS volume set',
        0x88 : 'Linux plaintext',
        0x8e : 'Linux LVM',
        0x93 : 'Amoeba',
        0x94 : 'Amoeba BBT',
        0x9f : 'BSD/OS',
        0xa0 : 'IBM Thinkpad hibernation',
        0xa5 : 'FreeBSD',
        0xa6 : 'OpenBSD',
        0xa7 : 'NeXTSTEP',
        0xa8 : 'Darwin UFS',
        0xa9 : 'NetBSD',
        0xab : 'Darwin boot',
        0xb7 : 'BSDI fs',
        0xb8 : 'BSDI swap',
        0xbb : 'Boot Wizard hidden',
        0xbe : 'Solaris boot',
        0xbf : 'Solaris',
        0xc1 : 'DRDOS/sec (FAT-12)',
        0xc4 : 'DRDOS/sec (FAT-16)',
        0xc6 : 'DRDOS/sec (FAT-32)',
        0xc7 : 'Syrinx',
        0xda : 'Non-FS data',
        0xdb : 'CP/M / CTOS',
        0xde : 'Dell Utility',
        0xdf : 'BootIt',
        0xe1 : 'DOS access',
        0xe3 : 'DOS R/O',
        0xe4 : 'SpeedStor',
        0xeb : 'BeOS fs',
        0xee : 'EFI GPT',
        0xef : 'EFI (FAT-12/16/32)',
        0xf0 : 'Linux/PA-RISC boot',
        0xf1 : 'SpeedStor',
        0xf4 : 'SpeedStor',
        0xf2 : 'DOS secondary',
        0xfd : 'Linux raid auto',
        0xfe : 'LANstep',
        0xff : 'BBT'
    }
