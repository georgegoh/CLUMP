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
        queueCommand(lvm.activateAllVolumeGroups, None)
        for func,args in cmd_fifo:
            if type(args) is tuple:
                apply(func, args)
            elif args:
                func(args)
            else:
                func()
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
    name = None
    partition = None
    group = None
    on_disk = None
    delete_flag = None

    def remove(path):
        """Static method to remove a physical volume."""
        queueCommand(lvm.removePhysicalVolume, (path))
    remove = staticmethod(remove)
        
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
    name = None
    pv_dict = None
    lv_dict = None
    extent_size_humanreadable = None
    extent_size = 0
    on_disk = None
    deleted = None

    def remove(name):
        """Static method used on a path."""
        queueCommand(lvm.removeVolumeGroup, (name))
    remove = staticmethod(remove)

    def __init__(self, name, extent_size='32M', pv_list=[], createNew=False):
        logger.info('Creating new logical volume group %s' % name)
        if not pv_list:
            raise VolumeGroupMustHaveAtLeastOnePhysicalVolumeError, \
                'Volume group must have at least one physical volume'
        self.name = name
        self.pv_dict = {}
        self.lv_dict = {}
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
        if fill:
            extents = free_extents
        else:
            extents_to_use = 1024.0 * 1024.0 * size_MB / self.extent_size
            import math
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
        if logicalVol.isInUse():
            raise CannotDeleteLogicalVolumeFromLogicalGroupError, \
                  'Logical Volume ' + logicalVol.name + ' is still in use.'
        del self.lv_dict[logicalVol.name]
        queueCommand(lvm.removeLogicalVolume, (logicalVol.path))
        logicalVol.group = None

    def delete(self):
        if self.deleted: raise VolumeGroupHasBeenDeletedError, 'Volume Group has already been deleted'
        logger.info('Deleting volume group %s' % self.name)
        self.delete = True
        queueCommand(lvm.removeVolumeGroup, (self.name))

    def leaveUnchanged(self):
        for pv in self.pv_dict.itervalues():
            if pv.partition.leave_unchanged:
                print "Respecting leave_unchanged flag on %s" % pv.partition.path
                return True

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
    name = None
    group = None
    extents = 0
    fs_type = None
    mountpoint = None
    on_disk = None
    leave_unchanged = None
    do_not_format = None

    def remove(path):
        """Static method used on a path."""
        queueCommand(lvm.removeLogicalVolume, (path))
    remove = staticmethod(remove)

    def __init__(self, name, volumeGroup, extents, fs_type=None, mountpoint=None):
        vg_extentsFree = volumeGroup.extentsTotal() - volumeGroup.extentsUsed()
        if extents > vg_extentsFree:
            raise InsufficientFreeSpaceInVolumeGroupError, \
                'Insufficient free space in volume group'
        self.size_MB = extents * volumeGroup.extent_size
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
        if name in ['name', 'group', 'fs_type', 'mountpoint', 'on_disk', 'leave_unchanged', 'do_not_format', 'size_MB']:
            object.__setattr__(self, name, value)
        elif name == 'extents':
            object.__setattr__(self, name, long(value))
        else:
            raise AttributeError, "%s instance does not have or cannot modify attribute %s" % \
                                  (self.__class__, name)

    def __size(self):
        return (self.extents * self.group.extent_size)

    def resize(self, size_MB, force=False):
        size = size_MB * 1024 * 1024
        if size == self.size:
            return
        elif size < self.size:
            if (self.size - size) < (self.group.extent_size * 1024 * 1024):
                # don't bother reducing if the change is less than an extent.
                return
            else:
                queueCommand(lvm.reduceLogicalVolume, (self.path, str(size_MB) + 'M', self.fs_type))
        else:
            queueCommand(lvm.extendLogicalVolume, (self.path, str(size_MB) + 'M', self.fs_type))
        
    def mount(self, mountpoint=None, readonly=False):
        """Mounts this partition. If no mountpoint is given, then the
           default mountpoint is used.
        """
        if not mountpoint:
            mountpoint = self.mountpoint
        args = ''
        if readonly:
            args = args + '-r'
        p = subprocess.Popen('mount -t %s %s %s %s' % (self.fs_type, self.path, mountpoint, args),
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        logger.debug('Mount stdout: %s, stderr: %s' % (out, err))

    def unmount(self):
        """Unmounts this partition."""
        p = subprocess.Popen('umount %s' % self.path,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()

    def format(self):
        if self.leave_unchanged or self.do_not_format:
            return

        if self.fs_type == 'ext2':
            logger.info('Making ext2 fs on %s' % self.path)
            mkfs = subprocess.Popen('mkfs.ext2 %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
        elif self.fs_type == 'ext3':
            logger.info('Making ext3 fs on %s' % self.path)
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
            logger.info('Making swap fs on %s' % self.path)
            mkfs = subprocess.Popen('mkswap %s' % self.path,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            mkfs_out, status = mkfs.communicate()
