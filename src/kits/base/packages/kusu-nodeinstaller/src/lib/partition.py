#!/usr/bin/env python
# $Id: partition.py 3536 2010-02-22 11:04:30Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

import sys
from primitive.system.hardware.partitiontool import DiskProfile
from primitive.system.hardware.disk import Partition
from kusu.nodeinstaller import NodeInstInfoHandler
from kusu.nodeinstaller.partitionfilterchain import *
from kusu.installer.defaults import getPartitionTuple
from os.path import basename
from pprint import PrettyPrinter
import kusu.util.log as kusulog
from kusu.util.errors import KusuError, InvalidPartitionSchema
from primitive.system.hardware.errors import *
logger = kusulog.getKusuLog('nodeinstaller.NodeInstaller')

class SchemaMatcher:
    """
        This class will attempt to match a partition schema (physical volumes)
        to a specific layout that will match up with available disk space.
    """
    
    PARTITION_SCHEMA = []
    
    def __init__(self, schema, disk_profile):
        
        self.PARTITION_SCHEMA = schema
        self.disk_profile = disk_profile
        
    def calculateAvailableSpace(self):
        """
            This method will figure out the disk layout and where there is available
            space for re-use. It will return an array consisting of 'bins'. Each
            'bin' is just a map denoting start and end sectors on disk. 
        """
        spaceArray = []
        for disk in self.disk_profile.disk_dict.values() :
            
            #reset position pointer to first sector for next disk
            currentPos = 1 #keeps current sector position
            extendedStart = 0
            extendedEnd = 0
            isExtended = False
            
            for partition in disk.partition_dict.values() :
                
                if (currentPos >= extendedStart and currentPos <= extendedEnd ):
                    isExtended = True
                else:
                    isExtended = False
                
                if (partition.pedPartition.native_type == 5) : #check for extended partition
                    extendedStart = partition.start_sector
                    extendedEnd = partition.end_sector
                    
                    spaceArray.append({'start_sector' : currentPos,
                                       'end_sector' : partition.start_sector - 1,
                                       'isExtended' : True
                                       })
                    #Update the currentPos marker to be the start of the extended space
                    currentPos = partition.start_sector + 1
                                        
                elif (partition.start_sector > currentPos):
                    
                    spaceArray.append({'start_sector' : currentPos,
                                       'end_sector' : partition.start_sector - 1,
                                       'isExtended' : isExtended
                                       })
                    currentPos = partition.end_sector + 1
                
 
            if (currentPos >= extendedStart and currentPos <= extendedEnd ):
                isExtended = True
            else:
                isExtended = False

            #check for empty block of space at end of extended partition
            if (currentPos < extendedEnd):
                spaceArray.append({'start_sector' : currentPos,
                                   'end_sector' : extendedEnd  -1,
                                   'isExtended' : isExtended
                                   })
                currentPos = extendedEnd    
            
            isExtended = False #reset extended flag                         
        
            #check for empty block of space after last partition
            if (currentPos < disk.length): #odd, would have expected disk.sectors to have this info
                spaceArray.append({'start_sector' : currentPos + 1,
                                   'end_sector' : disk.length,
                                   'isExtended' : isExtended 
                                   })
                        
        return spaceArray

    def combinations(self, items, n):
        if n==0: 
            yield []
        else:
            for i in xrange(len(items)):
                for cc in self.combinations(items[:i] + items[i+1:], n-1):
                    yield [items[i]] + cc
    
    def permutations(self, items):
        """
            Returns an iterable with all the permutations of the
            passed in list. This will be Factorial(len(items)) in size
            so beware!
        """        
        return self.combinations(items, len(items))       

    def getPartitionLayout(self):
        """
            This method is a brute-force approach to the knapsack problem. Even so, 
            since our partitions and potential schemas are small sets, it's pretty quick.
            This function will retrieve the *first* solution from the solution set.
            The first solution is not necessarily the optimal solution. 
            
        """
        availableSpace = self.calculateAvailableSpace()
        
        for schema in self.permutations(self.PARTITION_SCHEMA): 
            #reset our partList for next schema match
            partList = []  
            for block in availableSpace:
                
                partSizeCounter = 0
                blockSize = block['end_sector'] - block['start_sector']
                for partition in schema:
                    #we need to skip those schema entries that we already treated
                    if (partition in partList):
                        continue
                    
                    partSizeCounter = partSizeCounter + int(partition["size"])
                    
                    if (partSizeCounter <= blockSize):
                        #add this schema block into our list
                        partList.append({'partition' : partition,
                                         'sector_block' : block})
   
                    else:
                        #continue onto next iteration; since the sum of schema block sizes is now too big
                        #to fit into the available space
                        continue

            # The way this algorithm is constructed implies that once
            # our partList has (length == number of entries in PARTITION_SCHEMA)
            # then we will have a solution.      
            if len(partList) == len(self.PARTITION_SCHEMA ):
                #return the first solution 
                return partList
                             
        return [] #too bad. you don't have enough space :(    
                      

def partitionRulesPreservationDefault(rules):
    # Check new-style rules first.
    for p in rules:
        logger.debug('Checking part_rule for preserveDefault')
        p_id, value = translatePartitionOptions(p['options'], 'preserveDefault')
        if p_id and value.lower() == 'all':
            logger.debug('Default Preserve set to All.')
            return 'all'
        elif p_id and value.lower() == 'none':
            logger.debug('Default Preserve set to None.')
            return 'none'
        elif p_id and value.lower() == 'undefined':
            logger.debug('Default Preserve set to Undefined.')
            return 'undefined'
        
    # If new-style rules are not present, then fallback to checking
    # old-style rules.
    for p in rules:
        logger.debug('Checking part_rule for partitionID=*')
        p_id, value = translatePartitionOptions(p['options'], 'partitionID')
        if p_id and value=='*':
            if p['preserve'] == '0':
                logger.debug('Default Preserve set to None.')
                return 'none'
            elif p['preserve'] == '1':
                logger.debug('Default Preserve set to All.')
                return 'all'
    return 'undefined'                


def adaptNIIPartition(niipartition, diskprofile, appglobal):
    """ Adapt niipartition into a partitiontool schema. This schema can
        be passed along with a partitiontool diskprofile to setupDiskProfile
        method.

    """
    part_rules = niipartition.values()
    preserve = partitionRulesPreservationDefault(part_rules)

    if preserve == 'all':
        logger.debug('Default Preserve')
        pefc = PartitionEntriesFilterChainDefaultPreserve()
        pefc.filter_list.append(FilterOnFileSystem())
        pefc.filter_list.append(FilterOnPartitionType())
        pefc.filter_list.append(FilterOnLogicalVolume())
        pefc.filter_list.append(FilterOnMountpoints())
        pefc.filter_list.append(AssignMntPntForLV())
        pefc.filter_list.append(PropagateLVPreserveToPV())
            
 # The following rules are used for avalon(preserving ntfs)
        if appglobal['PRESERVE_NODE_IP'] == '1':
            pefc.filter_list.append(FilterMatchPartitionSchema())
            pefc.filter_list.append(FilterUseMBR())
            pefc.filter_list.append(FilterMatchPartitionUUID(appglobal['MASTER_UUID']))
    elif preserve == 'none':
        logger.debug('Default No Preserve')
        pefc = PartitionEntriesFilterChainDefaultNoPreserve()
        pefc.filter_list.append(AssignMntPntForLV())
        pefc.filter_list.append(FilterOnMountpointsNoPreserve())
        pefc.filter_list.append(FilterOnLogicalVolumeNoPreserve())
        pefc.filter_list.append(FilterOnPartitionTypeNoPreserve())
        pefc.filter_list.append(FilterOnFileSystemNoPreserve())
        pefc.filter_list.append(PropagateLVPreserveToPV())

# The following rules are used for avalon(preserving ntfs)
        if appglobal['PRESERVE_NODE_IP'] == '1':
            pefc.filter_list.append(FilterMatchPartitionSchema())
            pefc.filter_list.append(FilterUseMBR())
            pefc.filter_list.append(FilterMatchPartitionUUID(appglobal['MASTER_UUID']))
    else:
        logger.debug('Default Preserve Undefined Disks')
        pefc = PEFCPreserveUndefinedDisks()
        pefc.filter_list.append(AssignMntPntForLV())
        pefc.filter_list.append(FilterOnMountpointsNoPreserve())
        pefc.filter_list.append(FilterOnLogicalVolumeNoPreserve())
        pefc.filter_list.append(FilterOnPartitionTypeNoPreserve())
        pefc.filter_list.append(FilterOnFileSystemNoPreserve())
        pefc.filter_list.append(PropagateLVPreserveToPV())

        if appglobal['PRESERVE_NODE_IP'] == '1':
# The following rules are used for avalon(preserving ntfs)
            pefc.filter_list.append(FilterMatchPartitionSchema())
            pefc.filter_list.append(FilterUseMBR())
            pefc.filter_list.append(FilterMatchPartitionUUID(appglobal['MASTER_UUID']))

    disk_profile = pefc.apply(part_rules, diskprofile)
    
    logger.debug('Before cleaning diskprofile:\n%s' % str(disk_profile))
    cleanDiskProfile(disk_profile)
    logger.debug('After cleaning diskprofile:\n%s' % str(disk_profile))

    pp = PrettyPrinter()
    logger.debug('Creating schema using rules:\n%s' % pp.pformat(part_rules))
    schema = createSchema(part_rules, diskprofile)

    #Modify the partition schema for '/boot', just a workaround for ensure '/boot' is primary partition.
    handlePartitionSchemaForBoot(schema, diskprofile)

    return schema, diskprofile
 
#In dualboot nodes, normally 1-2 primary partitions(Dell UP, Windows) are preserved,
#so if we define '/boot', it must have two free partition(one for '/boot', one for others),
#and make '/boot' the first partition in schema.
def handlePartitionSchemaForBoot(schema, diskprofile):
    for disk_index in schema['disk_dict'].keys():
        for pt_index, pt_info in schema['disk_dict'][disk_index]['partition_dict'].items():
            if (pt_info['mountpoint'] != '/boot'):
                continue

            #find '/boot' in partition schema, and get the Disk instance from DiskProfile
            disks_biosorder = diskprofile.getBIOSDiskOrder() or diskprofile.disk_dict.keys()
            disk = diskprofile.disk_dict[disks_biosorder[disk_index-1]]
            logger.debug('Check enough free partition for [boot] mountpoint on No.%d disk %s' % (disk_index, disks_biosorder[disk_index-1]))

            preserve_primary_num = 0
            for pt in disk.partition_dict.values():
                if pt.leave_unchanged and pt.type.strip().lower() == 'primary':
                    preserve_primary_num += 1
            if preserve_primary_num > 2:
                msg = "Can't create a primary partition for the [boot] mountpoint on disk %d." % (disk_index)
                msg += "The [boot] partition must be primary and cannot be a logical partition."
                raise InvalidPartitionSchema, msg

            #make '/boot' the first partition in schema
            new_partition_dict = schema['disk_dict'][disk_index]['partition_dict']
            sorted_pt_index = schema['disk_dict'][disk_index]['partition_dict'].keys()

            sorted_pt_index.sort()
            for idx in sorted_pt_index:
                if idx == pt_index:
                    break
                tmp_pt = new_partition_dict[idx]
                new_partition_dict[idx] = new_partition_dict[pt_index]
                new_partition_dict[pt_index] = tmp_pt

            logger.debug('new partition schema is %s' % new_partition_dict)
            return

def cleanDiskProfile(disk_profile):
    lv_list = disk_profile.lv_dict.values()

    for lv in lv_list:
        if not lv.leave_unchanged:
            disk_profile.delete(lv)

    for vg in disk_profile.lvg_dict.values():
        try:
            disk_profile.delete(vg)
        except CannotDeleteVolumeGroupError:
            logger.debug('VG: %s has PVs with leave unchanged' % vg.name)
        except PhysicalVolumeStillInUseError:
            logger.debug('VG: %s has LVs remaining.' % vg.name)
        except LogicalVolumeGroupStillInUseError,msg:
            logger.debug('VG: %s has LVs remaining. Message: %s' % (vg.name,
                         str(msg)))
        except Exception, e:
            logger.debug('Error: %s' % str(e))
      

    for disk in disk_profile.disk_dict.values():
        primary, extended, logical = getPartitionTuple(disk)

        # remove the logical partitions first.
        for partition in reversed(sorted(logical)):
            logger.debug('Checking if partition %s is preserved:', partition.path)
            if partition.leave_unchanged:
                logger.debug('Yes')
            else:
                logger.debug('No, deleting %s' % partition.path)
                try:
                    disk_profile.delete(partition, keep_in_place=True)
                except PartitionIsPartOfVolumeGroupError, e:
                    logger.debug(str(e))
                    f = sys._getframe()
                    logger.debug('Caller: %s' % (f.f_back.f_code.co_name))
                    raise e
                except KusuError, e:
                    logger.info(str(e))

        # then remove the extended partitions.
        if extended and disk.partition_dict.has_key(basename(extended.path)):
            logger.debug('Removing extended partition')
            try:
                disk_profile.delete(extended, keep_in_place=True)
            except CannotDeleteExtendedPartitionError, e:
                logger.info(str(e))
                f = sys._getframe()
                logger.debug('Caller: %s' % (f.f_back.f_code.co_name))

        # finally remove the primary partitions.
        for partition in reversed(sorted(primary)):
            logger.debug('Checking if partition %s is preserved:', partition.path)
            if partition.leave_unchanged:
                logger.debug('Yes')
            else:
                logger.debug('No, deleting %s' % partition.path)
                try:
                    disk_profile.delete(partition, keep_in_place=True)
                except PartitionIsPartOfVolumeGroupError, e:
                    logger.debug(str(e))
                    f = sys._getframe()
                    logger.debug('Caller: %s' % (f.f_back.f_code.co_name))
                    raise e
                except KusuError, e:
                    logger.info(str(e))

    disk_profile.executeLVMFifo()
    disk_profile.commit()

def isVG(rule):
    """Helper function to determine if partition database rule describes a VG."""
    return translatePartitionOptions(rule['options'], 'vg')[0]

def isLV(rule):
    """Helper function to determine if partition database rule describes a LV."""
    return translatePartitionOptions(rule['options'], 'lv')[0]

def getVGList(part_rules, diskprofile):
    vg_list = []
    for p in part_rules:
        if isVG(p):
            vg_name = p['device']
            vg_list.append(p)
    return vg_list

def getPartList(part_rules, diskprofile):
    """Get the list of partition entries that don't already exist."""
    part_list = []
    filtered_partrules = [p for p in part_rules if not isVG(p) and not isLV(p)]
    for p in filtered_partrules:
        dev = p['device']
        if dev.lower() == 'n':
            vg = translatePartitionOptions(p['options'], 'pv')[1]
            if vg not in diskprofile.lvg_dict.keys():
                part_list.append(p)
                logger.debug('Append to part_list: %s' % p)
        elif dev.isdigit():
            mountpoint = translateMntPnt(p['mntpnt'])
            if mountpoint not in diskprofile.mountpoint_dict.keys():
                part_list.append(p)
                logger.debug('Append to part_list: %s' % p)
    return part_list

def hasPVs(diskprofile):
    for disk in diskprofile.disk_dict.values():
        for p in disk.partition_dict.values():
            if p.lvm_flag:
                return True
    return False

def getLVList(part_rules, diskprofile):
    lv_list = []
    for p in part_rules:
        if isLV(p):
            lv_name = p['device']
            if lv_name not in diskprofile.lv_dict.keys():
                lv_list.append(p)
    return lv_list

    
def createSchema(part_rules, diskprofile):
    """ Adapt niipartition into a partitiontool schema. This schema can
        be passed along with a partitiontool diskprofile to setupDiskProfile
        method.

    """
    schema = {'disk_dict':{},'vg_dict':{}}

    # format for debug printing
    pp = PrettyPrinter(indent=2)
    vg_list = getVGList(part_rules, diskprofile)
    logger.debug('VG List after filtering:\n%s' % pp.pformat(vg_list))
    part_list = getPartList(part_rules, diskprofile)
#    schemaMatcher = SchemaMatcher(part_list, diskprofile)
    
#    part_layout = schemaMatcher.getPartitionLayout() 

    logger.debug('Partitions List after filtering:\n%s' % pp.pformat(part_list))
    lv_list = getLVList(part_rules, diskprofile)
    logger.debug('LV List after filtering:\n%s' % pp.pformat(lv_list))
    # create the volume groups first.
    try:
        for vginfo in vg_list:
            vgname = vginfo['device']
            vg_extent_size = translatePartitionOptions(vginfo['options'], 'vg')[1]
            schema['vg_dict'][vgname] = {'pv_list':[], 'lv_dict':{},
                                         'extent_size':vg_extent_size,
                                         'name':vgname}

        # create the normal volumes.
        for partinfo in part_list:
            fs = translateFSTypes(partinfo['fstype'])
            createPartition(partinfo, schema['disk_dict'], schema['vg_dict'])
            pv, vg_name = translatePartitionOptions(partinfo['options'], 'pv')
            if pv: handlePV(partinfo, vg_name, schema['vg_dict'])
        # renumber spanning partitions
        for disk in schema['disk_dict'].itervalues():
            part_dict = disk['partition_dict']
            if part_dict.has_key('N'):
                partition = part_dict['N']
                part_dict[len(part_dict)] = partition
                del part_dict['N']

        # create the logical volumes.
        for lvinfo in lv_list:
            lv, vg_name = translatePartitionOptions(lvinfo['options'],'lv')
            if lv: handleLV(lvinfo, vg_name, schema['vg_dict'])

        attachPVsToVGs(diskprofile, schema['vg_dict'])
        logger.debug('VG dict: %s' % str(schema['vg_dict']))

        preserve_types = Partition.native_type_dict.values() 
        preserve_fs = DiskProfile.fsType_dict.keys() 
        preserve_mntpnt = diskprofile.mountpoint_dict.keys()
        preserve_lv = [lv.name for lv in diskprofile.lv_dict.values()]
        schema['preserve_types'] = preserve_types
        schema['preserve_fs'] = preserve_fs
        schema['preserve_mntpnt'] = preserve_mntpnt
        schema['preserve_lv'] = preserve_lv

    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the lines."

    return schema

def attachPVsToVGs(disk_profile, vg_dict):
    for vg_name,vg in vg_dict.iteritems():
        logger.debug('VG Name: %s' % vg_name)
        pvs_with_vgs = [pv for pv in disk_profile.pv_dict.values() if pv.group]
        for pv in pvs_with_vgs:
            logger.debug('PV, group: %s' % str(pv.group.name))
            if pv.group and pv.group.name == vg_name:
                disk_no = getDiskNumber(pv.partition, disk_profile.disk_dict)
                part_no = pv.partition.num
                if not disk_no: continue
                vg['pv_list'].append({ disk: disk_no, partition: part_no })
                logger.debug('VG PV list: %s' % str(vg['pv_list']))

def getDiskNumber(partition, disk_dict):
    l = sorted(disk_dict.keys())
    for i in xrange(len(disk_dict)):
        k = l[i]
        disk = disk_dict[k]
        if partition.disk is disk:
            return i


def createPartition(partinfo, disk_dict, vg_dict):
    """ Create a new partition and add it to the supplied disk dictionary."""
    try:
        disknum = int(partinfo['device'])
        part_no = translatePartitionNumber(partinfo['partition'])
    except ValueError:
        if partinfo['device'].lower() == 'n':
            handleSpanningPartition(partinfo, disk_dict, vg_dict)
            disknum = 1
            part_no = 'N'
        else:
            logger.debug('Failed to translate disknum: %s, partition: %s' % (partinfo['device'], partinfo['partition']))
            raise InvalidPartitionSchema, "Couldn't translate the disknum/partition number."
    try:
        size = translatePartitionSize(partinfo['size'])
        fs = translateFSTypes(partinfo['fstype'])
        mountpoint = translateMntPnt(partinfo['mntpnt'])
        fill = translatePartitionOptions(partinfo['options'], 'fill')[0]
    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the Partition fields. " + \
                                      "disknum=%s, size=%s, fs=%s, mntpnt=%s, fill=%s, " + \
                                      "part_no=%s" % (partinfo['device'], partinfo['size'], \
                                      partinfo['fstype'], partinfo['mntpnt'], \
                                      partinfo['options'], partinfo['partition'])
 
    if part_no != 'N' and part_no <= 0:
        raise InvalidPartitionSchema, "Partition number cannot be less than 1."
    partition = {'size_MB': size, 'fill': fill,
                 'fs': fs, 'mountpoint': mountpoint}

    if disk_dict.has_key(disknum): disk = disk_dict[disknum]
    else: disk = {'partition_dict': {}}
    disk['partition_dict'][part_no] = partition
    disk_dict[disknum] = disk

def handleSpanningPartition(partinfo, disk_dict, vg_dict):
    is_pv, vg_name = translatePartitionOptions(partinfo['options'], 'pv')
    if not is_pv:
        raise InvalidPartitionSchema, "Partition marked as spanning multiple disks, but not as physical volumes."
    vg_dict[vg_name]['pv_span'] = True

def handlePV(partinfo, vg_name, vg_dict):
    if not vg_name.strip(): raise InvalidPartitionSchema, 'No Volume Group given for Physical Volume.'
    if vg_dict.has_key(vg_name): vg = vg_dict[vg_name]
    else: raise InvalidPartitionSchema, 'Physical Volume belongs to an unspecified Volume Group.'
    try:
        disknum = int(partinfo['device'])
        part_no = translatePartitionNumber(partinfo['partition'])
    except ValueError:
        if partinfo['device'].lower() == 'n':
            disknum = 'N'
            part_no = 'N'
        else:
            raise InvalidPartitionSchema, "Couldn't parse one of the LVM physical volume fields. " + \
                                          "disknum=%s, part_no=%s" % \
                                          (partinfo['device'], partinfo['partition'])

    vg['pv_list'].append({'disk': disknum, 'partition': part_no})

def handleLV(lvinfo, vg_name, vg_dict):
    vg_name = vg_name.strip()
    if not vg_name.strip(): raise InvalidPartitionSchema, 'No Volume Group given for Logical Volume.'
    if vg_dict.has_key(vg_name): vg = vg_dict[vg_name]
    else: raise InvalidPartitionSchema, 'Logical Volume %s belongs to non-existent Volume Group %s.' % \
                                        (lvinfo['device'], vg_name)
    try:
        name = lvinfo['device']
        size_MB = translatePartitionSize(lvinfo['size'])
        fill = translatePartitionOptions(lvinfo['options'], 'fill')[0]
        fs = translateFSTypes(lvinfo['fstype'])
        mountpoint = translateMntPnt(lvinfo['mntpnt'])
    except ValueError:
        raise InvalidPartitionSchema, "Couldn't parse one of the LVM logical volume fields."

    vg['lv_dict'][name] = {'size_MB': size_MB, 'fill': fill,
                           'fs': fs, 'mountpoint': mountpoint}
