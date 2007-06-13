#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import kusu.util.log as kusulog
from kusu.util.errors import *

from path import path

logger = kusulog.getKusuLog('installer.defaults')

def vanillaSchema():
    """This is a plain vanilla schema that contains 4 physical partitions:
          a. /boot - ext3, 100:
          b. swap - 1000M
          c. / - 2000M
          d. /depot - 4000M (fill)
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
    disk1_partition_dict[3] = { 'size_MB': 2000,
                                'fs': 'ext3',
                                'mountpoint': '/',
                                'fill': False}
    disk1_partition_dict[4] = { 'size_MB': 4000,
                                'fs': 'ext3',
                                'mountpoint': '/depot',
                                'fill': True}

    schema = {'disk_dict' : disk_dict,
              'vg_dict' : None}

    return schema


def vanillaSchemaLVM():
    """This is a plain vanilla schema that contains 3 physical partitions:
          a. /boot - ext3, 100:
          b. swap - 1000M
          c. LVM physical volume - 6000M (fill)
       The LVM pv makes up a logical volume group'VolGroup00', which contains
       2 logical volumes:
          a. ROOT - ext3, 2000M, mounted on /
          b. DEPOT - ext3, 4000M, mounted on /depot (fill)
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
                                'fs': 'physical volume',
                                'mountpoint': None,
                                'fill': True}

    # define the lvm schema
    vg_dict = { 'VolGroup00': { 'pv_dict': {},
                                'lv_dict': {},
                                'extent_size': '32M'
                              }
              }

    volgroup00 = vg_dict['VolGroup00']
    volgroup00['pv_dict'][1] = { 'disk': 1, 'partition': 3 }
    volgroup00['lv_dict']['ROOT'] = { 'size_MB': 2000,
                                      'fs': 'ext3',
                                      'mountpoint': '/',
                                      'fill': False}
    volgroup00['lv_dict']['DEPOT'] = { 'size_MB': 4000,
                                       'fs': 'ext3',
                                       'mountpoint': '/depot',
                                       'fill': True}

    schema = {'disk_dict' : disk_dict,
              'vg_dict' : vg_dict}

    return schema


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
              'vg_dict' : {} }

    return schema


def setupDiskProfile(disk_profile, schema=None):
    """Set up a disk profile based on a given schema."""
    # check that no partitions have been created.
    for disk in disk_profile.disk_dict.itervalues():
        if disk.partition_dict:
            raise DiskProfileNotEmptyError, 'Disk Profile is not empty.'
    # check for consistency in LVM dicts.
    if disk_profile.pv_dict or disk_profile.lvg_dict or disk_profile.lv_dict:
        raise DiskProfileNotEmptyError, 'LVM entities still exist.'

    if not schema:
        return True
    else: # do the schema stuff.
        if not schema.has_key('disk_dict') or not schema.has_key('vg_dict'):
            raise PartitionSchemaError, 'Schema has no disk and/or LVM description.'

        createPhysicalSchema(disk_profile, schema['disk_dict'])
        if schema['vg_dict']: createLVMSchema(disk_profile, schema['vg_dict'])
    logger.debug('Disk Profile set up')


def createPhysicalSchema(disk_profile, disk_schemata):
        # check if we have enough disks to fulfill the schema
        if len(disk_profile.disk_dict) < len(disk_schemata):
            raise PartitionSchemaError, 'Schema defines more disks than ' + \
                                        'is physically available on this system.'

        # do the physical disk and partitions first.
        sorted_disk_keys = sorted(disk_profile.disk_dict.keys())
        for i in range(len(disk_schemata)):
            # for each disk in the schema.
            schema_disk = disk_schemata[i+1]
            schema_partition_dict = schema_disk['partition_dict']
            try:
                for j in range(len(schema_partition_dict)):
                    # for each partition in the current disk.
                    schema_partition = schema_partition_dict[j+1]
                    disk_key = sorted_disk_keys[i]
                    size_MB = schema_partition['size_MB']
                    logger.debug('Creating new partition of size: %d' % size_MB)
                    fs = schema_partition['fs']
                    mountpoint = schema_partition['mountpoint']
                    fill = schema_partition['fill']
                    disk_profile.newPartition(disk_key,
                                              size_MB,
                                              False,
                                              fs,
                                              mountpoint,
                                              fill)
            except IndexError:
                raise PartitionSchemaError, 'Run out of disks.'


def createLVMSchema(disk_profile, lvm_schemata):
    for vg_key, vg_schema in lvm_schemata.iteritems():
        sorted_disk_keys = sorted(disk_profile.disk_dict.keys())
        # create the Volume Group first.
        pv_schemata = vg_schema['pv_dict']
        pv_list = []
        for pv_schema in pv_schemata.itervalues():
            disk_id = pv_schema['disk']
            part_id = pv_schema['partition']
            disk_key = sorted_disk_keys[disk_id-1]
            disk = disk_profile.disk_dict[disk_key]
            partition = disk.partition_dict[part_id]
            pv = disk_profile.pv_dict[partition.path]
            pv_list.append(pv)

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
            disk_profile.newLogicalVolume(lv_name,
                                          vg,
                                          lv_schema['size_MB'],
                                          lv_schema['fs'],
                                          lv_schema['mountpoint'],
                                          lv_schema['fill'])
            logger.debug('Finished creating %s' % lv_name)
        if last_lv:
            disk_profile.newLogicalVolume(last_lv[0],
                                          vg,
                                          last_lv[1]['size_MB'],
                                          last_lv[1]['fs'],
                                          last_lv[1]['mountpoint'],
                                          last_lv[1]['fill'])
    logger.debug('Create LVM Schema finished')
