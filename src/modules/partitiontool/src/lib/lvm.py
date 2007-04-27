#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Tool LVM module.
#
# Copyright 2007 Platform Computing Corporation.
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
__version__ = "$Revision$"
import commands
from kusuexceptions import *
import lvm202 as lvm
#from kusu.util.log import Logger

def probeLVMEntities(retrieveAllEntitiesPropFunc, probeEntityFunc):
    probe_dict = {}
    entity_prop_list = retrieveAllEntitiesPropFunc()
    for entity_prop in entity_prop_list:
        probe_dict[entity_prop] = probeEntityFunc(entity_prop)
    return probe_dict

def probePhysicalVolumes():
    return probeLVMEntities(lvm.retrievePhysicalVolumePaths,
                            lvm.probePhysicalVolume)

def probeLogicalVolumeGroups():
    return probeLVMEntities(lvm.retrieveLogicalVolumeGroupNames,
                            lvm.probeLogicalVolumeGroup)


class PhysicalVolume(object):
    """A physical volume object that can belong to a logical volume group.
       Hidden attributes available:
          a. size
          b. extents
    """
    name = None
    partition = None
    group = None

    def __init__(self,  partition):
        """A partition may not have knowledge about it's physical volume role,
           but a physical volume must have knowledge about its beginnings
           (the partition).
        """
        from os.path import basename
        self.name = basename(partition.path)
        self.partition = partition

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
        if name in ['name', 'partition', 'group']:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError, "%s instance does not have or cannot modify attribute %s" % \
                                  (self.__class__, name)

    def __extents(self):
        if not group:
            return 0
        return self.size / self.group.extent_size

    def commit(self):
        if not self.partition.leave_unchanged:
            lvm.createPhysicalVolume(self.partition.path)
        else:
            print "Respecting partition's leave_unchanged flag"


class LogicalVolumeGroup(object):
    """A logical volume group consists of physical volumes that are combined
       to form a shared pool of disk space. Subsequently, it can be divided
       into several logical volumes."""
    name = None
    pv_dict = None
    lv_dict = None
    extent_size_humanreadable = None
    extent_size = 0

    def __init__(self, name, extent_size='32M', pv_list=[]):
        #logger.info('Creating new logical volume group %s' % name)
        self.name = name
        self.pv_dict = {}
        self.lv_dict = {}
        self.extent_size_humanreadable = extent_size
        self.extent_size = self.parsesize(extent_size)
        for pv in pv_list:
            self.pv_dict[pv.name] = pv
            pv.group = self

    def extentsTotal(self):
        extents = 0
        for pv in self.pv_dict.itervalues():
            extents = extents + pv.extents()

    def extentsUsed(self):
        extents = 0
        for lv in self.lv_dict.itervalues():
            extents = extents + lv.extents()

    def parsesize(self, text_size):
        """This method parses text such as '100K', '20M' into integers(base k).
           For example, text_size=20M would return 20 * 1024 = 2048 and 
           text_size=100k would return 100 * 1 = 100.

           Acceptable suffixes: kKmM - all other suffixes will be ignored
                                (i.e., return -1)
        """
        if text_size[-1] not in "kKmM":
            return -1

        if text_size[-1].upper == 'K':
            multiplier = 1024L
        else:
            multiplier = 1024L*1024L

        size = long(text_size[:-1]) * multiplier
        return size


    def addPhysicalVolume(self, physicalVol):
        """Add a physical volume(i.e., partition) into this group."""
        logger.info('Adding physical volume %s to volume group %s' % (physicalVol.name, self.name))
        if physicalVol.name in self.pv_dict.keys():
            raise PhysicalVolumeAlreadyInLogicalGroupError
        self.pv_dict[physicalVol.name] = physicalVol
        physicalVol.group = self.name
#        lvm.extendVolumeGroup(self.name, physicalVol.partition.path)

    def delPhysicalVolume(self, physicalVol):
        logger.info('Deleting physical volume')
        if physicalVol.name not in self.pv_dict.keys():
            raise CannotDeletePhysicalVolumeFromLogicalGroupError, \
                  'Physical Volume ' + physicalVol.name + ' does not exist ' + \
                  'in Logical Group ' + self.name + '.'
        physicalVol.group = None
        del self.pv_dict[physicalVol.name]
#        lvm.reduceVolumeGroup(self.name, physicalVol.partition.path)

    def createLogicalVolume(self, name, size):
        logger.info('Creating logical volume %s from volume group %s' % (name, self.name))
        if name in self.lv_dict.keys():
            raise LogicalVolumeAlreadyInLogicalGroupError
        lv = LogicalVolume(name, self, size)
        self.lv_dict[name] = lv
#        lvm.createLogicalVolume(self.name, name, size)
        return lv

    def delLogicalVolume(self, logicalVol):
        logger.info('Deleting logical volume %s from volume group %s' % (name, self.name))
        if logicalVol.name not in self.lv_dict.keys():
            raise CannotDeleteLogicalVolumeFromLogicalGroupError, \
                  'Logical Volume ' + logicalVol.name + ' does not exist ' + \
                  'in Logical Group ' + self.name + '.'
        if logicalVol.isInUse():
            raise CannotDeleteLogicalVolumeFromLogicalGroupError, \
                  'Logical Volume ' + logicalVol.name + ' is still in use.'
        logicalVol.group = None
        del self.lv_dict[logicalVol.name]
#        lvm.removeLogicalVolume(logicalVol.path)

    def leaveUnchanged(self):
        for pv in self.pv_dict.itervalues():
            if pv.partition.leave_unchanged:
                return True

    def commit(self):
        if self.leaveUnchanged():
            print "Respecting leave_unchanged flag on %s" % pv.partition.path
            return
        pv_paths = [ pv.partition.path for pv in self.pv_dict.itervalues() ]
        lvm.createVolumeGroup(self.name,
                              self.extent_size,
                              pv_paths)


class LogicalVolume(object):
    """A logical volume assigned from a logical volume group.
       Hidden attributes available:
          a. size
          b. extents
    """
    name = None
    group = None
    extents = 0
    fs_type = None
    mountpoint = None

    def __init__(self, name, volumeGroup, size, fs_type=None, mountpoint=None):
        vg_extentsFree = volumeGroup.extentsTotal() - volumeGroup.extentsUsed()
        newExtentsToAllocate = size / volumeGroup.extent_size
        if newExtentsToAllocate > vg_extentsFree:
            raise InsufficientFreeSpaceInVolumeGroupError
        self.name = name
        self.group = volumeGroup
        self.extents = newExtentsToAllocate
        self.fs_type = fs_type
        self.mountpoint = mountpoint

    def __getattr__(self, name):
        if name == 'size':
            return self.__size
        elif name == 'path':
            return '/dev/' + group.name + '/' + name
        else:
            raise AttributeError, "%s instance has no attribute '%s'" % \
                                  (self.__class__, name)

    def __setattr__(self, name, value):
        if name in ['name', 'group', 'fs_type', 'mountpoint']:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError, "%s instance does not have or cannot modify attribute %s" % \
                                  (self.__class__, name)

    def __size(self):
        return (self.extents * self.group.extent_size)

    def commit(self):
        if self.group.leaveUnchanged():
            print "Respecting Group's leaveUnchanged request"
            return
        lvm.createLogicalVolume(self.group.name, self.name, size)
