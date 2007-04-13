#!/usr/bin/env python
# $Id: partition.py 248 2007-04-10 09:35:57Z ggoh $
#
# Kusu Text Installer Partition Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision: 248 $"

import logging
import snack
from gettext import gettext as _
from partition_new import *
from partition_edit import *
from partition_delete import *
from partitiontool import partitiontool
from ui.text import screenfactory, kusuwidgets
from ui.text.kusuwidgets import LEFT,CENTER,RIGHT

def printCurrent(ps):
    print ps.listbox.current()

class PartitionScreen(screenfactory.BaseScreen):
    """This screen asks for partition setups. This class is probably not the
       best class to look at if you're trying to understand the kusu-tui
       framework. It breaks some conventions(like error reporting and screen
       drawing) established by other classes in the kusu installer package.
    """
    name = _('Partitions')
    msg = _('Please enter the following information:')
    buttons = [_('New'), _('Edit'), _('Delete')]#, _('RAID')]
    disk_profile = partitiontool.DiskProfile(False)

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('New')].setCallback_(createNew, self)
        self.buttonsDict[_('Edit')].setCallback_(editDevice, self)
        self.buttonsDict[_('Delete')].setCallback_(deleteDevice, self)
#        self.buttonsDict[_('RAID')].setCallback_(self.raidPartition)


    def raidPartition(self):
        """Stub function"""

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 1)

        self.listbox = kusuwidgets.ColumnListbox(height=8, 
                                 colWidths=[15,6,6,8,9,12],
                                 colLabels=[_('Device'), _('Start'), _('End  '),
                                            _('Size(MB) '), _('Type  '),
                                            _('Mount Point   ')],
                                 justification=[LEFT, RIGHT, RIGHT,
                                                RIGHT, LEFT, LEFT],
                                 returnExit=0)

        # retrieve info about logical volumes and lv groups
        lvg_keys = self.disk_profile.lv_groups.keys()
        lvg_keys.sort()
        for key in lvg_keys:
            vg_devicename = 'VG ' + key
            vg_pv = self.disk_profile.lv_groups[key].physical_volume_ids
            vg_size = 0
            for pv in vg_pv:
                vg_size = vg_size + int(self.disk_profile.partitions[pv].size)
            # display volume groups first in listbox
            self.listbox.addRow(['VG ' + key, '', '', str(vg_size), 'VolGroup',
                                 ''], key)
            vg_lv = self.disk_profile.lv_groups[key].logical_volume_ids
            for lv in vg_lv:
                lv_devicename = '  LV ' + lv
                lv_size = self.disk_profile.logi_vol[lv].size
                lv_type = self.disk_profile.logi_vol[lv].fs_type
                lv_mount = self.disk_profile.logi_vol[lv].mountpoint
                # display indented logical volumes belonging to the vg.
                self.listbox.addRow([lv_devicename, '', '', str(lv_size),lv_type,
                                    lv_mount], lv)

        logging.debug('Partition screen: getting disk list')
        disk_keys = self.disk_profile.disk_dict.keys()
        disk_keys.sort()
        for key in disk_keys:
            # display device
            self.listbox.addRow(['/dev/'+key, '', '', '', '', ''], key)
            parts_dict = self.disk_profile.disk_dict[key].partitions_dict
            logging.debug('Disk %s has %d partitions as reported by parted.' % (key, \
                          self.disk_profile.disk_dict[key].pedDisk.get_last_partition_num()))
            for partition in sorted(parts_dict.itervalues()):
                part_devicename = '  ' + key + str(partition.num)
                # display partition info
                self.listbox.addRow([part_devicename,
                                    str(partition.start_cylinder),
                                    str(partition.end_cylinder),
                                    str(partition.size()/(1024*1024)),
                                    partition.fs_type,
                                    partition.mountpoint], partition)

        self.screenGrid.setField(self.listbox, col=0, row=0, anchorLeft=1,
                                 padding=(0,0,0,0))

        #self.listbox.setCallback_(printCurrent, self)

    def validate(self):
        errList = []

        if errList:
            errMsg = _('Please correct the following errors:')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
            return False, errMsg
        else:
            return True, ''

    def formAction(self):
        """
        
        Store to database
        
        """
        self.database.put(self.name, 'partition', 'tool')
        self.disk_profile.commit()
        self.kusuApp['DiskProfile'] = self.disk_profile

    def executeCallback(self, obj):
        if obj is self.listbox.listbox:
            return True
        return False

stored_mountpoint=''
def fileSystemCallback(args):
    global stored_mountpoint
    listbox, textEntry, diskProfile = args
    filesystem = listbox.current()
    fs_type = diskProfile.fsType_dict[filesystem]
    if textEntry.value() != '<Not Applicable>':
        stored_mountpoint = textEntry.value()
    if not fs_type:
        textEntry.setEntry('<Not Applicable>')
        textEntry.setEnabled(False)
    else:
        textEntry.setEntry(stored_mountpoint)
        textEntry.setEnabled(True)
