#!/usr/bin/env python
# $Id: partition_edit.py 1999 2009-01-29 07:56:46Z ggoh $
#
# Kusu Text Installer Edit Partition Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
import partition
from gettext import gettext as _
from partition_new import *
from os.path import basename
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from kusu.ui.text.navigator import NAV_NOTHING
from kusu.util.errors import KusuError
from primitive.system.hardware.errors import *

logger = kusulog.getKusuLog('installer.partition')

def editDevice(baseScreen):
    """Determine the type of device and bring up the appropriate screen."""
    screen = baseScreen.screen
    listbox = baseScreen.listbox
    disk_profile = baseScreen.disk_profile
    selected_device = listbox.current()

    logger.debug('Editing device')
    scr=None
    while True:
        try:
            if selected_device in disk_profile.lvg_dict.values():
                scr = EditVolumeGroup(screen, selected_device, disk_profile)
                scr.start()
            elif selected_device in disk_profile.lv_dict.values():
                logger.debug('Logical Volume Selected')
                scr = EditLogicalVolume(screen, selected_device, disk_profile)
                scr.start()
            elif selected_device in disk_profile.disk_dict.keys():
                raise KusuError, 'Cannot edit the selected device because it is a physical disk in the system.'
            elif hasattr(selected_device, 'type') and selected_device.type=='extended':
                raise KusuError, 'Extended partitions are managed by the Partitiontool and cannot be edited.'
            else:
                for disk in disk_profile.disk_dict.values():
                    if selected_device in disk.partition_dict.values():
                        checkPartOfActiveVolGroup(selected_device, disk_profile)
                        checkIfPreserved(selected_device)
                        scr = EditPartition(screen, selected_device, disk_profile)
                        scr.start()
  
            return NAV_NOTHING

        except (KusuError, PartitionException), e:
            msgbox = snack.GridForm(screen, 'Error', 1, 2)
            text = snack.TextboxReflowed(30, str(e))
            msgbox.add(text, 0, 0)
            msgbox.add(snack.Button('Ok'), 0, 1)
            msgbox.runPopup()
            return NAV_NOTHING
 
def checkIfPreserved(partition):
    if partition.leave_unchanged and partition.on_disk:
        raise KusuError, 'Partition %s cannot be edited because it has ' % \
                         partition.path + \
                         'been preserved from a previous installation.' 
 
def checkPartOfActiveVolGroup(partition, disk_profile):
    if partition.path in disk_profile.pv_dict.keys():
        pv = disk_profile.pv_dict[partition.path]
        if pv.group and pv.group.lv_dict:
            raise PartitionIsPartOfVolumeGroupError, 'Partition %s cannot ' % \
                (partition.path) + \
                'be edited because it is part of Logical Volume Group %s, ' % \
                (pv.group.name) + \
                'which still contains allocated logical volumes.\nDelete those first.'
 
class EditPartition:
    title = _('Edit Partition')

    def __init__(self, screen, partition, diskProfile):
        self.screen = screen
        self.partition = partition
        self.diskProfile = diskProfile
        self.gridForm = snack.GridForm(screen, self.title, 1, 7)

        self.mountpoint = kusuwidgets.LabelledEntry(_('Mount Point:'), 20,
                                                    text="", hidden=0,
                                                    password=0, scroll=0,
                                                    returnExit=0
                                                   )

        self.fixed_size = snack.SingleRadioButton('Fixed Size (MB):', None,
                                                  isOn=1)
        self.fixed_size_entry = snack.Entry(7)

        self.min_size = snack.SingleRadioButton('Fill at least (MB):',
                                                self.fixed_size)
        self.min_size_entry = snack.Entry(7)

        self.fill = snack.SingleRadioButton('Fill remaining space on disk.',
                                                self.min_size)


        self.do_not_format_partition = snack.Checkbox('Do not format partition')

        self.ok_button = kusuwidgets.Button(_('OK'))
        self.cancel_button = kusuwidgets.Button(_('Cancel'))

    def drawAvailableSpace(self):
        text = "Allocatable space (MB) - "
        availableSpace = 0
        for k,v in self.diskProfile.disk_dict.iteritems():
            available_space = v.getLargestSpaceAvailable() / 1024 / 1024
            text += '%s: %d ' % (k, available_space)
        avail_tb = snack.Label(text)
        return avail_tb

    def draw(self):
        """Draw the fields onscreen."""
        # mount point
        if self.diskProfile.mountable_fsType.has_key(self.partition.fs_type) and \
           self.diskProfile.mountable_fsType[self.partition.fs_type]:
            if not self.partition.mountpoint:
                mntpnt = ''
            else:
                mntpnt = self.partition.mountpoint
            self.mountpoint.setEntry(str(mntpnt))
        else:
            self.mountpoint.setEntry('<Not Applicable>')
            self.mountpoint.setEnabled(False)
    
        # file system
        if hasattr(self.partition, 'lvm_flag') and self.partition.lvm_flag:
            self.filesystem = snack.Label('Physical Volume')
        else:
            self.filesystem = snack.Label(str(self.partition.fs_type))

        # query drives
        self.drives = snack.Label('On %s' % self.partition.disk.path)

        self.gridForm.add(self.mountpoint, 0,0)

        # filesystems and drives
        subgrid = snack.Grid(2,1)
        subgrid.setField(self.filesystem, 0,0, padding=(0,0,2,0))
        subgrid.setField(self.drives, 1,0, padding=(2,0,0,0))
        self.gridForm.add(subgrid, 0,1)

        avail_tb = self.drawAvailableSpace() 
        self.gridForm.add(avail_tb, 0,2, anchorLeft=1, padding=(0,1,0,0))

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.fixed_size, 0,0)
        self.fixed_size_entry.set(str(self.partition.size_MB))
        subgrid.setField(self.fixed_size_entry, 1,0)
        self.gridForm.add(subgrid, 0,3, anchorLeft=1, padding=(0,1,0,0))

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.min_size, 0,0)
        subgrid.setField(self.min_size_entry, 1,0)
        self.gridForm.add(subgrid, 0,4, anchorLeft=1)

        subgrid = snack.Grid(1,1)
        subgrid.setField(self.fill, 0,0)
        self.gridForm.add(subgrid, 0,5, anchorLeft=1)

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.ok_button, 0,0)
        subgrid.setField(self.cancel_button, 1,0)
        self.gridForm.add(subgrid, 0,6)

        self.gridForm.draw()

    def start(self):
        self.draw()
        result = self.gridForm.run()
        if result is self.ok_button:
            self.processForm()
        self.screen.popWindow()
        return NAV_NOTHING

    def processForm(self):
        """Process the fields."""
        try:
            size_MB, fixed_size = self.calculatePartitionSize()
            if (fixed_size or self.min_size.selected()) and size_MB <= 0:
                raise KusuError, 'Please provide a positive integer partition size.'
        except ValueError: #catch potential conversion problem with wrong inputs
            raise KusuError,'Please provide a numeric minimum partition size'
        logger.debug('Fixed: %s Size: %d' % (fixed_size, size_MB))
        fs_type = self.partition.fs_type

        mountpoint = self.mountpoint.value()
        if mountpoint == '<Not Applicable>':
            mountpoint = None
        elif not mountpoint or mountpoint[0] != '/':
            raise KusuError, 'Please provide an absolute path for the mountpoint.'
        self.diskProfile.editPartition(self.partition, size_MB, fixed_size, fs_type, mountpoint)

    def calculatePartitionSize(self):
        """Calculate Partition size from the form's fields. Multiply by
           megabyte (1024 * 1024)"""
        if self.fixed_size.selected():
            value = long(self.fixed_size_entry.value())
            return (value, True)
        elif self.min_size.selected():
            value = long(self.min_size_entry.value())
            return (value, False)
        else:
            return (1, False)


class EditLogicalVolume(NewLogicalVolume):
    """Form for editing an existing logical volume."""
    title = _('Edit Logical Volume')

    def __init__(self, screen, device, disk_profile):
        NewLogicalVolume.__init__(self, screen, disk_profile)
        self.lv = device

    def draw(self):
        """Draw the fields onscreen."""
        # mount point
        if self.lv.mountpoint:
            self.mountpoint.setEntry(self.lv.mountpoint)
        else:
            self.mountpoint.setEntry('<Not Applicable>')
            self.mountpoint.setEnabled(False)
        self.gridForm.add(self.mountpoint, 0,0)
    
        # logical volume name
        self.lv_name.setEntry(self.lv.name)
        self.lv_name.setEnabled(False)
        self.gridForm.add(self.lv_name, 0,1)

        # size
        self.size.setEntry(str(self.lv.size_MB))
        self.gridForm.add(self.size, 0,2)

        fs_type = self.lv.fs_type or 'Unable to detect'
        self.filesystem = snack.Label('Filesystem: ' + fs_type)

        # query volume groups
        self.volumegroup = snack.Label('Volume Group: ' + self.lv.group.name)

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.filesystem, 0,0, padding=(0,0,2,0))
        subgrid.setField(self.volumegroup, 1,0, padding=(2,0,0,0))
        self.gridForm.add(subgrid, 0,3, padding=(0,1,0,1))

        text = "Available space (MB) - "
        available_space = 0
        for k,v in self.disk_profile.lvg_dict.iteritems():
            available_space = v.extentsFree() * v.extent_size / 1024 / 1024
            text += '%s: %d ' % (k, available_space)
        avail_tb = snack.Label(text)
        self.gridForm.add(avail_tb, 0,4, anchorLeft=1, padding=(0,1,0,0))


        self.gridForm.add(self.fill, 0,5, padding=(0,0,0,1))
        self.gridForm.add(self.do_not_format_partition, 0,6, padding=(0,0,0,1))

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.ok_button, 0,0)
        subgrid.setField(self.cancel_button, 1,0)
        self.gridForm.add(subgrid, 0,7)

        self.gridForm.draw()

        logger.debug('Finish populating LV screen')

    def processForm(self):
        """Process the fields."""
        retVal = True
        fs_type = self.lv.fs_type
        if fs_type in self.disk_profile.mountable_fsType.keys() and \
           self.disk_profile.mountable_fsType[fs_type] is True:
           mountpoint = self.mountpoint.value()
           if not mountpoint or mountpoint[0] != '/':
               raise KusuError, 'Please provide an absolute path for the mountpoint.'
        else:
            mountpoint = None

        vol_grp = self.lv.group
        try:

            available_space = vol_grp.extentsFree() * vol_grp.extent_size / 1024 / 1024
            self_size_MB = self.lv.size / 1024 /1024
            available_space += self_size_MB

            if self.fill.value():
                size_MB = available_space
            else:
                size_MB = long(self.size.value())
            if size_MB <= 0 or size_MB > available_space and not self.fill.value():
                raise KusuError, 'Size must be between 1 and %d MB.' % available_space
            
        except ValueError:
            raise KusuError, 'Please provide a numeric size'

        logger.debug('Edit LV - size: %s fs: %s mntpnt: %s' % (str(size_MB), str(fs_type), str(mountpoint)))
        self.disk_profile.editLogicalVolume(self.lv, size_MB, self.lv.fs_type, mountpoint)


        self.lv.do_not_format = self.do_not_format_partition.value()
        return retVal 


class EditVolumeGroup(NewVolumeGroup):
    """Form for editing an existing logical volume group."""
    title = _('Modify Logical Volume Group')

    def __init__(self, screen, device, disk_profile):
        NewVolumeGroup.__init__(self, screen, disk_profile)
        self.phys_to_use_lbl = snack.Label('Physical Volumes to Add:')
        self.lvg = device

    def draw(self):
        """Draw the fields onscreen."""
        NewVolumeGroup.draw(self)

        logger.debug('Populate LVG screen')
        self.vg_name.setEntry(self.lvg.name)
        self.vg_name.setEnabled(False)
        pv_list = self.lvg.pv_dict.keys()
        for pv_key in sorted(pv_list):
            pv = self.lvg.pv_dict[pv_key]
            self.phys_to_use.append(pv_key, pv, 1)


    def processForm(self):
        """Process the fields."""
        phys_vols = self.phys_to_use.getSelection()
        
        self.disk_profile.editLogicalVolumeGroup(self.lvg, phys_vols)
