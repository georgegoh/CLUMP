#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool.
#
# Copyright 2007 Platform Computing Inc.
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
from common import *
from path import path
import kusu.hardware.probe
import kusu.util.log as kusulog
from os.path import basename, exists
from kusu.util.errors import *
from kusu.util.tools import mkdtemp
from kusu.util.testing import runCommand

logger = kusulog.getKusuLog('partitiontool')
#import logging
#kusulog.getKusuLog().handlers[0].addFilter(logging.Filter('kusu.partitiontool'))

def checkAndMakeNode(devpath):
    """
    Give me a path to a disk device and I will check if it exists. If it
    doesn't, then I will create it according to the numbering schema
    by lanana.
    """
    # temp solution, until ggoh refactor this
    logger.info('FORMAT %s: Checking if node already exists in /dev.' % \
                devpath)
    import stat
    from os import mknod, makedev, path
    if not path.exists(devpath):
        logger.info('FORMAT %s: %s does not exist. Creating...' % \
                    (devpath, devpath))
        dev_basename = basename(devpath)

        if devpath[-1] in '1234567890':
            if devpath[-2] in '1234567890': num = int(devpath[-2:])
            else: num = int(devpath[-1])
        else: num = 0

        # Remap /dev/sr# to /dev/scd# - /dev/sr is legacy and is replaced with
        # /dev/scd. (http://www.lanana.org/docs/device-list/devices.txt)
        if dev_basename.startswith('sr') or dev_basename.startswith('scd'):
            dev_major_num = 11
            part_minor_num = num

        elif dev_basename.startswith('sd'):
            alpha = 'abcdefghijklmnopqrstuvwxyz'
            li = [ x for x in alpha ]
            dev_major_num = 8
            if num==0: dev_minor_multiplier = li.index(devpath[-1])
            else: dev_minor_multiplier = li.index(devpath[-2])
            part_minor_num = 16 * dev_minor_multiplier + num

        elif dev_basename.startswith('hd'):
            # first IDE interface
            if dev_basename.startswith('hda'):
                dev_major_num = 3
                part_minor_num = num
            elif dev_basename.startswith('hdb'):
                dev_major_num = 3
                part_minor_num = 64 + num
            # second IDE interface
            elif dev_basename.startswith('hdc'):
                dev_major_num = 22
                part_minor_num = num
            elif dev_basename.startswith('hdd'):
                dev_major_num = 22
                part_minor_num = 64 + num
            # third IDE interface
            elif dev_basename.startswith('hde'):
                dev_major_num = 33
                part_minor_num = num
            elif dev_basename.startswith('hdf'):
                dev_major_num = 33
                part_minor_num = 64 + num
            # fourth IDE interface
            elif dev_basename.startswith('hdg'):
                dev_major_num = 34
                part_minor_num = num
            elif dev_basename.startswith('hdh'):
                dev_major_num = 34
                part_minor_num = 64 + num
            # fifth IDE interface
            elif dev_basename.startswith('hdi'):
                dev_major_num = 56
                part_minor_num = num
            elif dev_basename.startswith('hdj'):
                dev_major_num = 56
                part_minor_num = 64 + num
            # sixth IDE interface
            elif dev_basename.startswith('hdk'):
                dev_major_num = 57
                part_minor_num = num
            elif dev_basename.startswith('hdl'):
                dev_major_num = 57
                part_minor_num = 64 + num

        # dummy data put here for test. Note that this
        # will break hdk(which is the 11th ide interface).
        elif dev_basename.startswith('loop'):
            dev_major_num = 57
            part_minor_num = num

        else:
            raise UnknownDeviceError, "Cannot create %s - don't know the " + \
                                      "major/minor number scheme." % basepath

        logger.info('FORMAT %s: Create block device, major: %s, minor: %s, path: %s' % \
                    (devpath, dev_major_num, part_minor_num, devpath))
        raw_dev_num = makedev(dev_major_num, part_minor_num)
        mknod(devpath, stat.S_IFBLK, raw_dev_num)


from disk import *
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
    fsType_dict = { 'ext2' : fsTypes['ext2'],
                    'ext3' : fsTypes['ext3'],
                    'physical volume' : None,
                    'software RAID' : None,
                    'linux-swap' : fsTypes['linux-swap'],
                    'fat32' : fsTypes['fat32'],
                    'ntfs'  : fsTypes['ntfs']
                  }
    mountable_fsType = { 'ext2' : True,
                         'ext3' : True,
                         'physical volume' : False,
                         'software RAID' : False,
                         'linux-swap' : False,
                         'fat32' : True,
                         'ntfs' : False
                       }

    def __diskDictStr(self):
        s = ''
        for k in sorted(self.disk_dict.keys()):
            disk = self.disk_dict[k]
            s += str(disk) + '\n'
            for p in sorted(disk.partition_dict.keys()):
                part = disk.partition_dict[p]
                s += str(part) + '\n'
        return s

    def __lvmStr(self, dict):
        s = ''
        for k in sorted(dict.keys()):
            v = dict[k]
            s += str(v) + '\n'
        return s

    def __mntStr(self):
        s = ''
        for k in self.mountpoint_dict:
            s += k + ' - ' + self.mountpoint_dict[k].path + '\n'
        return s

    def __str__(self):
        from pprint import pformat
        s = 'Disk Dictionary:\n' + self.__diskDictStr()
        s = s + '\nPhysical Volume Dictionary:\n' + self.__lvmStr(self.pv_dict)
        s = s + '\nLogical Volume Group Dictionary:\n' + self.__lvmStr(self.lvg_dict)
        s = s + '\nLogical Volume Dictionary:\n' + self.__lvmStr(self.lv_dict)
        s = s + '\nMountpoints:\n' + self.__mntStr()
        return s

    def __init__(self, fresh, test=None, probe_fstab=True):
        """Initialises a DiskProfile object by doing the following:
           
        """
        global cmd_fifo
        self.disk_dict = {}
        self.mountpoint_dict = {}
        self.pv_dict = {}
        self.lvg_dict = {}
        self.lv_dict = {}

        import lvm202
        lvm202.activateAllVolumeGroups()
        
        if test:
            self.populateDiskProfileTest(fresh, test)
        else:
            self.populateDiskProfile(fresh, probe_fstab)

    def probeLVMEntities(self):
        logger.debug('Probing PVs.')
        pv_probe_dict = probePhysicalVolumes()
        logger.debug('Probing VGs.')
        lvg_probe_dict = probeLogicalVolumeGroups()
        logger.debug('Probing LVs.')
        lv_probe_dict = probeLogicalVolumes()
        return pv_probe_dict, lvg_probe_dict, lv_probe_dict

    def populateDiskProfileTest(self, fresh, test):
        testDisk = Disk('/dev/'+test, self, fresh)
        self.disk_dict[test] = testDisk
        if testDisk.partition_dict:
            pv_probe_dict, lvg_probe_dict, lv_probe_dict = self.probeLVMEntities()
            for partition in testDisk.partition_dict.values():
                if partition.lvm_flag and pv_probe_dict.has_key(partition.path):
                    pv = PhysicalVolume(partition)
                    pv.on_disk = True
                    pv_prop_dict = pv_probe_dict[partition.path]
                    pv.group = pv_prop_dict['group']
                    self.pv_dict[partition.path] = pv

                    if self.lvg_dict.has_key(pv.group):
                        self.lvg_dict[pv.group].addPhysicalVolume(pv)
                    else:
                        lvg_prop_dict = lvg_probe_dict[pv.group]
                        lvg_name = pv.group
                        lvg = LogicalVolumeGroup(lvg_name, 
                                                 lvg_prop_dict['extent_size'],
                                                 [pv])
                        self.lvg_dict[lvg_name] = lvg

                    for lv_path, lv_prop_dict in lv_probe_dict.iteritems():
                        lvg_name = lv_prop_dict['group']
                        if self.lvg_dict.has_key(lvg_name):
                            lvg = self.lvg_dict[lvg_name]
                            lv_name = basename(lv_path)
                            lv = LogicalVolume(lv_name, lvg, 0)
                            lv.extents = lv_prop_dict['extents']
                            lvg.lv_dict[lv_name] = lv
                            self.lv_dict[lv_name] = lv


    def populateDiskProfile(self, fresh, probe_fstab):
        self.disk_dict = self.__findDisksAndCreateDictionary(fresh)
        pv_probe_dict, lvg_probe_dict, lv_probe_dict = self.probeLVMEntities()

        if fresh:
            self.__wipeLVMObjects(pv_probe_dict,
                                  lvg_probe_dict,
                                  lv_probe_dict)
            # re-probe
            pv_probe_dict = {}
            lvg_probe_dict = {}
            lv_probe_dict = {}

            for disk in self.disk_dict.itervalues():
                for partition in disk.partition_dict.itervalues():
                    disk.delPartition(partition)

        self.__createLVMObjects(pv_probe_dict,
                                lvg_probe_dict,
                                lv_probe_dict)

        if not fresh:
            runCommand('lvm vgchange -ay')
            if probe_fstab:
                self.populateMountPoints()


    def __findDisksAndCreateDictionary(self, fresh):
        logger.debug('Finding disks.')
        disk_dict = {}
        disks_str = kusu.hardware.probe.getDisks().keys()
        for disk_str in disks_str:
            disk_dict[disk_str] = Disk('/dev/'+disk_str, self, fresh)
        logger.debug('Found disks.')
        return disk_dict


    def populateMountPoints(self, fstab_path='etc/fstab'):
        """Look through the partitions and LV's to determine mountpoints."""
        logger.debug('Populate mount points.')
        # Check the partitions and logical volumes
        m_parts = self.getMountablePartitions()
        m_lvs = self.getMountableLVs()
        m_list = m_parts + m_lvs
        for p in m_list:
            found, loc = self.lookForFstab(p, fstab_path)
            if found:
                dev_map = self.extractFstabToDevices(p, loc)
                for dev, mntpnt in dev_map.iteritems():
                    vol = self.findDevice(dev)
                    if vol:
                        self.mountpoint_dict[mntpnt] = vol
                        vol.mountpoint = mntpnt
                # Ok, we've parsed the first fstab we found, job done.
                return

    def extractFstabToDevices(self, device, loc):
        """For linux-type systems."""
        # get the temp directory to mount the device.
        mntpnt = mkdtemp()

        try:
            # mount the device.
            device.mount(mountpoint=mntpnt, readonly=True)
            fstab_loc = str(path(mntpnt) / path(loc))
            # open fstab file and filter out comments.
            fstab = open(fstab_loc)
            f_lines = [l for l in fstab.readlines() if \
                       len(l.strip()) and l.strip()[0] != '#']
            fstab.close()
            device.unmount()

            device_map = {}
            for l in f_lines:
                try:
                    # look for a mountable entry and append it to our dict.
                    dev, mntpnt, fs_type = l.split()[:3]
                    if fs_type in self.mountable_fsType.keys():
                        device_map[dev] = mntpnt
                except ValueError, e:
                    raise KusuError, str(e) + ' Offending line: \n' + l
        except MountFailedError:
            pass
        return device_map

    def findDevice(self, dev):
        """Find a device."""
        logger.debug('find device %s', dev)
        if dev.startswith('UUID='):
            # TODO find device with matching UUID.
            logger.warning('fstab file uses UUID signatures. This is not yet supported.')

        if dev.startswith('LABEL='):
            # TODO find device with matching label.
            logger.warning('Encountered label, but is not yet supported.')

        # Check physical partitions.
        for d in self.disk_dict.itervalues():
            if dev.startswith(d.path):
                for p in d.partition_dict.itervalues():
                    if dev == p.path:
                        return p

        # Check logical volumes.
        for lv in self.lv_dict.itervalues():
            if dev == lv.path:
                return lv

        return None

    def getMountablePartitions(self):
        logger.debug('get mountable partitions')
        mountable_parts = []
        for disk in self.disk_dict.itervalues():
            for p in disk.partition_dict.itervalues():
                if self.mountable_fsType.has_key(p.fs_type) and \
                   self.mountable_fsType[p.fs_type]:
                    mountable_parts.append(p)
        return mountable_parts

    def getMountableLVs(self):
        logger.debug('get mountable LVs')
        mountable_lvs = []
        mntpnt = mkdtemp()
        for lv in self.lv_dict.itervalues():
            try:
                logger.debug('Mounting %s' % lv.path)
                lv.mount(mountpoint=mntpnt, readonly=True)
                logger.debug('Unmounting %s' % lv.path)
                lv.unmount()
                mountable_lvs.append(lv)
            except MountFailedError:
                continue
        return mountable_lvs

    def lookForFstab(self, partition, fstab_path='etc/fstab'):
        """If found, returns a tuple (True, <location>),
           Else, returns (False, None)
        """
        logger.debug('Looking for fstab in %s' % partition.path)
        mntpnt = mkdtemp()
        partition.mount(mountpoint=mntpnt, readonly=True)
        loc = path(mntpnt) / path(fstab_path)
        loc_exists = loc.exists()
        partition.unmount()
        if loc_exists:
            logger.debug('Fstab found')
            return True, fstab_path
        return False, None

    def __wipeLVMObjects(self, pv_probe_dict, lvg_probe_dict, lv_probe_dict):
        logger.debug('Wiping LVs.')
        for lv_path in lv_probe_dict.iterkeys():
            LogicalVolume.remove(lv_path)
        logger.debug('Wiping VGs.')
        for lvg_name in lvg_probe_dict.iterkeys():
            LogicalVolumeGroup.remove(lvg_name)
        logger.debug('Wiping PVs.')
        for pv_path in pv_probe_dict.iterkeys():
            PhysicalVolume.remove(pv_path)

    def __createLVMObjects(self, pv_probe_dict, lvg_probe_dict, lv_probe_dict):
        logger.debug('Creating PV objects.')
        for pv_path, pv_prop_dict in pv_probe_dict.iteritems():
            partition = self.getPartitionFromPath(pv_path)
            partition.lvm_flag = 1
            pv = PhysicalVolume(partition)
            pv.on_disk = True
            pv.group = pv_prop_dict['group']
            self.pv_dict[pv_path] = pv

        logger.debug('Creating VG objects.')
        for lvg_name, lvg_prop_dict in lvg_probe_dict.iteritems():
            pv_list = [pv for pv in self.pv_dict.itervalues() \
                              if pv.group == lvg_name]
            lvg = LogicalVolumeGroup(lvg_name, lvg_prop_dict['extent_size'],
                                     pv_list)
            lvg.on_disk = True
            self.lvg_dict[lvg_name] = lvg

        logger.debug('Creating LV objects.')
        for lv_path, lv_prop_dict in lv_probe_dict.iteritems():
            lvg_name = lv_prop_dict['group']
            lvg = self.lvg_dict[lvg_name]
            lv_name = basename(lv_path)
            lv = LogicalVolume(lv_name, lvg, 0)
            lv.on_disk = True
            lv.extents = lv_prop_dict['extents']
            lvg.lv_dict[lv_name] = lv
            self.lv_dict[lv_name] = lv

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

    def delete(self, deviceObj, keep_in_place=False):
        """Polymorphic delete function."""
        logger.debug('Device %s' % str(deviceObj))
        if type(deviceObj) is Partition:
            if deviceObj.leave_unchanged:
                logger.info('Device has been flagged to be unchangeable')
                return
            self.deletePartition(deviceObj, keep_in_place)
        elif type(deviceObj) is LogicalVolumeGroup:
            self.deleteLogicalVolumeGroup(deviceObj)
        elif type(deviceObj) is LogicalVolume:
            if deviceObj.leave_unchanged:
                logger.info('Device has been flagged to be unchangeable')
                return
            self.deleteLogicalVolume(deviceObj)
        elif type(deviceObj) is Disk:
            raise KusuError, 'Cannot delete the selected device because ' + \
                             'it is a physical disk in the system.'
        else:
            raise KusuError, 'An internal error has occurred in the ' + \
                             'program. Please restart.'

    def newPartition(self, disk_id, size_MB, fixed_size, fs_type, mountpoint, fill=False):
        """Create a new partition."""
        # sanity check
        if self.mountpoint_dict.has_key(mountpoint):
            raise DuplicateMountpointError, 'Assigned mountpoint ' + \
                                            'already exists.'
        size = size_MB * 1024 * 1024
        disk = self.disk_dict[disk_id]
        logger.debug('Add New Partition to Disk ID: ' + disk_id)
        if fs_type:
            logger.debug('FS type specified: %s' % fs_type)
            new_partition = disk.createPartition(size,
                                                 self.fsType_dict[fs_type],
                                                 mountpoint,
                                                 fill)
        else:
            logger.debug('FS type not specified')
            new_partition = disk.createPartition(size, None, mountpoint, fill)

        if mountpoint:
            self.mountpoint_dict[mountpoint] = new_partition
        logger.debug('Created mountpoint')

        # if it's a LVM physical volume, add it to the dict.
        if fs_type == 'physical volume':
            self.pv_dict[new_partition.path] = PhysicalVolume(new_partition,
                                                              createNew=True)
            new_partition.lvm_flag = 1
        return new_partition

    def editPartition(self, partition_obj, size_MB, fixed_size, fs_type, mountpoint):
        """Edit an existing partition."""
        logger.debug('Edit partition %s' % partition_obj.path)
        if size_MB == partition_obj.size_MB:
            partition_obj.mountpoint = mountpoint
            partition_obj.fs_type = fs_type
            return partition_obj

        backup_disk_id = basename(partition_obj.disk.path)
        backup_size = partition_obj.size_MB
        backup_fs_type = partition_obj.fs_type
        backup_mountpoint = partition_obj.mountpoint

        
        self.deletePartition(partition_obj, keep_in_place=True)
        logger.debug('Original partition deleted. Remaining partitions: ' + \
                     str(partition_obj.disk.partition_dict.keys()))
        try:
            edited_partition = self.newPartition(backup_disk_id,
                                                 size_MB,
                                                 fixed_size,
                                                 fs_type,
                                                 mountpoint)
            logger.debug('New partition created')

        except PartitionSizeTooLargeError, e:
            logger.debug('Exception raised when trying to edit partition %s' % \
                         partition_obj.path)
            logger.debug('There is no contiguous free space on disk ' + \
                         'to fit new size')
            self.newPartition(backup_disk_id,
                              backup_size,
                              False,
                              backup_fs_type,
                              backup_mountpoint)
            raise KusuError, "Couldn't find a contiguous free space to " + \
                             "fit the new size. Try deleting other partitions."

        return edited_partition

    def deletePartition(self, partition_obj, keep_in_place=False):
        """Delete an existing partition."""
        # if partition is a physical volume.
        if self.pv_dict.has_key(partition_obj.path):
            physicalVol = self.pv_dict[partition_obj.path]
            if physicalVol.group != None:
                raise PartitionIsPartOfVolumeGroupError, 'Partition cannot ' + \
                    'be deleted because it is part of a Logical Volume Group.'
            del self.pv_dict[partition_obj.path]

        if self.mountpoint_dict.has_key(partition_obj.mountpoint):
            del self.mountpoint_dict[partition_obj.mountpoint]

        partition_obj.disk.delPartition(partition_obj, keep_in_place)


    def newLogicalVolumeGroup(self, name, extent_size, pv_list):
        """Create a new logical volume group."""
        # sanity checks
        if self.lvg_dict.has_key(name):
            raise DuplicateNameError, 'Logical Volume Group name already exists.'
        unit = extent_size[-1]
        if unit.upper() != 'M':
            raise InvalidVolumeGroupExtentSizeError, 'Invalid Volume Group ' + \
                                                     'Extent Size.'
        _extent_size = int(extent_size[:-1])
        if _extent_size not in range(2, 512+1) and \
           _extent_size % 2:
            raise InvalidVolumeGroupExtentSizeError, 'Invalid Volume Group ' + \
                                                     'Extent Size.'

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
            raise PhysicalVolumeStillInUseError, 'Cannot delete Volume ' + \
                                       'Group. Delete Logical Volumes first.'
        pv_list = lvg.pv_dict.values()
        for pv in pv_list:
            lvg.delPhysicalVolume(pv)

        self.lvg_dict.pop(lvg.name)
        lvg.delete()

    def newLogicalVolume(self, name, lvg, size_MB, fs_type=None, mountpoint=None, fill=False):
        """Create a new logical volume."""
        # sanity checks
        if self.lv_dict.has_key(name):
            raise DuplicateNameError, 'Logical Volume name already exists.'
        if self.mountpoint_dict.has_key(mountpoint):
            raise DuplicateMountpointError, 'Assigned mountpoint already exists.'

        new_lv = lvg.createLogicalVolume(name, long(size_MB), \
                                         fs_type, mountpoint, fill)
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
        if mountpoint:
            self.mountpoint_dict[mountpoint] = lv
        return lv

    def deleteLogicalVolume(self, lv):
        """Delete an existing logical volume."""
        # delete from Volume Group.
        lv.group.delLogicalVolume(lv)
        # delete from mountpoints(if any).
        if self.mountpoint_dict.has_key(lv.mountpoint):
            del self.mountpoint_dict[lv.mountpoint]
        # delete from Logical Volume dictionary.
        if self.lv_dict.has_key(lv.name):
            del self.lv_dict[lv.name]

    def commit(self):
        for disk in self.disk_dict.itervalues():
            disk.commit()
            for part in disk.partition_dict.itervalues():
                checkAndMakeNode(part.path)
        # now the partitions are actually created.
        self.executeLVMFifo()

    def executeLVMFifo(self):
        execFifo()

    def reprLVMFifo(self):
        return reprFifo()

    def printLVMFifo(self):
        print reprFifo()

    def formatAll(self):
        for disk in self.disk_dict.itervalues():
            disk.formatAll()
        for lvg in self.lvg_dict.itervalues():
            lvg.formatAll()
