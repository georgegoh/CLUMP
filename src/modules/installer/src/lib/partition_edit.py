#!/usr/bin/env python
# $Id: partition_edit.py 237 2007-04-05 08:57:10Z ggoh $
#
# Kusu Text Installer Edit Partition Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision: 237 $"

#import logging
import snack
import partition
from gettext import gettext as _
from partition_new import *
from kusu.partitiontool import partitiontool
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT

NAV_NOTHING = -1

def editDevice(baseScreen):
    """Determine the type of device and bring up the appropriate screen."""
    screen = baseScreen.screen
    listbox = baseScreen.listbox

    selected_device = listbox.current()

    scr=None
    while True:
        try:
            if selected_device in partitiontool.lv_groups.keys():
                scr = EditVolumeGroup(screen, selected_device)
                scr.start()
            elif selected_device in partitiontool.logi_vol.keys():
                scr = EditLogicalVolume(screen, selected_device)
                scr.start()
            elif selected_device in partitiontool.disks.keys():
                print 'Disk'
            elif selected_device in partitiontool.partitions.keys():
                scr = EditPartition(screen, selected_device)
                scr.start()

            return NAV_NOTHING

        except partitiontool.KusuError, e:
            msgbox = snack.GridForm(screen, 'Error', 1, 2)
            text = snack.TextboxReflowed(30, str(e))
            msgbox.add(text, 0, 0)
            msgbox.add(snack.Button('Ok'), 0, 1)
            msgbox.runPopup()


class EditPartition(NewPartition):
    """Form for editing an existing partition."""
    title = _('Edit Partition')

    def __init__(self, screen, device):
        NewPartition.__init__(self, screen)
        self.partition_id = device
        self.part_info = partitiontool.partitions[device]

    def draw(self):
        """Draw the fields onscreen."""
        NewPartition.draw(self)

        self.mountpoint.setEntry(self.part_info.mountpoint)
        self.filesystem.setCurrent(self.part_info.fs_type)

        # find parent drive
        self.drives.setCurrent(self.part_info.disk_id)

        # set fixed size
        self.fixed_size_entry.set(str(self.part_info.size))

    def processForm(self):
        """Process the fields."""
        fs_type = self.filesystem.current()
        if partitiontool.filesystem_types[fs_type].mountable:
            mountpoint = self.mountpoint.value()
        else:
            mountpoint = ''
        disk = self.drives.current()
        size, fixed = self.calculatePartitionSize(disk)
        partitiontool.editPartition(self.partition_id, size, fixed_size,
                                    fs_type, mountpoint)


class EditLogicalVolume(NewLogicalVolume):
    """Form for editing an existing logical volume."""
    title = _('Edit Logical Volume')

    def __init__(self, screen, device):
        NewLogicalVolume.__init__(self, screen)
        self.logical_vol = device
        self.lv_info = partitiontool.logi_vol[device]
        self.lv_group = self.lv_info.vol_group

    def draw(self):
        """Draw the fields onscreen."""
        NewLogicalVolume.draw(self)

        self.mountpoint.setEntry(self.lv_info.mountpoint)
        self.lv_name.setEntry(self.logical_vol)
        self.size.setEntry(str(self.lv_info.size))
        self.filesystem.setCurrent(self.lv_info.fs_type)
        self.volumegroup.setCurrent(self.lv_info.vol_group)

    def processForm(self):
        """Process the fields."""
        fs_type = self.filesystem.current()
        if partitiontool.filesystem_types[fs_type].mountable:
            mountpoint = self.mountpoint.value()
        else:
            mountpoint = ''
        vol_grp = self.volumegroup.current()

        size = self.size.value()

        new_lv_name = self.lv_name.value()

        partitiontool.editLogicalVolume(self.logical_vol, new_lv_name,
                                        vol_grp, size, fs_type, mountpoint)


class EditVolumeGroup(NewVolumeGroup):
    """Form for editing an existing logical volume group."""
    title = _('Modify Logical Volume Group')
    def __init__(self, screen, device):
        NewVolumeGroup.__init__(self, screen)
        self.vol_grp = device
        self.vg_info = partitiontool.lv_groups[device]

    def draw(self):
        """Draw the fields onscreen."""
        self.vg_name.setEntry(self.vol_grp)
        self.phys_extent.setEntry(str(self.vg_info.physical_extent))
        self.phys_extent.setEnabled(False)
        for phys_vol in self.vg_info.physical_volume_ids:
            self.phys_to_use.append(phys_vol, phys_vol, 1)

        NewVolumeGroup.draw(self)

    def processForm(self):
        """Process the fields."""
        vol_grp_name = self.vg_name.value()
        phys_extent = self.phys_extent.value()
        phys_vols = self.phys_to_use.getSelection()
        
        partitiontool.editLogicalVolumeGroup(self.vol_grp, vol_grp_name, phys_vols)
