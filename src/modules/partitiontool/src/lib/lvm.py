#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool LVM module.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 
"""This tool keeps track of the following entities in a system:
      c) logical volume groups
      d) logical volumes

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
"""
import subprocess
from kusu.util.errors import *
import lvm202 as lvm
from kusu.util.log import getKusuLog
from os.path import basename, exists

logger = getKusuLog('partitiontool.lvm')

cmd_fifo = None

def queueCommand(func, args=None):
    global cmd_fifo
    if cmd_fifo == None:
        cmd_fifo = []
    cmd_fifo.append((func, args))

def execFifo():
    global cmd_fifo
    if cmd_fifo:
        lvm.activateAllVolumeGroups()
        for func,args in cmd_fifo:
            if type(args) is tuple:
                apply(func, args)
            elif args:
                func(args)
            else:
                func()
        lvm.activateAllVolumeGroups()
    cmd_fifo = None

def reprFifo():
    global cmd_fifo
    if not cmd_fifo: return ''
    s = '\n'
    for func,args in cmd_fifo:
        if type(args) is tuple:
            s = s + func.func_name + str(args) + '\n'
        elif args:
            s = s + func.func_name + "('" + str(args) + "')" + '\n'
        else:
            s = s + func.func_name + '()' + '\n'
    return s

def printFifo():
    global cmd_fifo
    print reprFifo()

def probeLVMEntities(retrieveAllEntitiesPropFunc, probeEntityFunc):
    probe_dict = {}
    entity_prop_list = retrieveAllEntitiesPropFunc()
    if entity_prop_list:
        for entity_prop in entity_prop_list:
            probe_dict[entity_prop] = probeEntityFunc(entity_prop)
    return probe_dict

def probePhysicalVolumes():
    return probeLVMEntities(lvm.retrievePhysicalVolumePaths,
                            lvm.probePhysicalVolume)

def probeLogicalVolumeGroups():
    return probeLVMEntities(lvm.retrieveLogicalVolumeGroupNames,
                            lvm.probeLogicalVolumeGroup)

def probeLogicalVolumes():
    return probeLVMEntities(lvm.retrieveLogicalVolumePaths,
                            lvm.probeLogicalVolume)


class PhysicalVolume(object):
    """A physical volume object that can belong to a logical volume group.
       Hidden attributes available:
          a. size
          b. extents
    """

    def remove(path):
        """Static method to remove a physical volume."""
        queueCommand(lvm.removePhysicalVolume, (path))
    remove = staticmethod(remove)

    def __str__(self):
        groupname = 'Not defined'
        if self.group: groupname = self.group.name
        s = self.partition.path + ' Group: ' + groupname + ' Del: ' + \
            str(self.delete_flag) + ' On Disk: ' + str(self.on_disk)
        return s

    def __init__(self,  partition, createNew=False):
        """A partition may not have knowledge about it's physical volume role,
           but a physical volume must have knowledge about its beginnings
           (the partition).
        """
        from os.path import basename
        self.name = basename(partition.path)
        self.partition = partition
        self.on_disk = False
        self.delete_flag = False
        self.group = None
        if createNew:
            queueCommand(lvm.createPhysicalVolume, (partition.path))

    def isInUse(self):
        return lvm.physicalVolumeInUse(self.partition.path)

    def __getattr__(self, name):
        if name == 'extents':
            return self.__extents()
        elif name == 'size':
            return self.partition.size
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __setattr__(self, name, value):
        if name in ['name', 'partition', 'group', 'on_disk', 'delete_flag']:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError, "%s instance does not have or cannot modify attribute %s" % \
                                  (self.__class__, name)

    def __extents(self):
        if not self.group:
            return 0
        return self.partition.size / self.group.extent_size


class LogicalVolumeGroup(object):
    """A logical volume group consists of physical volumes that are combined
       to form a shared pool of disk space. Subsequently, it can be divided
       into several logical volumes."""

    def remove(name):
        """Static method used on a path."""
        queueCommand(lvm.removeVolumeGroup, (name))
    remove = staticmethod(remove)

    def __str__(self):
        s = self.name + ' Extent Size: ' + self.extent_size_humanreadable + \
            ' Total Extents: ' + str(self.extentsTotal()) + \
            ' Leave Unchanged: ' + str(self.leaveUnchanged()) + \
            ' PVs: ' + str(self.pv_dict.keys()) + ' LVs: ' + \
            str(self.lv_dict.keys())
        return s

    def __init__(self, name, extent_size='32M', pv_list=[], createNew=False):
        logger.info('Creating new logical volume group %s' % name)
        if not pv_list:
            raise VolumeGroupMustHaveAtLeastOnePhysicalVolumeError, \
                'Volume group must have at least one physical volume'
        self.name = name
        self.pv_dict = {}
        self.lv_dict = {}
        self.deleted = False
        self.extent_size_humanreadable = extent_size
        self.extent_size = self.parsesize(extent_size)
        self.on_disk = False
        if exists('/dev/' + name): self.on_disk = True
        self.deleted = False
        for pv in pv_list:
            self.pv_dict[pv.name] = pv
            pv.group = self
        if createNew or not self.on_disk:
            pv_paths = [pv.partition.path for pv in pv_list]
            queueCommand(lvm.createVolumeGroup, (name, extent_size, pv_paths))

    def extentsTotal(self):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        extents = 0
        for pv in self.pv_dict.itervalues():
            extents = extents + pv.extents
        return extents

    def extentsUsed(self):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        extents = 1
        for lv in self.lv_dict.itervalues():
            extents = extents + lv.extents
        return extents

    def parsesize(self, text_size):
        """This method parses text such as '100K', '20M' into integers.
           For example, text_size=20M would return 20 * 1024 * 1024 and 
           text_size=100k would return 100 * 1024.

           Acceptable suffixes: kKmM - all other suffixes will be ignored
                                (i.e., return -1)
        """
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        if text_size[-1] not in "kKmM":
            return -1

        if text_size[-1].upper == 'K':
            multiplier = 1024L
        else:
            multiplier = 1024L*1024L

        size = long(text_size[:-1]) * multiplier
        return size


    def addPhysicalVolume(self, physicalVol):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        """Add a physical volume(i.e., partition) into this group."""
        logger.info('Adding physical volume %s to volume group %s' % (physicalVol.name, self.name))
        if physicalVol.name in self.pv_dict.keys():
            raise PhysicalVolumeAlreadyInLogicalGroupError, \
                'Physical volume already in logical group'
        self.pv_dict[physicalVol.name] = physicalVol
        physicalVol.group = self
        queueCommand(lvm.extendVolumeGroup, (self.name, physicalVol.partition.path))

    def delPhysicalVolume(self, physicalVol):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        if physicalVol.partition.leave_unchanged:
            raise CannotDeleteVolumeGroupError, 'Physical Volume flagged to be unchanged.' 
        logger.info('Deleting physical volume')
        if physicalVol.name not in self.pv_dict.keys():
            raise CannotDeletePhysicalVolumeFromLogicalGroupError, \
                  'Physical Volume ' + physicalVol.name + ' does not exist ' + \
                  'in Logical Group ' + self.name + '.'
        physicalVol.group = None
        del self.pv_dict[physicalVol.name]
        queueCommand(lvm.reduceVolumeGroup, (self.name, physicalVol.partition.path))

    def createLogicalVolume(self, name, size_MB, fs_type, mountpoint, fill=False):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        logger.info('Creating logical volume %s from volume group %s size %d' % (name, self.name, size_MB))
        if name in self.lv_dict.keys():
            raise LogicalVolumeAlreadyInLogicalGroupError, 'Logical volume already exists in Volume Group'

        free_extents = self.extentsTotal() - self.extentsUsed()
        extents_to_use = 1024.0 * 1024.0 * size_MB / self.extent_size
        import math
        if fill:
            if extents_to_use > free_extents:
                raise OutOfSpaceError, 'Cannot fulfill minimum size requirements for LV %s.' % name
            extents = free_extents
        else:
            if extents_to_use == free_extents:
                extents = free_extents
            elif free_extents > extents_to_use:
                extents = int(math.ceil(extents_to_use))
            else:
                extents = int(math.floor(extents_to_use))

        lv = LogicalVolume(name, self, extents, fs_type, mountpoint)
        self.lv_dict[name] = lv

        queueCommand(lvm.createLogicalVolume, (self.name, name, extents))
        queueCommand(lvm.makeNodes, None)
        return lv

    def logFreeExtents(self):
        free = lvm.retrieveLVMEntityData('lvm vgdisplay %s' % self.name, 'Free  PE / Size')
        logger.debug('LVM Free Extents: %s' % free)

    def delLogicalVolume(self, logicalVol):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        logger.info('Deleting logical volume %s from volume group %s' % (logicalVol.name, self.name))
        if logicalVol.name not in self.lv_dict.keys():
            raise CannotDeleteLogicalVolumeFromLogicalGroupError, \
                  'Logical Volume ' + logicalVol.name + ' does not exist ' + \
                  'in Logical Group ' + self.name + '.'
        if logicalVol.isInUse() or logicalVol.leave_unchanged:
            raise CannotDeleteLogicalVolumeFromLogicalGroupError, \
                  'Logical Volume ' + logicalVol.name + ' is still in use.'
        del self.lv_dict[logicalVol.name]
        queueCommand(lvm.removeLogicalVolume, (logicalVol.path))
        logicalVol.group = None

    def delete(self):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted.'
        if self.leaveUnchanged(): raise CannotDeleteVolumeGroupError, 'Volume Group flagged to be unchanged.' 
        logger.info('Deleting volume group %s' % self.name)
        self.delete = True
        for pv in self.pv_dict.values():
            pv.group = None
        queueCommand(lvm.removeVolumeGroup, (self.name))

    def leaveUnchanged(self):
        for pv in self.pv_dict.itervalues():
            if pv.partition.leave_unchanged:
                logger.debug("Respecting leave_unchanged flag on %s" % pv.partition.path)
                return True
        return False

    def formatAll(self):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        for lv in self.lv_dict.itervalues():
            lv.format()


class LogicalVolume(object):
    """A logical volume assigned from a logical volume group.
       Hidden attributes available:
          a. size
          b. extents
          c. path
    """

    def remove(path):
        """Static method used on a path."""
        queueCommand(lvm.removeLogicalVolume, (path))
    remove = staticmethod(remove)

    def __str__(self):
        s = self.name + ' VolGrp: ' + self.group.name + ' Extents: ' + \
            str(self.extents) + '\nFS: ' + str(self.fs_type) + ' On Disk: ' + str(self.on_disk) + \
            ' MntPnt: ' + str(self.mountpoint) + ' Leave Unchanged: ' + str(self.leave_unchanged)
        return s

    def __init__(self, name, volumeGroup, extents, fs_type=None, mountpoint=None):
        vg_extentsFree = volumeGroup.extentsTotal() - volumeGroup.extentsUsed()
        if extents > vg_extentsFree:
            raise InsufficientFreeSpaceInVolumeGroupError, \
                'Insufficient free space in volume group'
        self.name = name
        self.group = volumeGroup
        self.extents = extents
        self.fs_type = fs_type
        self.mountpoint = mountpoint
        self.on_disk = False
        self.leave_unchanged = False
        self.do_not_format = False

    def isInUse(self):
        return False

    def __getattr__(self, name):
        if name == 'size':
            return self.__size()
        elif name == 'path':
            return '/dev/' + self.group.name + '/' + self.name
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __setattr__(self, name, value):
        if name in ['name', 'group', 'fs_type', 'mountpoint', 'mountedpoint', 'on_disk', 'leave_unchanged', 'do_not_format']:
            object.__setattr__(self, name, value)
        elif name == 'extents':
            object.__setattr__(self, name, long(value))
        else:
            raise AttributeError, "%s instance does not have or cannot modify attribute %s" % \
                                  (self.__class__, name)

    def __size(self):
        return (self.extents * self.group.extent_size)

    def resize(self, size_MB, force=False):
        extents = int(size_MB) * 1024 * 1024 / self.group.extent_size
        if extents == self.extents:
            return
        if extents < self.extents:
            queueCommand(lvm.reduceLogicalVolume, \
                         (self.path, extents, self.group.extent_size, self.fs_type))
        else:
            queueCommand(lvm.extendLogicalVolume, \
                         (self.path, extents, self.group.extent_size, self.fs_type))
        self.extents = extents
        logger.debug('LV %s resized to %d extents' % (self.name, self.extents))
        logger.debug('LV %s new size=%d' % (self.name, self.size/1024/1024))
       
    def mount(self, mountpoint=None, readonly=False):
        """Mounts this partition. If no mountpoint is given, then the
           default mountpoint is used.
        """
        if not mountpoint:
            mountpoint = self.mountpoint
        args = ''
        if readonly:
            args = args + '-r'
        fs_arg = ''
        if self.fs_type: fs_arg = '-t %s' % self.fs_type
        p = subprocess.Popen('mount %s %s %s %s' % (fs_arg, self.path, mountpoint, args),
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
        if self.leave_unchanged or self.do_not_format:
            logger.info('Not formatting %s due to flag' % self.path)
            return

        if self.fs_type == 'ext2':
            logger.info('Making ext2 fs on %s' % self.path)
            mkfs = subprocess.Popen('mke2fs %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
            logger.info('mke2fs done')
        elif self.fs_type == 'ext3':
            logger.info('Making ext3 fs on %s' % self.path)
            mkfs = subprocess.Popen('mke2fs -j %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()

            logger.info('FORMAT (mke2fs -j) done, doing tune2fs')
            tune2fs = subprocess.Popen('tune2fs -c0 -i0 -O dir_index -ouser_xattr,acl %s' % self.path,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            tune2fs_out, status = tune2fs.communicate()
            logger.info('tune2fs done.')
        elif self.fs_type == 'linux-swap':
            logger.info('Making swap fs on %s' % self.path)
            mkfs = subprocess.Popen('mkswap %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
            logger.info('mkswap done.')
