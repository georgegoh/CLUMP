#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
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
import re
import math
import parted
import StringIO
from lvm import *
from filesystems import *
from helper import *
from path import path
from struct import pack,unpack
import probe
from os.path import basename, exists
import primitive.support.compat
from errors import *
from tempfile import mkdtemp
from primitive.support.util import runCommand
from primitive.support.type import Struct
from nodes import checkAndMakeNode
import primitive.support.log as primitivelog
logger = primitivelog.getPrimitiveLog(name='disk')

from disk import *

try:
    import subprocess
except:
    from popen5 import subprocess


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
                    'reiserfs' : fsTypes['reiserfs'],
                    'ntfs'  : fsTypes['ntfs']
                  }
    mountable_fsType = { 'ext2' : True,
                         'ext3' : True,
                         'reiserfs' : True,
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
        s = s + 'Ignore disks: ' + str(self.ignore_disk_dict.keys())
        s = s + '\nPhysical Volume Dictionary:\n' + self.__lvmStr(self.pv_dict)
        s = s + '\nLogical Volume Group Dictionary:\n' + self.__lvmStr(self.lvg_dict)
        s = s + '\nLogical Volume Dictionary:\n' + self.__lvmStr(self.lv_dict)
        s = s + '\nMountpoints:\n' + self.__mntStr()
        return s

    def __init__(self, fresh, test=None, probe_fstab=True, ignore_errors=True, bootstrap=False):
        """Initialises a DiskProfile object by doing the following:
           
        """
        global cmd_fifo
        self.disk_dict = {}
        self.ignore_disk_dict = {}
        self.mountpoint_dict = {}
        self.pv_dict = {}
        self.lvg_dict = {}
        self.lv_dict = {}
        self.manual_writes = [] # hack for writing partition types to disk

        import lvm202
        out, err = lvm202.activateAllVolumeGroups()
        real_errors = []
        for l in err.split('\n'):
            l = l.strip()
            if not l.startswith('File descriptor ') \
               and not l.startswith('No volume groups found') \
               and not l.startswith('device-mapper: reload ioctl failed: Invalid argument') \
               and l:
                real_errors.append(l)
        if real_errors and not ignore_errors:
            raise LVMInconsistencyError, '\n'.join(real_errors)
        
        if test:
            self.populateDiskProfileTest(fresh, test)
        else:
            try:
                self.populateDiskProfile(fresh, probe_fstab, bootstrap=bootstrap)
            except Exception, e:
                logger.debug("Encountered an unrecoverable error while " + \
                             "scanning the disks/LVM. Clearing the disk " + \
                             "profile and starting without probing fstab.")
                import traceback
                if hasattr(traceback, "format_exc"): # new in python 2.4
                    tb = traceback.format_exc()
                else:
                    fp = StringIO.StringIO()
                    traceback.print_exc(file=fp)
                    tb = fp.getvalue()

                logger.debug("Traceback: %s" % tb)
                self.populateDiskProfile(fresh, probe_fstab=False, bootstrap=False)
        logger.debug('State after scan:\n%s' % self.__str__())


    def probeLVMEntities(self):
        logger.debug('Probing PVs.')
        # sometimes LVM metadata doesn't correspond with actual partitions.
        _pv_probe_dict = probePhysicalVolumes()
        pv_probe_dict = {}
        for k in _pv_probe_dict.keys():
            if not self.disk_dict.has_key(basename(k)):
                pv_probe_dict[k] = _pv_probe_dict[k]
        logger.debug('PVs found: %s' % str(pv_probe_dict))
        logger.debug('Probing VGs.')
        lvg_probe_dict = probeLogicalVolumeGroups()
        logger.debug('VGs found: %s' % str(lvg_probe_dict))
        logger.debug('Probing LVs.')
        lv_probe_dict = probeLogicalVolumes()
        logger.debug('LVs found: %s' % str(lv_probe_dict))
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


    def populateDiskProfile(self, fresh, probe_fstab, bootstrap=False):
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
                self.populateMountPoints(bootstrap=bootstrap)


    def __findDisksAndCreateDictionary(self, fresh):
        logger.debug('Finding disks.')
        disk_dict = {}
        disks_str = probe.getDisks().keys()
        for disk_str in disks_str:
            logger.debug('Disk: %s' % disk_str)
            disk_dict[disk_str] = Disk('/dev/'+disk_str, self, fresh)
        logger.debug('Found disks.')
        return disk_dict


    def populateMountPoints(self, fstab_path='etc/fstab', bootstrap=False):
        """Look through the partitions and LV's to determine mountpoints."""
        logger.debug('Populate mount points.')
        if bootstrap:
            dev_map = self.extractFstabToDevices(None, '/etc/fstab', bootstrap=bootstrap)
            for dev_path, dev in dev_map.iteritems():
                logger.debug("populating %s's mountpoint" % dev)
                vol = self.findDevice(dev_path)
                if vol:
                    self.mountpoint_dict[dev.mntpnt] = vol
                    vol.mountpoint = dev.mntpnt
                    vol.fs_type = dev.fs_type
                logger.debug('Done')
            # Ok, we've parsed the first fstab we found, job done.
            return

        # Check the partitions and logical volumes
        m_parts = self.getMountablePartitions()
        m_lvs = self.getMountableLVs()
        m_list = m_parts + m_lvs
        for p in m_list:
            found, loc = self.lookForFstab(p, fstab_path)
            if found:
                dev_map = self.extractFstabToDevices(p, loc, bootstrap=bootstrap)
                for dev_path, dev in dev_map.iteritems():
                    logger.debug("populating %s's mountpoint" % dev)
                    vol = self.findDevice(dev_path)
                    if vol:
                        self.mountpoint_dict[dev.mntpnt] = vol
                        vol.mountpoint = dev.mntpnt
                        vol.fs_type = dev.fs_type
                    logger.debug('Done')
                # Ok, we've parsed the first fstab we found, job done.
                return

    def extractFstabToDevices(self, device, loc, bootstrap=False):
        """For linux-type systems."""
        if bootstrap:
            fstab = open(loc)
            f_lines = [l for l in fstab.readlines() if \
                       len(l.strip()) and l.strip()[0] != '#']
            fstab.close()

        else:
            # get the temp directory to mount the device.
            mntpnt = path(mkdtemp('partitiontool-extractfstab'))

            try:
                # mount the device.
                logger.debug('Mounting %s on %s to extract fstab.' % (device.path, mntpnt))
                device.mount(mountpoint=mntpnt, readonly=True)
                fstab_loc = str(path(mntpnt) / path(loc))
                # open fstab file and filter out comments.
                logger.debug('%s mounted, opening fstab.' % device.path)
                fstab = open(fstab_loc)
                f_lines = [l for l in fstab.readlines() if \
                           len(l.strip()) and l.strip()[0] != '#']
                fstab.close()
                logger.debug('fstab read, unmounting %s.' % mntpnt)
                device.unmount()
                mntpnt.rmtree()
                logger.debug('%s unmounted.' % device.path)
            except MountFailedError:
                return {}

        device_map = {}
        logger.debug('Parsing fstab')
        for l in f_lines:
            try:
                # look for a mountable entry and append it to our dict.
                dev, mntpnt, fs_type = l.split()[:3]
                if fs_type in self.mountable_fsType.keys():
                    dev_struct = Struct(fs_type=fs_type, mntpnt=mntpnt)
                    device_map[dev] = dev_struct
            except ValueError, e:
                raise PartitionException, str(e) + ' Offending line: \n' + l
        logger.debug('Parsed fstab')
        return device_map

    def findDevice(self, dev):
        """Find a device."""
        logger.debug('find device %s', dev)
        if dev.startswith('UUID='):
            uuid = dev.strip('UUID=')
            for d in self.disk_dict.itervalues():
                for p in d.partition_dict.itervalues():
                    try:
                        fs = Ext2Viewer(p.path)
                        if fs.uuid == uuid:
                            return p
                    except Exception:
                        pass
            return None

        if dev.startswith('LABEL='):
            lbl = dev.strip('LABEL=')
            for d in self.disk_dict.itervalues():
                for p in d.partition_dict.itervalues():
                    try:
                        fs = Ext2Viewer(p.path)
                        if fs.label == lbl:
                            return p
                    except Exception:
                        pass
            return None

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

    def getMBRSignatureByBIOSOrder(self):
        if not exists('/sys/firmware/edd'):
            logger.debug('EDD module not found. BIOS disk order cannot be determined.')
            return []

        logger.debug('Starting EDD detection of BIOS disk order:')
        # EDD keeps list of MBR signatures by BIOS order
        bios_mbrsig_list = []
        # anaconda looks at first sixteen only, so we follow
        for disk_no in xrange(80,95):
            edd_path = '/sys/firmware/edd/int13_dev%d/mbr_signature' % disk_no
            if exists(edd_path):
                mbrsig = int(open(edd_path).read().strip(), 16)
                logger.debug('Disk %d MBR signature: %d' % (disk_no, mbrsig))
                bios_mbrsig_list.append(pack('I', mbrsig))
        return bios_mbrsig_list


    def getBIOSDiskOrder(self, bios_mbrsig_list=None):
        """
        Return the list of disks in the system ordered according to how the
        BIOS sees them. This method depends on the Enhanced Disk Drive (EDD)
        Services support available in RedHat and SuSE distros.
        Returns an empty list if EDD is not available.

        MBR signatures are assumed to be unique across all disks in a system.

        See http://linux.dell.com/installermagic.shtml
        """
        if not bios_mbrsig_list:
            bios_mbrsig_list = self.getMBRSignatureByBIOSOrder()

        disk_dict_cp = dict(self.disk_dict)
        disks = self.disk_dict.keys()
        bios_driveorder = []
        for mbrsig in bios_mbrsig_list:
            found = None
            for k,v in disk_dict_cp.iteritems():
                if v.mbr_signature == mbrsig:
                    found = k
                    break
            if found:
                disk_dict_cp.pop(found)
                bios_driveorder.append(found)
        return bios_driveorder


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
        for lv in self.lv_dict.itervalues():
            try:
                f = open(lv.path, 'r')
                sb = f.read(1082)
                magic_str = sb[-2:]
                magic = unpack('H', magic_str)
                if hex(magic[0]) == hex(0xef53):
                    mountable_lvs.append(lv)
            finally:
                f.close()
        return mountable_lvs

    def lookForFstab(self, partition, fstab_path='etc/fstab'):
        """If found, returns a tuple (True, <location>),
           Else, returns (False, None)
        """
        logger.debug('Looking for fstab in %s' % partition.path)
        mntpnt = path(mkdtemp('partitiontool-fstabsearch'))
        try:
            partition.mount(mountpoint=mntpnt, readonly=True)
            logger.debug('Mounted %s on %s' % (partition.path, mntpnt))
            loc = mntpnt / path(fstab_path)
            loc_exists = loc.exists()
            partition.unmount()
        finally:
            mntpnt.rmtree()
        if loc_exists:
            logger.debug('fstab found')
            return True, fstab_path
        logger.debug('fstab not found')
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
            if isDisk(pv_path):
                msg = 'Physical Volume %s is not a partition.' % pv_path
                raise PhysicalVolumeIsNotPartitionError, msg
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
        p = path_str.strip()
        while p[i].isdigit():
            i = i-1

        j = i+1
        cciss_pat = re.compile('c(\d)d(\d+)p(\d+)')
        m = cciss_pat.match(path(path_str).basename())
        if m :
            disk_path = path('cciss') / basename(p[:i])
        else:
            i = i+1
            disk_path = basename(p[:i])

        disk = self.disk_dict[disk_path]
        partition_number = int(p[j:])
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
            raise PartitionException, 'Cannot delete the selected device because ' + \
                             'it is a physical disk in the system.'
        else:
            raise PartitionException, 'An internal error has occurred in the ' + \
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
        """
             Edit an existing partition. The mountpoint dictionary needs to
             be updated as well.
        """
        try:
            logger.debug('Edit partition %s' % partition_obj.path)
            if partition_obj.path in self.pv_dict.keys():
                pv = self.pv_dict[partition_obj.path]
                if pv.group and pv.group.lv_dict:
                    raise PartitionIsPartOfVolumeGroupError

            if mountpoint in self.mountpoint_dict and \
               partition_obj is not self.mountpoint_dict[mountpoint]:
                raise MountpointAlreadyUsedError, 'The selected mountpoint ' \
                    '%s is already in use.' % mountpoint 

            fill = not fixed_size
            partition_obj.resize(size_MB, fill)

            if partition_obj.mountpoint in self.mountpoint_dict:
                del(self.mountpoint_dict[partition_obj.mountpoint])

            partition_obj.mountpoint = mountpoint
            if mountpoint:
                self.mountpoint_dict[mountpoint] = partition_obj

            if fs_type in ['ext2', 'ext3', 'reiserfs', 'linux-swap']:
                partition_obj.fs_type = fs_type
 

        except PartitionIsPartOfVolumeGroupError:
            pv = self.pv_dict[partition_obj.path]
            if pv.group:
                group = pv.group.name
            else:
                group = 'Unknown'
            raise PartitionIsPartOfVolumeGroupError, 'Partition %s cannot ' % \
                (partition_obj.path) + \
                'be edited because it is part of Logical Volume Group %s, ' % \
                (group) + \
                'which still contains allocated logical volumes.\nDelete those first.'
 
        except PartitionSizeTooLargeError, e:
            logger.debug('Exception raised when trying to edit partition %s' % \
                         partition_obj.path)
            logger.debug('There is no contiguous free space on disk ' + \
                         'to fit new size')
            raise PartitionSizeTooLargeError, "Couldn't find a contiguous free space to " + \
                             "fit the new size. Try deleting other partitions."

        return partition_obj

    def deletePartition(self, partition_obj, keep_in_place=False):
        """Delete an existing partition."""
        # if partition is a physical volume.
        if self.pv_dict.has_key(partition_obj.path):
            physicalVol = self.pv_dict[partition_obj.path]
            if physicalVol.group != None:
                raise PartitionIsPartOfVolumeGroupError, 'Partition %s cannot ' % \
                    (partition_obj.path) + \
                    'be deleted because it is part of Logical Volume Group %s.' % \
                    (physicalVol.group.name)
            del self.pv_dict[partition_obj.path]

        if self.mountpoint_dict.has_key(partition_obj.mountpoint):
            del self.mountpoint_dict[partition_obj.mountpoint]

        partition_is_logical = (partition_obj.type == 'logical')
        disk = partition_obj.disk
        p_path = partition_obj.path
        disk.delPartition(partition_obj, keep_in_place)
        logger.debug('Deleted partition %s' % p_path)

        if partition_is_logical:
            if not disk.hasLogicalPartitions():
                self.__deleteExtendedPartition(disk)


    def __deleteExtendedPartition(self, disk):
        for p in disk.partition_dict.values():
            if p.type == 'extended':
                logger.debug('delete extended partition')
                self.deletePartition(p)


    def newLogicalVolumeGroup(self, name, extent_size, pv_list):
        """Create a new logical volume group."""
        # sanity checks
        if self.lvg_dict.has_key(name):
            raise DuplicateNameError, 'Logical Volume Group name already exists.'
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
                deleted_pvs.append(existing_pv)
        for pv in deleted_pvs:
            lvg_obj.delPhysicalVolume(pv)
        # insertion pass
        for pv in pv_obj_list:
            if pv.name not in lvg_obj.pv_dict.keys():
                inserted_pvs.append(pv)
        for pv in inserted_pvs:
            lvg_obj.addPhysicalVolume(pv)

        return lvg_obj


    def deleteLogicalVolumeGroup(self, lvg):
        """Delete an existing logical volume group."""
        # sanity checks
        if lvg.lv_dict:
            raise LogicalVolumeGroupStillInUseError, 'Cannot delete Volume ' + \
                                        'Group. Delete Logical Volumes first.'
        pv_list = lvg.pv_dict.values()
        for pv in pv_list:
            lvg.delPhysicalVolume(pv)

        lvg.delete()
        self.lvg_dict.pop(lvg.name)

    def newLogicalVolume(self, name, lvg, size_MB, fs_type=None, mountpoint=None, fill=False):
        """Create a new logical volume."""
        # sanity checks
        if self.lv_dict.has_key(name):
            raise DuplicateNameError, 'Logical Volume name %s already exists.' % name
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
        if mountpoint in self.mountpoint_dict and \
           lv is not self.mountpoint_dict[mountpoint]:
            raise MountpointAlreadyUsedError, 'The selected mountpoint ' \
                '%s is already in use.' % mountpoint 

        size = size_MB * 1024 * 1024
        if size != lv.size:
            lv.resize(size_MB)
        if lv.fs_type == fs_type:
            lv.do_not_format = True
        lv.fs_type = fs_type
        if lv.mountpoint != mountpoint:
            if lv.mountpoint in self.mountpoint_dict:
                del(self.mountpoint_dict[lv.mountpoint])
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

    def commit(self, ignore_errors=False):
        p = subprocess.Popen('lvm vgchange -an',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        logger.debug('Deactivate VGs: %s, %s' % (out, err))
        for disk in self.disk_dict.itervalues():
            disk.commit()
            for part in disk.partition_dict.itervalues():
                checkAndMakeNode(part.path)
            # sync after each disk is committed.
            p = subprocess.Popen('sync', shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
        # after all disks are committed, sleep for 2 seconds to allow
        # for udev to settle before proceeding with LVM operations.
        from time import sleep
        sleep(2)

        # now the partitions are actually created.
        self.executeLVMFifo(ignore_errors)
        self.__modifyPartitionTypeHack()
        p = subprocess.Popen('lvm vgchange -ay',
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        logger.debug('Activate VGs: %s, %s' % (out, err))
 
    def __modifyPartitionTypeHack(self):
        # XXX
        # hack for modifying partition types.
        for (path, index, type) in self.manual_writes:
            out_p = file(path, 'w')
            try:
                logger.debug('Writing preserve info to %s: %d %s' % (path, index, type))
                out_p.seek(index)
                out_p.write(type)
            except Exception, e:
                logger.debug('Exception thrown: %s' % str(e))
                pass
            out_p.close()

    def executeLVMFifo(self, ignore_errors=False):
        execFifo(ignore_errors)

    def reprLVMFifo(self):
        return reprFifo()

    def printLVMFifo(self):
        print reprFifo()

    def formatAll(self):
        logger.debug('Format all disks in the profile.')
        for disk in self.disk_dict.itervalues():
            disk.formatAll()
        for lvg in self.lvg_dict.itervalues():
            lvg.formatAll()
