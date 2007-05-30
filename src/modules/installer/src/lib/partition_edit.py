#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Edit Partition Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
import partition
from gettext import gettext as _
from partition_new import *
from os.path import basename
from kusu.partitiontool import partitiontool
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog

logger = kusulog.getKusuLog('installer.partition')

NAV_NOTHING = -1

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
                raise partitiontool.KusuError, 'Cannot delete the selected device because it is a physical disk in the system.'
            else:
                for disk in disk_profile.disk_dict.values():
                    if selected_device in disk.partition_dict.values():
                        scr = EditPartition(screen, selected_device, disk_profile)
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

    def __init__(self, screen, device, disk_profile):
        NewPartition.__init__(self, screen, disk_profile)
        self.partition = device

    def draw(self):
        """Draw the fields onscreen."""
        NewPartition.draw(self)

        mountpoint = ''
        if self.partition.mountpoint: mountpoint = self.partition.mountpoint
        self.mountpoint.setEntry(mountpoint)
        if self.partition.fs_type in self.diskProfile.fsType_dict.keys():
            self.filesystem.setCurrent(self.partition.fs_type)

        # find parent drive
        self.drives.setCurrent(basename(self.partition.disk.path))

        # set fixed size
        size_MB = self.partition.size / 1024 /1024
        self.fixed_size_entry.set(str(size_MB))

    def processForm(self):
        """Process the fields."""
        fs_type = self.filesystem.current()
        if fs_type in self.diskProfile.mountable_fsType.keys() and \
           self.diskProfile.mountable_fsType[fs_type] is True:
            mountpoint = self.mountpoint.value()
        else:
            mountpoint = ''
        disk = self.drives.current()
        size_MB, fixed = self.calculatePartitionSize(disk)
        self.diskProfile.editPartition(self.partition, size_MB, fixed,
                                       fs_type, mountpoint)


class EditLogicalVolume(NewLogicalVolume):
    """Form for editing an existing logical volume."""
    title = _('Edit Logical Volume')

    def __init__(self, screen, device, disk_profile):
        NewLogicalVolume.__init__(self, screen, disk_profile)
        self.lv = device

    def draw(self):
        """Draw the fields onscreen."""
        NewLogicalVolume.draw(self)

        logger.debug('Populate LV screen')

        mountpoint = ''
        if self.lv.mountpoint: mountpoint = self.lv.mountpoint
        self.mountpoint.setEntry(mountpoint)
        self.lv_name.setEntry(self.lv.name)
        self.lv_name.setEnabled(False)
        size_MB = self.lv.size / 1024 / 1024
        self.size.setEntry(str(size_MB))
        if self.lv.fs_type in self.disk_profile.fsType_dict.keys():
            self.filesystem.setCurrent(self.lv.fs_type)
        self.volumegroup.clear()
        self.volumegroup.addRow([self.lv.group.name], self.lv.group)

        logger.debug('Finish populating LV screen')

    def processForm(self):
        """Process the fields."""
        fs_type = self.filesystem.current()
        if fs_type in self.disk_profile.mountable_fsType.keys() and \
           self.disk_profile.mountable_fsType[fs_type] is True:
            mountpoint = self.mountpoint.value()
        else:
            mountpoint = ''
        size = self.size.value()
        self.disk_profile.editLogicalVolume(self.lv, size, fs_type, mountpoint)

        if not self.format_partition.value():
            self.lv.do_not_format = True


class EditVolumeGroup(NewVolumeGroup):
    """Form for editing an existing logical volume group."""
    title = _('Modify Logical Volume Group')

    def __init__(self, screen, device, disk_profile):
        NewVolumeGroup.__init__(self, screen, disk_profile)
        self.lvg = device

    def draw(self):
        """Draw the fields onscreen."""
        NewVolumeGroup.draw(self)

        logger.debug('Populate LVG screen')

        self.vg_name.setEnabled(False)
        self.vg_name.setEntry(self.lvg.name)
        self.phys_extent.setEntry(self.lvg.extent_size_humanreadable[:-1])
        self.phys_extent.setEnabled(False)
        pv_list = self.lvg.pv_dict.keys()
        for pv_key in sorted(pv_list):
            pv = self.lvg.pv_dict[pv_key]
            self.phys_to_use.append(pv_key, pv, 1)


    def processForm(self):
        """Process the fields."""
        phys_vols = self.phys_to_use.getSelection()
        
        self.disk_profile.editLogicalVolumeGroup(self.lvg, phys_vols)
