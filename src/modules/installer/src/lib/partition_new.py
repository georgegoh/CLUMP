#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer New Partition Setup Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
import partition
from gettext import gettext as _
import kusu.partitiontool
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
from kusu.ui.text.navigator import NAV_NOTHING
from kusu.util.errors import *
import kusu.util.log as kusulog
logger = kusulog.getKusuLog('installer.partition')

def createNew(baseScreen):
    """Ask if user wants to create a new partition, logical volume, or volume
       group.
    """
    screen = baseScreen.screen
    diskProfile = baseScreen.disk_profile
    gridForm = snack.GridForm(screen, _('Select type of device'),1,3)

    tb = snack.TextboxReflowed(30, 
         _('Please select what you would like to create:'))
    gridForm.add(tb, 0,0)

    choice = snack.Listbox(4, returnExit=1)
    choice.append('partition', 'partition')
    if diskProfile.pv_dict:
        choice.append('volume group', 'volume group')
    if diskProfile.lvg_dict:
        choice.append('logical volume', 'logical volume')
#    choice.append('RAID device','RAID device')
    gridForm.add(choice, 0,1, padding=(0,1,0,1))

    ok_button = kusuwidgets.Button(_('OK'))
    cancel_button = kusuwidgets.Button(_('Cancel'))
    subgrid = snack.Grid(2,1)
    subgrid.setField(ok_button, 0,0)
    subgrid.setField(cancel_button, 1,0)
    gridForm.add(subgrid, 0,2)

    gridForm.draw()
    exitCmd = gridForm.run()
    screen.popWindow()
    if exitCmd is cancel_button:
        return NAV_NOTHING

    scr=None
    while True:
        try:
            if choice.current() == 'partition':
                scr = NewPartition(screen, diskProfile)
                scr.start()
            elif choice.current() == 'logical volume':
                scr = NewLogicalVolume(screen, diskProfile)
                scr.start()
            elif choice.current() == 'volume group':
                scr = NewVolumeGroup(screen, diskProfile)
                scr.start()
            elif choice.current() == 'RAID device':
                scr = NewRAIDDevice(screen, diskProfile)
                scr.start()

            return NAV_NOTHING

        except KusuError, e:
            msgbox = snack.GridForm(screen, 'Error', 1, 2)
            text = snack.TextboxReflowed(30, str(e))
            msgbox.add(text, 0, 0)
            msgbox.add(snack.Button('Ok'), 0, 1)
            msgbox.runPopup()


class NewPartition:
    """Form for specifying a new partition."""
    title = _('Add Partition')

    def __init__(self, screen, diskProfile):
        self.screen = screen
        self.diskProfile = diskProfile
        self.gridForm = snack.GridForm(screen, self.title, 1, 8)

        self.mountpoint = kusuwidgets.LabelledEntry(_('Mount Point:'), 20,
                                                    text="", hidden=0,
                                                    password=0, scroll=0,
                                                    returnExit=0
                                                   )

        self.filesystem = kusuwidgets.ColumnListbox(2, colWidths=[20], 
                                                colLabels=['File System type:'],
                                                    justification=[LEFT],
                                                    returnExit=0)

        self.drives = kusuwidgets.ColumnListbox(2, colWidths=[20],
                                                colLabels=['Allowable Drives:'],
                                                justification=[LEFT],
                                                returnExit=0)

        self.fixed_size = snack.SingleRadioButton('Fixed Size (MB):', None,
                                                  isOn=1)
        self.fixed_size_entry = snack.Entry(7)

        self.min_size = snack.SingleRadioButton('Fill at least (MB):',
                                                self.fixed_size)
        self.min_size_entry = snack.Entry(7)

        self.fill = snack.SingleRadioButton('Fill remaining space on disk.',
                                                self.min_size)


#        self.primary_partition=snack.Checkbox('Force to be a primary partition')
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
        self.gridForm.add(self.mountpoint, 0,0, padding=(0,0,0,1))

        # query filesystems
        for fs in ['ext2', 'ext3', 'linux-swap', 'physical volume']:
            self.filesystem.addRow([fs], fs)

        self.filesystem.setCallback_(partition.fileSystemCallback,
                                     (self.filesystem, self.mountpoint, self.diskProfile))
        # query drives
        disks = self.diskProfile.disk_dict.keys()
        for disk in disks:
            self.drives.addRow([disk], disk)

        # filesystems and drives
        subgrid = snack.Grid(2,1)
        subgrid.setField(self.filesystem, 0,0, padding=(0,0,2,0))
        subgrid.setField(self.drives, 1,0, padding=(2,0,0,0))
        self.gridForm.add(subgrid, 0,1)

        avail_tb = self.drawAvailableSpace() 
        self.gridForm.add(avail_tb, 0,2, anchorLeft=1, padding=(0,1,0,0))

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.fixed_size, 0,0)
        subgrid.setField(self.fixed_size_entry, 1,0)
        self.gridForm.add(subgrid, 0,3, anchorLeft=1, padding=(0,1,0,0))

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.min_size, 0,0)
        subgrid.setField(self.min_size_entry, 1,0)
        self.gridForm.add(subgrid, 0,4, anchorLeft=1)

        subgrid = snack.Grid(1,1)
        subgrid.setField(self.fill, 0,0)
        self.gridForm.add(subgrid, 0,5, anchorLeft=1)

        self.gridForm.add(self.do_not_format_partition, 0,6, padding=(0,1,0,1))

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.ok_button, 0,0)
        subgrid.setField(self.cancel_button, 1,0)
        self.gridForm.add(subgrid, 0,7)
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
        fs_type = self.filesystem.current()
        if fs_type in self.diskProfile.mountable_fsType.keys() and \
           self.diskProfile.mountable_fsType[fs_type]:
            mountpoint = self.mountpoint.value()
            if not mountpoint or mountpoint[0] != '/':
                raise KusuError, 'Please provide an absolute path for the mountpoint.'
        else:
            mountpoint = None
        disk = self.drives.current()
        try:
            size_MB, fixed_size = self.calculatePartitionSize()
            if (fixed_size or self.min_size.selected()) and  size_MB <= 0:
                raise KusuError, 'Please provide a positive integer partition size.'
        except ValueError: #catch potential conversion problem with wrong inputs
            raise KusuError,'Please provide a numeric minimum partition size'
        logger.debug('Fixed: %s Size: %d' % (fixed_size, size_MB))
        fill = self.min_size.selected() or self.fill.selected()
        logger.debug('Fill value: %s' % fill)
        p = self.diskProfile.newPartition(disk, size_MB, fixed_size, fs_type, mountpoint, fill)
        p.do_not_format = self.do_not_format_partition.value()

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


class NewLogicalVolume:
    """Form for specifying a new logical volume."""
    title = _('Make Logical Volume')

    def __init__(self, screen, disk_profile):
        self.screen = screen
        self.disk_profile = disk_profile
        self.gridForm = snack.GridForm(screen, self.title, 1, 8)

        self.mountpoint = kusuwidgets.LabelledEntry(_('Mount Point:').rjust(20),
                                                    20, text="", hidden=0,
                                                    password=0, scroll=0,
                                                    returnExit=0
                                                   )
        self.lv_name = kusuwidgets.LabelledEntry(
                                        _('Logical Volume Name:').rjust(20),
                                        20, text="", hidden=0, password=0,
                                        scroll=0, returnExit=0
                                   )
        self.lv_name.addCheck(LVMNameCheck)
        self.size = kusuwidgets.LabelledEntry(_('Size (MB):').rjust(20), 20,
                                              text="", hidden=0, password=0,
                                              scroll=0, returnExit=0
                                             )
        self.filesystem = kusuwidgets.ColumnListbox(2, colWidths=[20], 
                                                colLabels=['File System type:'],
                                                justification=[LEFT],
                                                returnExit=0)
        self.volumegroup = kusuwidgets.ColumnListbox(2, colWidths=[20],
                                                    colLabels=['Volume Group:'],
                                                    justification=[LEFT])

        self.fill = snack.Checkbox('Fill remaining space on disk.')
        self.do_not_format_partition = snack.Checkbox('Do not format partition')
        self.ok_button = kusuwidgets.Button(_('OK'))
        self.cancel_button = kusuwidgets.Button(_('Cancel'))

    def draw(self): 
        """Draw the fields onscreen."""
        # mount point
        self.gridForm.add(self.mountpoint, 0,0)
    
        # logical volume name        
        self.gridForm.add(self.lv_name, 0,1)

        # size
        self.gridForm.add(self.size, 0,2)

        # query filesystems
        for fs in ['ext2', 'ext3', 'linux-swap']:
            self.filesystem.addRow([fs], fs)

        self.filesystem.setCallback_(partition.fileSystemCallback,
                                     (self.filesystem, self.mountpoint, self.disk_profile))

        # query volume groups
        for vg_key in sorted(self.disk_profile.lvg_dict.keys()):
            self.volumegroup.addRow([vg_key], self.disk_profile.lvg_dict[vg_key])

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

    def start(self):
        self.draw()
        result = self.gridForm.run()
        if result is self.ok_button:
            self.processForm()
        self.screen.popWindow()
        return NAV_NOTHING

    def processForm(self):
        """Process the fields."""
        verified, msg = self.lv_name.verify()
        if not verified:
            if msg:
                raise KusuError, msg
            else:
                # we can fail in verify() before the callback is fired - no input entered
                raise KusuError, 'Please enter a name for the Logical Volume.'
        fs_type = self.filesystem.current()
        if fs_type in self.disk_profile.mountable_fsType.keys() and \
           self.disk_profile.mountable_fsType[fs_type]:
            mountpoint = self.mountpoint.value()
            if not mountpoint or mountpoint[0] != '/':
                raise KusuError, 'Please provide an absolute path for the mountpoint.'
        else:
            mountpoint = None

        vol_grp = self.volumegroup.current()
        try:
            if not self.fill.value():
                size = long(self.size.value())
            else:
                size = 1  #dummy
            available_space = vol_grp.extentsFree() * vol_grp.extent_size / 1024 / 1024
            if available_space == 0:
                errMsg = 'Selected volume group %s does not have any ' % vol_grp.name
                errMsg += 'free space left. Please select another volume group '
                errMsg += 'with sufficient free space.'
                raise KusuError, errMsg
            if not self.fill.value() and (size <= 0 or size > available_space):
                raise KusuError, 'Size must be between 1 and %d MB.' % available_space
        except ValueError:
            raise KusuError, 'Please provide a numeric size'
        new_lv_name = self.lv_name.value()
        if self.fill.value():
           lv = self.disk_profile.newLogicalVolume(name=new_lv_name,
                                                   lvg=vol_grp,
                                                   size_MB=size,
                                                   fs_type=fs_type,
                                                   mountpoint=mountpoint,
                                                   fill=True)
        else:
            lv = self.disk_profile.newLogicalVolume(name=new_lv_name,
                                                    lvg=vol_grp,
                                                    size_MB=size,
                                                    fs_type=fs_type,
                                                    mountpoint=mountpoint)

        lv.do_not_format = self.do_not_format_partition.value() 


class NewVolumeGroup:
    """Form for specifying a new logical volume group."""
    title = _('Make Logical Volume Group')

    def __init__(self, screen, disk_profile):
        self.screen = screen
        self.disk_profile = disk_profile
        self.gridForm = snack.GridForm(screen, self.title, 1, 4)

        self.vg_name = kusuwidgets.LabelledEntry(
                                       _('Volume Group Name:').rjust(21),
                                       21, text="", hidden=0, password=0,
                                       scroll=0, returnExit=0
                                   )
        self.vg_name.addCheck(LVMNameCheck)
        self.phys_to_use_lbl = snack.Label('Physical Volumes to Use:')
        self.phys_to_use = snack.CheckboxTree(height=3, scroll=1)
        self.ok_button = kusuwidgets.Button(_('OK'))
        self.cancel_button = kusuwidgets.Button(_('Cancel'))

    def draw(self):
        """Draw the fields onscreen."""
        # volume group name
        self.gridForm.add(self.vg_name, 0,0)
        # physical volume to use
        self.gridForm.add(self.phys_to_use_lbl, 0,1)

        # list of available physical volumes
        pv_list = self.disk_profile.pv_dict.keys()
        for pv_key in sorted(pv_list):
            pv = self.disk_profile.pv_dict[pv_key]
            if pv.group is None:
                self.phys_to_use.append(pv_key, pv)
        self.gridForm.add(self.phys_to_use, 0,2)

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.ok_button, 0,0)
        subgrid.setField(self.cancel_button, 1,0)
        self.gridForm.add(subgrid, 0,3)
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
        verified, msg = self.vg_name.verify()
        if not verified:
            if msg:
                raise KusuError, msg
            else:
                # we can fail in verify() before the callback is fired - no input entered
                raise KusuError,'Please enter a name for the Logical Volume Group.'
        vol_grp_name = self.vg_name.value()
        phys_extent = '32M' 
        phys_vols = self.phys_to_use.getSelection()

        self.disk_profile.newLogicalVolumeGroup(vol_grp_name,
                                                phys_extent,
                                                phys_vols)

import re
def LVMNameCheck(input):
    """Verifies that the input string is a valid LVM name."""
    p = re.compile('[^a-zA-Z0-9]')
    li = p.findall(input)
    if li:
        return False, 'Valid LVM names contain only letters and numbers.'
    return True, None

class NewRAIDDevice:
    """Form for specifying a new RAID device."""
    title = _('Make RAID device')

    def __init__(self, screen, diskProfile):
        self.screen = screen
        self.diskProfile = diskProfile
        self.gridForm = snack.GridForm(screen, self.title, 1, 4)

        self.mountpoint = kusuwidgets.LabelledEntry(_('Mount Point:'), 20,
                                                    text="", hidden=0,
                                                    password=0, scroll=0,
                                                    returnExit=0
                                                   )

        self.filesystem = kusuwidgets.ColumnListbox(2, colWidths=[20], 
                                                colLabels=['File System type:'],
                                                    justification=[LEFT],
                                                    returnExit=0)

        self.raid_level = kusuwidgets.ColumnListbox(2, colWidths=[20],
                                                colLabels=['RAID Level:'],
                                                justification=[LEFT],
                                                returnExit=0)

        self.raid_members_lbl = snack.Label('RAID Members:')
        self.raid_members = snack.CheckboxTree(height=3, scroll=1)

        self.spares = kusuwidgets.LabelledEntry(_('Number of spares:'), 3,
                                                    text="", hidden=0,
                                                    password=0, scroll=0,
                                                    returnExit=0
                                                   )

        self.format=snack.Checkbox('Format partition')

        self.ok_button = kusuwidgets.Button(_('OK'))
        self.cancel_button = kusuwidgets.Button(_('Cancel'))

    def draw(self):
        """Draw the fields onscreen."""
        # mount point
        self.gridForm.add(self.mountpoint, 0,0, padding=(0,0,0,1))

        # query filesystems
        fs_types = partitiontool.filesystem_types.keys()
        fs_types.sort()
        for fs in fs_types:
            self.filesystem.addRow([fs], fs)

        self.filesystem.setCallback_(partition.fileSystemCallback,
                                     (self.filesystem, self.mountpoint))

        # get available raid levels
        for raid_lvl in partitiontool.raid_lvls_supported:
            self.raid_level.addRow([raid_lvl], raid_lvl)

        # filesystems and drives
        subgrid = snack.Grid(2,1)
        subgrid.setField(self.filesystem, 0,0, padding=(0,0,2,1))
        subgrid.setField(self.raid_level, 1,0, padding=(2,0,0,1))
        self.gridForm.add(subgrid, 0,1)

        # get RAID partitions
        for part_id, part in partitiontool.partitions.iteritems():
            if part.fs_type == 'software RAID':
                self.raid_members.append(part_id, part_id)

        subgrid = snack.Grid(2,1)
        subgrid2 = snack.Grid(1,2)
        subgrid2.setField(self.raid_members_lbl, 0,0)
        subgrid2.setField(self.raid_members, 0,1)
        subgrid.setField(subgrid2, 0,0, padding=(0,0,2,1))

        subgrid2 = snack.Grid(1,2)
        subgrid2.setField(self.spares, 0,0, padding=(0,0,0,1))
        subgrid2.setField(self.format, 0,1)

        subgrid.setField(subgrid2, 1,0, padding=(2,0,0,0))
        self.gridForm.add(subgrid, 0,2)

        subgrid = snack.Grid(2,1)
        subgrid.setField(self.ok_button, 0,0)
        subgrid.setField(self.cancel_button, 1,0)
        self.gridForm.add(subgrid, 0,3)

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

