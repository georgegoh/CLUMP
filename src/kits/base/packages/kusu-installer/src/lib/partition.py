#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Partition Setup Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
from gettext import gettext as _
from partition_new import *
from partition_edit import *
from partition_delete import *
from defaults import *
from kusu.partitiontool import partitiontool
from kusu.ui.text import kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
from kusu.util.errors import *
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_NOTHING
from kusu.util.testing import runCommand
import kusu.util.log as kusulog
logger = kusulog.getKusuLog('installer.partition')

class PartitionScreen(InstallerScreen):
    """This screen asks for partition setups. This class is probably not the
       best class to look at if you're trying to understand the kusu-tui
       framework. It breaks some conventions(like error reporting and screen
       drawing) established by other classes in the kusu installer package.
    """
    name = _('Partitions')
    profile = 'Partitions'
    msg = _('Please enter the following information:')
    buttons = [_('New'), _('Edit'), _('Delete')]#, _('RAID')]
    disk_profile = None

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('New')].setCallback_(createNew, self)
        self.buttonsDict[_('Edit')].setCallback_(editDevice, self)
        self.buttonsDict[_('Delete')].setCallback_(deleteDevice, self)
#        self.buttonsDict[_('RAID')].setCallback_(self.raidPartition)

    def setHotKeys(self):
        self.hotkeysDict = {'F5': self.displayInternalState, 'F6' : self.saveInternalStateToFile }

    def displayInternalState(self):
        s = str(self.disk_profile) + '\n\n'
        s = s + 'LVM Fifo:\n'
        s = s + self.disk_profile.reprLVMFifo()
        self.selector.popupMsg('Internal Partitiontool State', s)
        return NAV_NOTHING

    def saveInternalStateToFile(self):
        result, values = self.selector.popupEntry('Save Partition Tool Dump To File',
                                 'Enter the location of the file where ' + \
                                 'you would like to save the dump of partitiontool',
                                 ['Location'], width=40)
        if result:
            try:
                location = values[0]
                s = str(self.disk_profile) + '\n\n'
                s = s + 'LVM Fifo:\n'
                s = s + self.disk_profile.reprLVMFifo()
                f = open(location, 'w')
                f.write(s)
            finally:
                f.close()
        return NAV_NOTHING

    def raidPartition(self):
        """Stub function"""

    def drawImpl(self):
        prog_dlg = self.selector.popupProgress('Scanning System', 'Scanning System disks...')
        self.screenGrid = snack.Grid(1, 1)

        self.listbox = kusuwidgets.ColumnListbox(height=8, 
                                 colWidths=[16,8,14,14],
                                 colLabels=[_('Device'),
                                            _('Size(MB) '), _('Type  '),
                                            _('Mount Point   ')],
                                 justification=[LEFT,
                                                RIGHT, LEFT, LEFT],
                                 returnExit=0)

        self.lvm_inconsistent = False
        if not self.disk_profile:
            try_again = True
            while try_again:
                try:
                    self.lvm_inconsistent = False
                    self.disk_profile = partitiontool.DiskProfile(fresh=False, probe_fstab=True, ignore_errors=False)
                    self.prompt_for_default_schema = True
                    try_again = False
                except LVMInconsistencyError, e:
                    self.lvm_inconsistent = True
                    errMsg = 'An LVM inconsistency has occurred that the installer may not '
                    errMsg += 'be able to recover from. Press Ctrl-Alt-F2 to access the command '
                    errMsg += 'prompt to fix this, and press Ctrl-Alt-F1 to return to the screen '
                    errMsg += "when you're done.(Recommended)\n"
                    errMsg += 'Alternatively, you may choose to ignore this message, and Kusu '
                    errMsg += 'will try to install anyway.'
                    errMsg += 'The specific trace from the command that raised this error is '
                    errMsg += 'shown below.\n\n'
                    errMsg += str(e)
                    retVal = self.selector.popupDialogBox('LVM Inconsistency', errMsg,
                                                          ['Retry Detection', 'Ignore', 'Reboot'])
                    if str(retVal) == 'retry detection':
                        try_again = True
                    elif str(retVal) == 'ignore':
                        self.disk_profile = partitiontool.DiskProfile(fresh=False, probe_fstab=True)
                        self.prompt_for_default_schema=True
                        try_again = False
                    else:
                        raise UserExitError, 'Rebooting on user request.'
                except Exception, e:
                    err_msg = 'An error occurred while scanning the disks in the system. '
                    err_msg += 'Kusu installer will try to proceed, but will wipe out any '
                    err_msg += 'existing data on the disks. If you wish to continue, press '
                    err_msg += '"OK". Otherwise, please poweroff the machine now.'
                    self.selector.popupMsg('Disk Probe Error', err_msg)
                    self.disk_profile = partitiontool.DiskProfile(fresh=True, probe_fstab=False)
                    self.prompt_for_default_schema = True
                    try_again = False


        if self.prompt_for_default_schema:
            self.promptForDefaultSchema()
            self.prompt_for_default_schema = False

        # retrieve info about logical volumes and lv groups
        lvg_keys = self.disk_profile.lvg_dict.keys()
        for key in sorted(lvg_keys):
            lvg = self.disk_profile.lvg_dict[key]
            lvg_displayname = 'VG ' + key
            lvg_size_MB = lvg.extentsTotal() * lvg.extent_size / (1024 * 1024)
            # display volume groups first in listbox
            self.listbox.addRow(['VG ' + key, str(lvg_size_MB), 'VolGroup',
                                 ''], lvg)
            lv_keys = lvg.lv_dict.keys()
            for lv_key in sorted(lv_keys):
                lv = self.disk_profile.lv_dict[lv_key]
                lv_devicename = '  LV ' + lv.name
                # display indented logical volumes belonging to the vg.
                self.listbox.addRow([lv_devicename, str(lv.size_MB),lv.fs_type,
                                    lv.mountpoint], lv)

        logger.debug('Partition screen: getting disk list')
        disk_keys = self.disk_profile.disk_dict.keys()
        for key in sorted(disk_keys):
            # display device
            device = self.disk_profile.disk_dict[key]
            self.listbox.addRow(['/dev/'+key, str(device.size/1024/1024), '', ''], device)
            parts_dict = self.disk_profile.disk_dict[key].partition_dict
            logger.debug('Disk %s has %d partitions as reported by parted.' % (key, \
                          self.disk_profile.disk_dict[key].pedDisk.get_last_partition_num()))
            parts_keys = parts_dict.keys()
            for part_key in sorted(parts_keys):
                partition = parts_dict[part_key]
                part_devicename = '  ' + key + str(partition.num)
                # indent one more level if logical partition.
                if partition.part_type == 'logical': part_devicename = '  ' + part_devicename
                fs_type = partition.fs_type
                mountpoint = partition.mountpoint
                if partition.lvm_flag:
                    fs_type = 'phys_vol'
                    for pv_name, pv in self.disk_profile.pv_dict.iteritems():
                        if pv.partition is partition and pv.group:
                            mountpoint = pv.group.name
                if partition.native_type == 'Dell Utility' or partition.dellUP_flag:
                    fs_type = 'Dell Utility'
                # display partition info
                self.listbox.addRow([part_devicename,
                                    str(partition.size_MB),
                                    fs_type,
                                    mountpoint], partition)

        prog_dlg.close()
        self.screenGrid.setField(self.listbox, col=0, row=0, anchorLeft=1,
                                 padding=(0,0,0,0))

        if self.listbox.length < 1:
           raise KusuError, 'The setup cannot continue because no ' + \
                            'disks could be found. Please check your ' + \
                            'system hardware to make sure that you have ' + \
                            'installed your disks correctly.'

    def findFormattedDisks(self):
        disks_keys = []
        for key,disk in self.disk_profile.disk_dict.iteritems():
            if isDiskFormatted(disk):
                disks_keys.append(key)
        return disks_keys

    def drawReinit(self, disks): 
        msg = 'The installer has detected drive(s) on this system that have a loop '
        msg += 'partition layout.\n\n'
        msg += 'To use a drive for installation, it must be re-initialized, '
        msg += 'causing the loss of ALL DATA on the drive.\n\n'
        msg += 'Please choose the drives that you wish to re-initialize below.\n\n'

        cbt = snack.CheckboxTree(3, scroll=1)
        for d in disks:
            cbt.append(d)
        
        gridForm = snack.GridForm(self.screen, _('Loop Partition Drives'),1,3)
        tb = snack.TextboxReflowed(40, msg)
        gridForm.add(tb, 0,0)

        gridForm.add(cbt, 0,1)

        proceed_button = kusuwidgets.Button(_('Proceed: Re-initialise Selected Drives'))
        cancel_button = kusuwidgets.Button(_('Cancel'))
        reboot_button = kusuwidgets.Button(_('Reboot'))
        subgrid = snack.Grid(3,1)
        subgrid.setField(proceed_button, 0,0)
        subgrid.setField(cancel_button, 1,0)
        subgrid.setField(reboot_button, 2,0)
        gridForm.add(subgrid, 0,2)
        gridForm.draw()
        exitCmd = gridForm.run()
        self.screen.popWindow()

        if exitCmd is reboot_button:
            raise UserExitError, 'User chose to reboot on re-init of drives.' 

        if exitCmd is proceed_button:
            return cbt.getSelection()

        return []

    def prepareIgnoreList(self, list):
        for d in list:
            disk = self.disk_profile.disk_dict.pop(d)
            self.disk_profile.ignore_disk_dict[d] = disk
        logger.debug('Ignore list: %s' % str(self.disk_profile.ignore_disk_dict.keys()))

    def useDefaultSchema(self, ignore_disks):
        logger.debug('Default chosen')
        self.disk_profile = partitiontool.DiskProfile(fresh=True, probe_fstab=False)
        self.prepareIgnoreList(ignore_disks)
        schema = vanillaSchemaLVM()
        logger.debug('%s' % schema)
        setupPreservedPartitions(self.disk_profile, schema)
        self.disk_order = self.disk_profile.getBIOSDiskOrder()
        try:
            setupDiskProfile(self.disk_profile, schema,
                             wipe_existing_profile=False,
                             disk_order=self.disk_order)
        except OutOfSpaceError,e:
            self.selector.popupDialogBox('Out of Space error', 
                                         "%s\nThe installer will now\
 exit." % (e) , ['Ok'])
            raise UserExitError, 'Rebooting due to error'


    def promptForDefaultSchema(self):
        formatted_disks = self.findFormattedDisks()
        do_not_use_disks = list(formatted_disks)
        if formatted_disks:
            chosen_disks = self.drawReinit(formatted_disks)
            logger.debug('Re-initializing disks: %s' % str(chosen_disks))
            for d in chosen_disks:
                do_not_use_disks.remove(d)
                runCommand('dd if=/dev/zero of=%s bs=1k count=10' % 
                           self.disk_profile.disk_dict[d].path)
            self.disk_profile = partitiontool.DiskProfile(fresh=False, probe_fstab=False)
            self.prepareIgnoreList(do_not_use_disks)

        exists = False
        for disk in self.disk_profile.disk_dict.values():
            if disk.partition_dict:
                exists = True
                break
        if exists:
            if self.lvm_inconsistent:
                buttons_list = ['Use Default', 'Clear All Partitions']
                msg = 'OCS installer can install using its default '
                msg += 'partition schema. Alternatively, you may choose '
                msg += 'to clear all partitions and create your own schema.'
            else:
                buttons_list = ['Use Default', 'Use Existing', 'Clear All Partitions']
                # tell user a schema exists and ask to proceed.
                msg = 'The installer has detected that one of the disks  ' + \
                      'is already partitioned. Do you want to use the ' + \
                      'default schema, edit the existing schema, or ' + \
                      'clear all partitions on the system?'
            result = self.selector.popupDialogBox('Partitions exist',
                                                  msg,
                                                  buttons_list)
            self.disk_order = self.disk_profile.getBIOSDiskOrder()
            if str(result) == 'use default':
                self.useDefaultSchema(do_not_use_disks)
            elif str(result) == 'clear all partitions':
                msg = 'Really clear all existing partitions? You cannot retrieve your '
                msg += 'existing partitions after proceeding.'
                result = self.selector.popupYesNo('Really clear partitions?', msg, defaultNo=True)
                if result:
                    logger.debug('Clear all partitions')
                    self.disk_profile = partitiontool.DiskProfile(fresh=True, probe_fstab=False)
                    self.prepareIgnoreList(do_not_use_disks)
                else:
                    msg = 'Do you want to use the default schema, or edit '
                    msg += 'the existing schema?'
                    result = self.selector.popupDialogBox('Partitions exist',
                                                          msg,
                                                         ['Use Default', 'Use Existing'])
                    if str(result) == 'use default':
                        self.useDefaultSchema(do_not_use_disks)
                    else:
                        logger.debug('Use Existing')
            else:
                logger.debug('Use Existing')

        else:
            # tell user nothing exists and ask to proceed.
            msg = 'The installer has detected that no disk(s) ' + \
                  'on this system are partitioned. Do you want to ' + \
                  'use the default schema?'
            result = self.selector.popupDialogBox('Use Default Partitioning Schema?',
                                                  msg,
                                                 ['Use Default', "Don't Use Default"])
            if str(result) == 'use default':
                self.useDefaultSchema(do_not_use_disks)

    def rollback(self):
        self.prompt_for_default_schema = True

    def validate(self):
        errList = []
        # verify that /, swap, /depot, and /boot exist.
        mntpnts = self.disk_profile.mountpoint_dict.keys()
        if '/' not in mntpnts:
            errList.append("'/' partition is required.")
        if '/depot' not in  mntpnts:
            errList.append("'/depot' partition is required.")
        if '/boot' not in  mntpnts:
            errList.append("'/boot' partition is required.")
        has_swap = False
        for disk in self.disk_profile.disk_dict.itervalues():
            for part in disk.partition_dict.itervalues():
                if part.fs_type == 'linux-swap':
                    has_swap = True
                    part.setLabel()
                    break
        if not has_swap:
            errList.append("A 'linux-swap' partition is required.")

        if not errList:
            # verify that /, /boot and /depot are to be formatted
            for mntpnt in ['/', '/boot', '/depot']:
                vol = self.disk_profile.mountpoint_dict[mntpnt]
                if vol.do_not_format or vol.leave_unchanged:
                    errList.append('%s is flagged as "do not format". ' % mntpnt + \
                                   'Installation cannot continue until this ' + \
                                   'flag is cleared.')

        if errList:
            errMsg = _('Please correct the following errors:')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
            return False, errMsg
        else:
            return True, ''

    def willBeFormatted(self, vol):
        if vol.do_not_format or vol.leave_unchanged:
            return False
        else:
            return True

    def swapPartitionExists(self):
        for disk in self.disk_profile.disk_dict.itervalues():
            for partition in disk.partition_dict.itervalues():
                if partition.fs_type == 'linux-swap':
                    return True
        for lv in self.disk_profile.lv_dict.itervalues():
            if lv.fs_type == 'linux-swap':
                return True
        return False
 
    def formAction(self):
        """
        
        Store to kiprofile
        
        """
        try:
            profile = self.kiprofile[self.profile]
        except KeyError:
            profile = {}
            self.kiprofile[self.profile] = profile

        profile['DiskProfile'] = self.disk_profile
        profile['disk_order'] = self.disk_order

        missing_fs_types = self.checkMissingFSTypes()
        if missing_fs_types:
            proceed = self.selector.popupMsg('No Filesystem type defined',
                        'The following volumes have mountpoints defined but ' + \
                        'no filesystem type defined. The installation cannot ' + \
                        'proceed until you have defined the filesystem for:\n' + \
                        missing_fs_types)
            self.selector.currentStep = self.selector.currentStep - 1
            return

    def checkMissingFSTypes(self):
        """Check that all the mountpoints have associated mountpoints."""
        missing_fs_types = []
        for vol in self.disk_profile.mountpoint_dict.values():
            if not vol.fs_type:
                missing_fs_type.append(vol.path) 
                setupDiskProfile(self.disk_profile, schema)

    def validate(self):
        errList = []
        # verify that /, swap, /depot, and /boot exist.
        mntpnts = self.disk_profile.mountpoint_dict.keys()
        if '/' not in mntpnts:
            errList.append("'/' partition is required.")
        if '/depot' not in  mntpnts:
            errList.append("'/depot' partition is required.")
        if '/boot' not in  mntpnts:
            errList.append("'/boot' partition is required.")
        has_swap = False
        for disk in self.disk_profile.disk_dict.itervalues():
            for part in disk.partition_dict.itervalues():
                if part.fs_type == 'linux-swap':
                    has_swap = True
                    break
        if not has_swap:
            errList.append("A 'linux-swap' partition is required.")

        if not errList:
            # verify that /, /boot and /depot are to be formatted
            for mntpnt in ['/', '/boot', '/depot']:
                vol = self.disk_profile.mountpoint_dict[mntpnt]
                if vol.do_not_format or vol.leave_unchanged:
                    errList.append('%s is flagged as "do not format". ' % mntpnt + \
                                   'Installation cannot continue until this ' + \
                                   'flag is cleared.')

        if errList:
            errMsg = _('Please correct the following errors:')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
            return False, errMsg
        else:
            return True, ''

    def willBeFormatted(self, vol):
        if vol.do_not_format or vol.leave_unchanged:
            return False
        else:
            return True

    def swapPartitionExists(self):
        for disk in self.disk_profile.disk_dict.itervalues():
            for partition in disk.partition_dict.itervalues():
                if partition.fs_type == 'linux-swap':
                    return True
        for lv in self.disk_profile.lv_dict.itervalues():
            if lv.fs_type == 'linux-swap':
                return True
        return False
 
    def formAction(self):
        """
        
        Store to kiprofile
        
        """
        try:
            profile = self.kiprofile[self.profile]
        except KeyError:
            profile = {}
            self.kiprofile[self.profile] = profile

        profile['DiskProfile'] = self.disk_profile
        profile['disk_order'] = self.disk_profile.getBIOSDiskOrder()

        missing_fs_types = self.checkMissingFSTypes()
        if missing_fs_types:
            proceed = self.selector.popupMsg('No Filesystem type defined',
                        'The following volumes have mountpoints defined but ' + \
                        'no filesystem type defined. The installation cannot ' + \
                        'proceed until you have defined the filesystem for:\n' + \
                        missing_fs_types)
            self.selector.currentStep = self.selector.currentStep - 1
            return

    def checkMissingFSTypes(self):
        """Check that all the mountpoints have associated mountpoints."""
        missing_fs_types = []
        for vol in self.disk_profile.mountpoint_dict.values():
            if not vol.fs_type:
                missing_fs_type.append(vol.path) 

#        proceed = self.selector.popupYesNo(_('Really Proceed?'),
#                       _('Proceeding beyond this screen will cause ' + \
#                         'irreversible changes to your disk(s).\n\nIf you ' + \
#                         'have any valuable data that is existing on your ' + \
#                         'current disk(s), please press "No" to cancel ' + \
#                         'installation, and then backup your data before ' + \
#                         're-attempting installation.\n\nOtherwise, if you ' + \
#                         'are sure you want to continue, then press the ' + \
#                         '"Yes" button.'), defaultNo=True)
#
#        if proceed:
#            from finalactions import setupDisks, mountKusuMntPts
#            prog_dlg = self.selector.popupProgress('Formatting Disks', 'Formatting disks...')
#            setupDisks(self.disk_profile)
#            mountKusuMntPts(self.kiprofile['Kusu Install MntPt'], self.disk_profile)
#            prog_dlg.close()
#        else:
#            self.selector.currentStep = self.selector.currentStep - 1
#         from finalactions import setupDisks, mountKusuMntPts
#         prog_dlg = self.selector.popupProgress('Formatting Disks', 'Formatting disks...')
#         setupDisks(self.disk_profile)
#         mountKusuMntPts(self.kiprofile['Kusu Install MntPt'], self.disk_profile)
#         prog_dlg.close()

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
    if not diskProfile.mountable_fsType[filesystem]:
        textEntry.setEntry('<Not Applicable>')
        textEntry.setEnabled(False)
    else:
        textEntry.setEntry(stored_mountpoint)
        textEntry.setEnabled(True)