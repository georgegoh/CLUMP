#!/usr/bin/env python
# $Id: test_partitiontool.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#
import os 
import copy
from primitive.system.hardware.partitiontool import DiskProfile
from primitive.system.hardware.filesystems import Ext2Viewer
from primitive.system.hardware.lvm202 import  probeLVMEntity 
from primitive.system.hardware.probe import getSCSIPartitions
from os import walk 
from primitive.support.util import runCommand
from tempfile import mkdtemp
from nose import SkipTest
from path import path
from fcntl import ioctl
from primitive.support.type import Struct
from primitive.system.hardware.errors import MountpointAlreadyUsedError
from primitive.system.hardware.errors import PartitionSizeTooLargeError
from primitive.system.hardware.errors import PartitionIsPartOfVolumeGroupError
from primitive.system.hardware.errors import LogicalVolumeGroupStillInUseError
from primitive.system.hardware.errors import *
from nose.tools import assert_raises

IOC_NRSHIFT = 0
IOC_NRBITS = 8
IOC_TYPESHIFT = (IOC_NRSHIFT + IOC_NRBITS)

def ioctlNoForBLKRRPART():
     return ((0x12 << IOC_TYPESHIFT) | \
             (95 << IOC_NRSHIFT))

def rereadPartitionTable(disk):
    try:
        fd = os.open(disk, os.O_RDONLY)
    except EnvironmentError, (e, str):
        print 'Open %s failed: %s' % (disk, str)
        raise e

    runCommand('sync')

    try:
        blkrrpart = ioctlNoForBLKRRPART()
        ioctl(fd, blkrrpart)
    except EnvironmentError, (e, str):
        print 'IOCTL failed: %s' % str

    os.fsync(fd)
    os.close(fd)

    runCommand('sync')


def diskMarkedForTest(disk):
    """
    Check that the given disk is marked for testing. It is positively marked
    if it passes the following criteria:
        a. It has a loop partition layout.
        b. It is mountable as an ext2 device.
        c. At the root of this device is a file called 'kusu_diskprofile_test_disk'
    """
    if disk.pedDisk.type.name != 'loop':
        print disk.pedDisk.type.name
        return False
    print "Disk is loop"
    try:
        Ext2Viewer(disk.path)
        print "Disk is Ext2"
        is_marked = False
        mntpnt = path(mkdtemp(prefix='KusuDiskProfileTest'))
        stdout, stderr = runCommand('mount %s %s' % (disk.path, mntpnt))
        if stderr:
            raise RuntimeError, 'mount failed:\nout:%s\nerr:%s' % (stdout, stderr)
        dir_filelist = walk(mntpnt).next()[2]
        if 'kusu_diskprofile_test_disk' in dir_filelist:
            print "Disk has file"
            is_marked = True
        runCommand('umount %s' % mntpnt)
        mntpnt.rmtree()
    except:
        is_marked = False
    return is_marked

def markTestDisk(disk):
    """
    !!! USE WITH CAUTION: DESTRUCTIVE OPERATION !!!
    Mark a disk to be used for the DiskProfile test. This function is symmetrical
    to the function diskMarkedForTest.
    """
    runCommand('mkfs.ext2 -F %s' % disk.path)
    mntpnt = path(mkdtemp(prefix='KusuDiskProfileTest'))
    stdout, stderr = runCommand('mount %s %s' % (disk.path, mntpnt))
    if stderr:
        errMsg = 'mount failed:\nout:%s\nerr:%s\n' % (stdout, stderr)
        errMsg += 'You need to mark %s for DiskProfile test manually.' % disk.path
        raise RuntimeError, errMsg
    stdout, stderr = runCommand('touch %s/kusu_diskprofile_test_disk' % mntpnt)
    if stderr:
        errMsg = 'touch failed:\nout:%s\nerr:%s\n' % (stdout, stderr)
        errMsg += 'You need to mark %s for DiskProfile test manually.' % disk.path
        runCommand('umount %s' % mntpnt)
        mntpnt.rmtree()
        raise RuntimeError, errMsg
    runCommand('umount %s' % mntpnt)
    mntpnt.rmtree()

    rereadPartitionTable(disk.path)
    print "%s successfully marked.\n" % disk.path 


class TestDiskProfile:
    """Test cases for the DiskProfile class.
       Testing the DiskProfile class can be a dangerous business - an
       accident can wipe out the existing partitions of the test
       machine that need to stay, so we need to be extra careful to
       identify and only use those disks that are marked in a special way.
    """
    def setup(self):
        if os.getuid() != 0:
            raise SkipTest, 'Partitiontool tests must be run as root user.\n'

        self.dp = DiskProfile(fresh=False)
        marked_disks = []
        unmarked_disks = []
        for key,disk in self.dp.disk_dict.iteritems():
            if diskMarkedForTest(disk):
                marked_disks.append(key)
            else:
                unmarked_disks.append(key)

        if not marked_disks:
            errMsg = 'No disks marked for DiskProfile test on this machine.'
            errMsg += 'Disks marked for DiskProfile test must:\n'
            errMsg += '\ta. Have a loop partition layout(i.e., mkfs.ext2 /dev/sdb).\n'
            errMsg += '\tb. Be mountable as an ext2 device.\n'
            errMsg += '\tc. At the root directory, contain a file called '
            errMsg += '"kusu_diskprofile_test_disk".'
            raise SkipTest, errMsg 

        if self.dp.pv_dict or self.dp.lvg_dict or self.dp.lv_dict:
            errMsg = 'The DiskProfile tests cannot be performed on a system with '
            errMsg += 'LVM volumes.'
            raise SkipTest, errMsg

        for key in unmarked_disks:
            self.dp.disk_dict.pop(key)

        if set(marked_disks) != set(self.dp.disk_dict.keys()):
            errMsg = 'Internal Error: DiskProfile disks are not all marked for test.'
            raise SkipTest, errMsg

        # Reasonably sure that we're not messing with any disk we actually want untouched here.
        for disk in self.dp.disk_dict.values():
            runCommand('dd if=/dev/zero of=%s bs=1k count=10' % disk.path)

        self.dp = DiskProfile(fresh=False)
        for key in unmarked_disks:
            self.dp.disk_dict.pop(key)

        if set(marked_disks) != set(self.dp.disk_dict.keys()):
            errMsg = 'Internal Error: DiskProfile disks are not all marked for test.'
            raise SkipTest, errMsg

        # for test fstab probe and parse
        self.fscontent = """
# Test fstab, taken from my system
/dev/VolGroup00/LogVol00    /           ext3    defaults        1 1
# LABEL=/boot                 /boot       ext3    defaults        1 2
devpts                      /dev/pts    devpts  gid=5,mode=620  0 0
tmpfs                       /dev/shm    tmpfs   defaults        0 0
proc                        /proc       proc    defaults        0 0
sysfs                       /sys        sysfs   defaults        0 0
/dev/VolGroup00/LogVol01    swap        swap    defaults        0 0
# More from Hirwan's
    /dev/sda6                   /hd6        ext3    acl,user_xattr  1 1
# Mike's

/dev/cdroms/cdrom0          /mnt/cdrom  iso9660 noauto,ro       0 0
       # Dirty comment here... we're all
#over
    # the place, but shouldn't be picked up.
"""
        self.fscontent_wanteddic = {'/dev/sda6': Struct({'mntpnt': '/hd6', 'fs_type': 'ext3'}), 
                                    '/dev/VolGroup00/LogVol00': Struct({'mntpnt': '/', 'fs_type': 'ext3'})}


    def teardown(self):
        self._clearLVM()
        self.dp.commit(ignore_errors=True)
        self._checkLVMClear()
        self._nukeDisks()

    def _clearLVM(self):
        for lv in self.dp.lv_dict.values():
            self.dp.delete(lv)
        for lvg in self.dp.lvg_dict.values():
            self.dp.delete(lvg)
        for pv in self.dp.pv_dict.values():
            self.dp.delete(pv.partition)
 
    def _checkLVMClear(self):
        stdout,stderr = runCommand('lvm pvscan')
        if not (stdout.strip().endswith('No matching physical volumes found') or \
           stderr.strip().endswith('No matching physical volumes found')):
            raise RuntimeError, 'LVM Physical Volumes not cleared.'
        stdout,stderr = runCommand('lvm vgscan')
        if not (stdout.strip().endswith('No volume groups found') or \
           stderr.strip().endswith('No volume groups found')):
            raise RuntimeError, 'LVM Volume Groups not cleared.'
        stdout,stderr = runCommand('lvm lvscan')
        if not (stdout.strip().endswith('No volume groups found') or \
           stderr.strip().endswith('No volume groups found')):
            raise RuntimeError, 'LVM Logical Volumes not cleared.'
 
    def _nukeDisks(self):
        disk_keys_to_mark = self.dp.disk_dict.keys()
        for disk in self.dp.disk_dict.values():
            markTestDisk(disk)

        dp = DiskProfile(fresh=False)
        probe_marked_disk_keys = []
        for key,disk in dp.disk_dict.iteritems():
            if diskMarkedForTest(disk):
                probe_marked_disk_keys.append(key)

        to_mark_set = set(disk_keys_to_mark)
        probed_set = set(probe_marked_disk_keys)
        if not to_mark_set.issubset(probed_set):
            errMsg = 'The following test disks could not be marked for testing '
            errMsg += 'again. Please note and perform manual marking:\n'
            errMsg += '%s' % list(to_mark_set - probed_set)
            raise RuntimeError, errMsg


    def _verifyPartitionSize(self, size_MB, partition):
        diff = abs(partition.size_MB - size_MB)
        disk = partition.disk
        cylinder_size = disk.heads * disk.sectors * disk.sector_size
        cylinder_size_MB = cylinder_size / 1024 / 1024
        if diff >= cylinder_size_MB:
            return False
        return True
        
    def __verifyLogicalVolumeSize(self, size_MB, lv):
        diff = abs(lv.size_MB - size_MB)
        vg = lv.group
        extent_size_MB = vg.extent_size / 1024 / 1024
        if diff > extent_size_MB:
            return False
        return True

    def _makePrimaryPartitions(self, disk_id, fs_types=['ext3','linux-swap','ext3']):
        """
        Make 3 equally sized partitions on the disk.
        """
        disk_size = self.dp.disk_dict[disk_id].size / 1024 / 1024
        p_size = disk_size / 3
        print "Disk size: %d, Partition size: %d" % (disk_size, p_size)
        for i in xrange(2):
            print "Making partition %d" % i
            self.dp.newPartition(disk_id, p_size, True, fs_types[i], '/'+disk_id+'/%d' % i)
        self.dp.newPartition(disk_id, 1, True, fs_types[2], '/'+disk_id+'/3', fill=True)

    def _makeLogicalPartitions(self, disk_id, fs_types=['ext3','linux-swap','ext3','ext3','ext2']):
        """
        Make 5 partitions - should result in 3 primary, 1 extended and 2 logical.
        """
        disk_size = self.dp.disk_dict[disk_id].size / 1024 / 1024
        p_size = disk_size / 5
        for i in xrange(4):
            self.dp.newPartition(disk_id, p_size, True, fs_types[i], '/'+disk_id+'/%d' % i)
        self.dp.newPartition(disk_id, p_size, True, fs_types[4], '/'+disk_id+'/4')

    def _makePrimaryPartitionsWithPV(self, disk_id):
        self._makePrimaryPartitions(disk_id, ['ext3', 'linux-swap', 'physical volume'])

    def _makeLogicalPartitionsWithPV(self, disk_id):
        self._makePrimaryPartitions(disk_id, ['ext3', 'linux-swap', 'physical volume'])

    def _makeVolumeGroupPerPV(self):
        for pv in self.dp.pv_dict.itervalues():
            self.dp.newLogicalVolumeGroup(pv.name + '_LVG', '32M',  [pv])

    def _makeVolumeGroupUseAllPVs(self):
        self.dp.newLogicalVolumeGroup('Big VG', '32M', self.dp.pv_dict.keys())

    def _makeLogicalVolumesWithVG(self, vg):
        """
        Make 2 logical volumes on the volume group.
        """
        fs_types = ['ext3', 'linux-swap', 'physical volume']
        size = vg.extentsFree() * vg.extent_size / 1024 / 1024
        for i in xrange(2):
            self.dp.newLogicalVolume(vg.name + '_LV%d' % i, vg, size/2,
                                     fs_types[i], '/'+vg.name+'/lv%d' % i)

    def _makeSingalLogicalVolumeWithVG(self, vg):
        """
        Make 1 single logical volumes on the volume group.
        """
        size = vg.extentsTotal() * vg.extent_size / 1024 / 1024
        self.dp.newLogicalVolume('LV0', vg, size/2,
                                 'ext3', '/'+vg.name+'/lv0')

    def _makeLogicalVolumesWithVGPoorFreeSize(self, vg):
        ''' 
        Make 1 single volume which size is larger than the left free size of the VG,
        this volume is set to fill the left disk.
        '''
        fs_types = ['ext3', 'linux-swap', 'physical volume']
        size = ( vg.extentsFree() * vg.extent_size / 1024 / 1024 ) + (vg.extent_size)
        self.dp.newLogicalVolume(vg.name + '_LV0', vg, size, 
                                 fs_types[0], '/'+vg.name+'/lv0', True)

    def _makeSinglePartitionFromDisk(self):
        ''' Make a signle partition '''
    
        for disk in self.dp.disk_dict.iterkeys():
            size = self.dp.disk_dict[disk].size / 1024 / 1024
            self.dp.newPartition(disk, size/2, True, 'physical volume', None)

    def _makeLogicalVolumeWithoutVG(self):
        ''' Make 2 logical volumes, make volume group first. '''
    
        # make LVM group first
        self._makeSinglePartitionFromDisk()
        self._makeVolumeGroupPerPV()
        self.dp.commit()
    
        # make Logical Volumes
        for everylvg in self.dp.lvg_dict.itervalues():
            self._makeLogicalVolumesWithVG(everylvg)
        self.dp.commit()
         
        if self.dp.lv_dict == {}:
            raise RuntimeError, 'Create Logical Volumes Failed.'

    def _makeLogicalVolumeWithoutVGPoorSize(self):
        ''' Make LV with required size larger than free size '''
    
        # make LVM group first
        self._makeSinglePartitionFromDisk()
        self._makeVolumeGroupPerPV()
        self.dp.commit()

        # make Logical Volumes
        for everylvg in self.dp.lvg_dict.itervalues():
            self._makeLogicalVolumesWithVGPoorFreeSize(everylvg)
        self.dp.commit()


    def _makeSingleLogicalVolumeWithoutVG(self):
        ''' Make 1 single LV '''

        # make LVM group first
        self._makeSinglePartitionFromDisk()
        self._makeVolumeGroupPerPV()
        self.dp.commit()

        # make Logical Volumes
        for everylvg in self.dp.lvg_dict.itervalues():
            self._makeSingalLogicalVolumeWithVG(everylvg)
        self.dp.commit(ignore_errors=True)

    def _createFstabFileWithStr(self, content):
        ''' create a fstab file '''

        if not content:
            errMsg = 'Must write something into the fstab file!'
            raise RuntimeError, errMsg
        for lv in self.dp.lv_dict.itervalues():
            lv.format()
            mountpath = path ( lv.mountpoint )
            if not mountpath.exists():
                mountpath.makedirs()
            lv.mount(lv.mountpoint)

            fstabdir = path(mountpath / 'etc')
            if not fstabdir.exists():
                fstabdir.makedirs()
            fstabpath = path(fstabdir / 'fstab')
            if not fstabpath.exists():
                fstabpath.touch()

            # write content
            fstab = open(fstabpath, 'w')
            fstab.write(content)
            fstab.flush()
            fstab.close()

            lv.unmount()
            mountpath.removedirs()

    def __verifyUpdateInSysFS(self):
        """ For each disk eg sda, sdb , probe /sys/block/disk/ 
        Retreive a list of strings starting with diskname 
        Eg: for /sys/block/sda all names starting with sda are returned - sda1 sda2 etc
        Compare the set of partitions vs the ones we have in memory """
        for key,disk in self.dp.disk_dict.iteritems(): # sda sdb etc
            parts = getSCSIPartitions(path('/sys/block') / key)  #sda1 sda2 etc
            disk_parts = [key+str(num) for num in disk.partition_dict.keys()] 
            assert set(parts) == set(disk_parts),"Sysfs_parts=%s, Disk_parts=%s" % (parts, disk_parts)
            for v in parts:
                # eg: cat sys/block/sda/sda1/size. Multiply result by 512 as its in 512 byte blocks
                size = int(runCommand("cat /sys/block/%s/%s/size" % (key,v))[0].strip())*512 
                assert size == self.dp.disk_dict[key].partition_dict[int(v[len(key):])].size

            

    def testPrimaryPartitions(self):
        for disk_id in self.dp.disk_dict.keys():
            self._makePrimaryPartitions(disk_id)
        self.dp.commit()
        self.__verifyUpdateInSysFS()

    
        
    def testNewPartition(self):
        """ Test for creating a new partition
        Test1: Positive test case - create an ext2 file system without a mount point and  verify update to SysFS
        Test2: Positive test case - create a physical volume without a mount point and verify update to SysFS
        Test3: Positive test case - create an ext2 file system with a mount point and verify update to SysFS
        Test4: Negative test case - create a physical volume with a mount point and verify update to SysFS """

        # newPartition(self,disk_id,size_MB,fixed_size,fs_type,mountpount, fill=False)
        # partition is a dictionary of the following
        #     partition = {'size_MB': size, 'fill': fill,
        #                  'fs': fs, 'mountpoint': mountpoint}
        partition = self.dp.newPartition('sdb',100,False,'ext2',None)
        self.dp.commit()
        self.__verifyUpdateInSysFS()
        assert not partition.mountpoint
        assert partition.fs_type == 'ext2'
        self.dp.deletePartition(partition)
        self.dp.commit()
        #Test Case 2: Positive test case create a physical volume without a mount point and verify update to SysFS
        partition = self.dp.newPartition('sdb',100,False,'physical volume',None)
        self.dp.commit()
        self.__verifyUpdateInSysFS()
        assert not partition.mountpoint
        assert not partition.fs_type

        self.dp.deletePartition(partition)
        self.dp.commit()
        #Test Case 3:
        partition = self.dp.newPartition('sdb',100,False,'ext2',None)
        self.dp.commit()
        self.__verifyUpdateInSysFS()
        assert partition.fs_type == 'ext2'
        self.dp.deletePartition(partition)
        self.dp.commit()
        self.__verifyUpdateInSysFS()
        #XXX - Test Case 4
        #Currently the mountpoint is silently ignored so this is a redundant case
        
    def testEditPartiton(self):
        """ edit a partition that is a part of a volume group
        edit a partition that is already mounted - send an obj in pv_dict
        there is no pv Group defined as yet. so it will error. Group = None now
        Test Case 1: Negative test - a  partition which is part of an LVG cannot be edited
        Test Case 2: Negative test - We cannot use a mointpount alreadt in use
        Test Case 3: Negative test - Requested partition size too large
        Test Case 4: Positive test - Resize existing partition and fill it all the way
        Test Case 5: Positive test - Resize the filled parititon to a Fixed size
        Test Case 6: Positive test - Shrink the partition, but fill is true so it expands 
        Test Case 7: Check changes are commited to proc """
        assert self.dp.disk_dict['sdb'],"Disk SDB required for tests"
        partition = self.dp.newPartition('sdb',100,True,'physical volume',None)
        #add it to a group
        pv = self.dp.pv_dict[partition.path]
        self.dp.newLogicalVolumeGroup('Testpart', '32M', [pv])
        lvg = self.dp.lvg_dict['Testpart']
        lv = self.dp.newLogicalVolume('BigV', lvg, 12)
        self.dp.commit(ignore_errors=True)
        assert_raises(PartitionIsPartOfVolumeGroupError,self.dp.editPartition,partition,150,True,'ext2',None)
        self.dp.deleteLogicalVolume(lv)
        self.dp.deleteLogicalVolumeGroup(lvg)
        self.dp.deletePartition(partition)
        self.dp.commit(ignore_errors=True)
        #test case 2 ext2fs paritition with a mountpoint
        #if there is a partition and current partition is not in the mountpoint list we error
        partition1 = self.dp.newPartition('sdb',100,True,'ext2','/test')
        partition2 = self.dp.newPartition('sdb',100,True,'ext2',None)
        self.dp.commit()
        assert_raises(MountpointAlreadyUsedError,self.dp.editPartition,partition2,150,False,'ext2','/test')
        # test case 3 partition too large
        assert_raises(PartitionSizeTooLargeError,self.dp.editPartition,partition1,partition1.size_MB + (self.dp.disk_dict['sdb'].availableSpaceForPartition(partition1)/1024/1024)+100,True,'ext2','/large')
        psize = partition2.size_MB
        #test case 4 positive - should work 
        self.dp.editPartition(partition2,150,False,'ext2','/test2')
        self.dp.commit()
        assert partition2.size_MB > psize
        psize = partition2.size_MB
        #test case 5 fill a partition  - also verify changes in SysFS
        self.dp.editPartition(partition2,150,True,'ext2','/test2')
        self.dp.commit()
        assert partition2.size_MB < psize
        psize = partition2.size_MB
        self.__verifyUpdateInSysFS()
        #test case 7 shrink a partition - the fill takes precedence - it will be bigger than 
        assert self.dp.editPartition(partition2,100,False,'ext2','/test2') # shrink it back
        self.dp.commit()
        self.__verifyUpdateInSysFS()
        assert partition2.size_MB > psize
        self.dp.deletePartition(partition1)
        self.dp.deletePartition(partition2)
        self.dp.commit()
        self.__verifyUpdateInSysFS()

    def testDeletePartition(self):
        """create a bunch of partitions and delete it
        Test Case 1 : Negative case - cannot delete if part of LVG
        Test Case 2 : Positive case - deletion works
        Test Case 3 : Check changes are comitted to proc
        """
        #Test case 1 : create and delete
        partition = self.dp.newPartition('sdb',100,False,'physical volume',None)

        pv = self.dp.pv_dict[partition.path]
        self.dp.newLogicalVolumeGroup('Testpart', '32M', [pv])
        lvg = self.dp.lvg_dict['Testpart']
        lv = self.dp.newLogicalVolume('BigV', lvg, 12)
        assert_raises(PartitionIsPartOfVolumeGroupError,self.dp.editPartition,partition,150,False,'ext2',None)
        self.dp.deleteLogicalVolume(lv)
        self.dp.deleteLogicalVolumeGroup(lvg)
        self.dp.deletePartition(partition)
        self.dp.commit(ignore_errors=True)
        self.__verifyUpdateInSysFS()

        #Test case 2 :  non volume - filesystem
        partition = self.dp.newPartition('sdb',100,False,'ext2',None)
        self.dp.commit()
        self.dp.deletePartition(partition)
        self.dp.commit()
        self.__verifyUpdateInSysFS()

    def testCreateLogicalVolumeGroup(self):
        ''' Unit Test: testCreateLogicalVolumeGroup '''

        #firstly, create a dummy partition for the test
        partition = self.dp.newPartition('sdb', 100, False, 'physical volume', None)
        pv = self.dp.pv_dict[partition.path]
        
        #if 'Big VG' not in self.dp.lvg_dict.keys():
        #Test Case 1: (Negative) Invalid extent size (too small)
        assert_raises(InvalidVolumeGroupExtentSizeError,
                      self.dp.newLogicalVolumeGroup,
                      'BigVG', '32', [pv])
                        
        #Test Case 2: (Negative) Invalid extent size (not in range 2~512 or not even number)
        assert_raises(InvalidVolumeGroupExtentSizeError,
                      self.dp.newLogicalVolumeGroup,
                      'BigVG', '1M', [pv])

        assert_raises(InvalidVolumeGroupExtentSizeError,
                      self.dp.newLogicalVolumeGroup,
                      'BigVG', '514M', [pv])

        assert_raises(InvalidVolumeGroupExtentSizeError,
                      self.dp.newLogicalVolumeGroup,
                      'BigVG', '25M', [pv])
           
        #Test Case 3: (Postive)
        self.dp.newLogicalVolumeGroup('BigVG', '32M', [pv])
        assert 'BigVG' in self.dp.lvg_dict.keys(), \
                "Logical Volume Group (name: BigVG, extent size: 32M) was not successfully created."

        self.dp.commit(ignore_errors=True)

        name = 'BigVG'
        lvg = self.dp.lvg_dict[name]

        # Achieve total PE, PE Size, and VG Size
        probe_dict = { 'total_pe' : 'Total PE',
                       'pe_size'  : 'PE Size',
                       'vg_size'  : 'VG Size' }
        res = probeLVMEntity('lvm vgdisplay', probe_dict)
        total_pe = long(res['total_pe'])
        pe_size = long(res['pe_size'][:-3])
        vg_size = long(res['vg_size'][:-3])

        # if the vg was created successfully, then :
        # total_pe = lvg.extentsTotal and lvg.extent_size = 32M and pe_size = 32M
        assert total_pe == lvg.extentsTotal() and lvg.extent_size == 32 * 1024 * 1024 and pe_size == 32, \
                "Logical Volume Group (name: BigVG, extent size: 32M) was not successfully created."
        
        #Test Case 4: (Negative) Duplicate group name
        try:
            lvg = self.dp.lvg_dict['BigVG']
            self.dp.newLogicalVolumeGroup('BigVG', '52M', [pv])
        except DuplicateNameError, e:
            pass
        assert lvg.extent_size_humanreadable == '32M', \
                "Logical Volume Group with duplicate name should not be created."

        self.dp.commit()

        # Due to duplicate name, BigVG should not be recreated.
        probe_dict = { 'vg_name' : 'VG Name',
                       'pe_size' : 'PE Size' }
        res = probeLVMEntity('lvm vgdisplay', probe_dict)
        vg_name = res['vg_name']
        pe_size = long(res['pe_size'][:-3])
        assert vg_name == 'BigVG' and pe_size != 52, \
                "Logical Volume Group with duplicate name should not be created."
                   
    def testEditLogicalVolumeGroup(self):
        ''' Unit Test: testEditLogicalVolumeGroup '''

        #firstly, create a dummy partition for the test
        partition = self.dp.newPartition('sdb', 100, False, 'physical volume', None)
        pv = self.dp.pv_dict[partition.path]
        self.dp.newLogicalVolumeGroup('BigVG', '32M', [pv])
        lvg = self.dp.lvg_dict['BigVG']

        self.dp.commit()

        # Achieve the physical volume's pv name and vg name
        probe_dict = { 'pv_name' : 'PV Name',
                       'vg_name' : 'VG Name' }
        res = probeLVMEntity('lvm pvdisplay', probe_dict)
        pv_name_old = res['pv_name']
        vg_name_old = res['vg_name']
        
        #old_pvs keesp the original pv_list
        old_pvs = lvg.pv_dict.keys()

        partition1 = self.dp.newPartition('sdb', 80, False, 'physical volume', None)
        pv1 = self.dp.pv_dict[partition1.path]
        self.dp.editLogicalVolumeGroup(self.dp.lvg_dict['BigVG'], [pv1])

        self.dp.commit()

        # Achieve the physical volume's pv name and vg name after the editing
        probe_dict = { 'pv_name' : 'PV Name',
                       'vg_name' : 'VG Name' }
        res = probeLVMEntity('lvm pvdisplay', probe_dict)
        pv_name_new = res['pv_name']
        vg_name_new = res['vg_name']
        
        #new_pvs keeps the new pv_list
        new_pvs = lvg.pv_dict.keys()

        assert old_pvs != new_pvs, \
                "Logical Volume Group was not edited successfully."

        assert vg_name_old == 'BigVG' and vg_name_old == vg_name_new and pv_name_old != pv_name_new, \
                "Logical Volume Group was not edited successfully."
        
    def testDeleteLogicalVolumeGroup(self):
        ''' Unit Test: testDeleteLogicalVolumeGroup '''
        
        #firstly, create a dummy partition for the test
        partition = self.dp.newPartition('sdb', 100, False, 'physical volume', None)
        pv = self.dp.pv_dict[partition.path]

        #create a logical volume group
        self.dp.newLogicalVolumeGroup('BigVG', '32M', [pv])
        lvg = self.dp.lvg_dict['BigVG']

        #create a logical volume
        lv = self.dp.newLogicalVolume('BigV', lvg, 12)

        self.dp.commit()

        probe_dict = { 'lv_name' : 'LV Name' }
        res = probeLVMEntity('lvm lvdisplay', probe_dict)
        lv_name = res['lv_name']

        # if the lv was successfully created to lvg
        if lv_name.find('BigVG/BigV'):
            #Test case 1: (Negative) Delete a logical volume group with logical volume still in use 
            assert_raises(LogicalVolumeGroupStillInUseError,
                          self.dp.deleteLogicalVolumeGroup, lvg)
            assert 'BigVG' in self.dp.lvg_dict.keys(), \
                    "Logical Volume Group should not be deleted when there is logical volume still in use."

            self.dp.commit()

            probe_dict = { 'vg_name' : 'VG Name' }
            res = probeLVMEntity('lvm vgdisplay', probe_dict)
            
            assert len(res) > 0 and res['vg_name'] == 'BigVG', \
                    "Logical Volume Group should not be deleted when there is logical volume still in use."

            #Test Case 2: (Positive)
            self.dp.deleteLogicalVolume(lv)
            self.dp.deleteLogicalVolumeGroup(lvg)
            assert 'BigVG' not in self.dp.lvg_dict.keys(), \
                    "Logical Volume Group was not deleted successfully."

            self.dp.commit()

            # if 'BigVG' vg record is still available, then the deleting was not successful
            probe_dict = { 'vg_name' : 'VG Name' }
            res = probeLVMEntity('lvm vgdisplay', probe_dict)
            assert len(res) == 0, \
                    "Logical Volume Group was not deleted successfully."
   
    def testLogicalVolume(self):
        '''Test newLogicalVolume '''

        self._makeLogicalVolumeWithoutVG()
        # to see if Volumes were created
        dict = {'gpname' : 'VG Name',
                'lvname' : 'LV Name',
                'lenum' : 'Current LE'}
        for everylv in self.dp.lv_dict.itervalues():
            res_dict = probeLVMEntity('lvm lvdisplay %s' % everylv.path, dict)
            assert res_dict['lvname'] == everylv.path
            assert res_dict['gpname'] == everylv.group.name
            assert int(res_dict['lenum']) * 32 * 1024 * 1024 == everylv.size

    def testLogicalVolumePoorSize(self):
        '''Test newLogicalVolume: not enough size. '''
        
        excepoccur = False
        try :
            self._makeLogicalVolumeWithoutVGPoorSize()
        except OutOfSpaceError, e:
            excepoccur = True
        assert excepoccur

    def testLogicalVolumeEdit(self):
        ''' test editLogicalVolume '''

        self._makeSingleLogicalVolumeWithoutVG()

        dict = {'gpname' : 'VG Name',
                'lvname' : 'LV Name',
                'lenum' : 'Current LE'}
        # larger its size.
        for lv in self.dp.lv_dict.itervalues():
            res_dict = probeLVMEntity('lvm lvdisplay %s' % lv.path, dict)
            orgsize = copy.copy(lv.size)
            newsize = (lv.size * 2) / 1024 / 1024 
            self.dp.editLogicalVolume(lv, newsize, 
                                      lv.fs_type, lv.mountpoint)
            self.dp.commit()
            assert lv.size == orgsize * 2
            assert lv.size == int(res_dict['lenum']) * 32 * 1024 * 1024 * 2

            res_new_dict = probeLVMEntity('lvm lvdisplay %s' % lv.path, dict)
            assert int(res_dict['lenum']) * 2 == int(res_new_dict['lenum'])

        # shrink its size.
        for lv in self.dp.lv_dict.itervalues():
            res_dict = probeLVMEntity('lvm lvdisplay %s' % lv.path, dict)
            orgsize = copy.copy(lv.size)
            newsize = (lv.size / 2) / 1024 / 1024
            self.dp.editLogicalVolume(lv, newsize, lv.fs_type, lv.mountpoint)
            self.dp.commit()
            assert lv.size * 2 == orgsize
            assert lv.size == int(res_dict['lenum']) * 32 * 1024 * 1024 / 2

            res_new_dict = probeLVMEntity('lvm lvdisplay %s' % lv.path, dict)
            assert int(res_dict['lenum']) == int(res_new_dict['lenum']) * 2

        # change fs type
        fs_types = ['ext3', 'ext2', 'linux-swap']
        for lv in self.dp.lv_dict.itervalues():
            for types in fs_types:
                orgtype = copy.copy(types)
                self.dp.editLogicalVolume(lv, lv.size_MB, types, lv.mountpoint)
                self.dp.commit()
                assert orgtype == lv.fs_type

        # change fs type and size at the same time
        for lv in self.dp.lv_dict.itervalues():
            res_dict = probeLVMEntity('lvm lvdisplay %s' % lv.path, dict)

            for types in fs_types:
                if types != lv.fs_type:
                    break
            assert not types == lv.fs_type

            lvsize_MB = int(lv.size_MB)
            delta = lv.group.extent_size / 1024 / 1024
            self.dp.editLogicalVolume(lv, (lvsize_MB + delta), types, lv.mountpoint)
            self.dp.commit()
            assert lv.fs_type == types
            assert lv.size_MB == lvsize_MB + delta, 'lv.size=%d, lvsize*2=%s' % (lv.size, lvsize*2)

            res_new_dict = probeLVMEntity('lvm lvdisplay %s' % lv.path, dict)
            assert int(res_dict['lenum']) + 1 == int(res_new_dict['lenum'])

    def testDeleteLogicalVolume(self):
        ''' test deleteLogicalVolume '''
        self._makeSingleLogicalVolumeWithoutVG()

        lvdict = copy.copy(self.dp.lv_dict)
        assert lvdict != {}

        # delete action
        for lv in lvdict.itervalues():
            self.dp.deleteLogicalVolume(lv)
            self.dp.commit()

        assert self.dp.lv_dict == {}

        probe_dict = { 'name' : 'LV Name'}
        res_dict = probeLVMEntity('lvm lvdisplay', probe_dict)

        assert res_dict == {}

    def testExtractFstab(self):
        ''' test extractFstabToDevices '''

        self._makeSingleLogicalVolumeWithoutVG()
        self._createFstabFileWithStr(self.fscontent)

        # call function:
        for lv in self.dp.lv_dict.itervalues():
            devmap = {}
            devmap = self.dp.extractFstabToDevices(lv, loc='etc/fstab')
            assert devmap == self.fscontent_wanteddic

    def testExtractFstabWithLABEL(self):
        raise SkipTest, 'not implemented.'

    def testExtractFstabWithUUID(self):
        raise SkipTest, 'not implemented.'

    def testLookForFsTab(self):
        '''test lookForFstab'''
        self._makeSingleLogicalVolumeWithoutVG()
        self._createFstabFileWithStr(self.fscontent)

        # call function:
        for lv in self.dp.lv_dict.itervalues():
            res, path = self.dp.lookForFstab(lv, fstab_path='etc/fstab')
            assert res == True
            assert path == 'etc/fstab'

    def testLookForFsTabNotFound(self):
        '''test lookForFstab'''
        self._makeSingleLogicalVolumeWithoutVG()

        for lv in self.dp.lv_dict.itervalues():
            lv.format()
            res, path = self.dp.lookForFstab(lv, fstab_path='etc/fstab')
            assert res == False
            assert path == None
