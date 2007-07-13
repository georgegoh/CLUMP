#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Setup Confirmation Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
from gettext import gettext as _
from kusu.partitiontool import partitiontool
from kusu.ui.text import screenfactory
from kusu.installer.finalactions import *
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_NOTHING

class ConfirmScreen(InstallerScreen):
    """This screen confirms all settings made."""
    name = _('Finalise')
    profile = 'Finalise'
    msg = _('Please confirm the following:')
    buttons = [_('Re-initialise')]
    # unless explicitly specified here, all contexts will be rendered in the
    # minimal "key=value" form
    render_exceptions = {'Partitions':'self.renderPartition',
                         'Root Password':''}

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Re-initialise')].setCallback_(self.reinit)

    def reinit(self):
        self.selector.selectScreen(0)
        return NAV_NOTHING
 
    def drawImpl(self):
        import kusu.util.log as kusulog
        self.logger = kusulog.getKusuLog('installer.confirm')
        self.screenGrid = snack.Grid(1, 2)
        self.screenGrid.setField(snack.Label(self.msg), col=0, row=0)
        confirmText = ''
        #for context_key in self.database.getContexts():
        #    if context_key in self.render_exceptions.keys():
        #        renderFunc = self.render_exceptions[context_key]
        #        if renderFunc: 
        #            confirmText = confirmText + \
        #                          eval(renderFunc + '()')
        #    else:
        #        confirmText = confirmText + '[' + context_key + ']' + '\n'
        #        settings_for_context = self.database.get(context_key)
        #        for setting in settings_for_context:
        #            confirmText = confirmText + '  ' + str(setting[2]) + '=' + \
        #                          str(setting[3]) + '\n'
        #        confirmText = confirmText + '\n'
        textBox = snack.Textbox(40, 10, confirmText, 1)
        self.screenGrid.setField(textBox, col=0, row=1, padding=(0,0,0,-2))

    def renderPartition(self):
        """Partitions are rendered as follows:
           [Partitions]
           Name(15 chars) Size(M)(8 chars) FS type(9 chars) Mountpoint(12 chars)
        ""
        dispTxt = '\n[Partitions]\n'
        dispTxt = dispTxt + 'Name            Size(M)  FS type   Mountpoint\n'
        dispTxt = dispTxt + '----            -------  -------   ----------\n'
        for vg_name, vg in sorted(partitiontool.lv_groups.iteritems()):
            dispTxt = dispTxt + vg_name[0:15] + '\n'
            for lv_id in vg.logical_volume_ids:
                lv = partitiontool.logi_vol[lv_id]
                dispTxt = dispTxt + '  ' + lv_id[0:13].ljust(13) + ' ' + \
                          str(lv.size)[0:8].ljust(8) + ' ' + \
                          lv.fs_type[0:9].ljust(9) + \
                          ' ' + lv.mountpoint[0:12].ljust(12) + '\n'
            
        for disk_name, disk in sorted(partitiontool.disks.iteritems()):
            dispTxt = dispTxt + disk_name[0:15] + '\n'
            for part_id in sorted(disk.partitions_dict.itervalues()):
                partition = partitiontool.partitions[part_id]
                dispTxt = dispTxt + '  ' + part_id[0:13].ljust(13) + ' ' + \
                          str(partition.size)[0:8].ljust(8) + ' ' + \
                          partition.fs_type[0:9].ljust(9) + ' ' + \
                          partition.mountpoint[0:12].ljust(12) + '\n'

        return dispTxt + '\n'
"""
        return ''

    def formAction(self):
#        result = snack.ButtonChoiceWindow(self.screen, title='Really continue?',
#                                          text='If you click ok, then your disks will be formatted.\n' + \
#                                               'You cannot recover data on a disk once it has been formatted.')
#        if result == 'ok':
         self.kiprofile.save()

         #prog_dlg = self.selector.popupProgress('Formatting Disks', 'Formatting disks...')
         #disk_profile = self.kiprofile['Partitions']['DiskProfile']
         #setupDisks(disk_profile)
         #prog_dlg.close()

         prog_dlg = self.selector.popupProgress('Setting Up Network', 'Setting up networking...')
         setupNetwork()
         self.logger.debug('Network set up.')
         prog_dlg.close()

         prog_dlg = self.selector.popupProgress('Setting Up Network Time', 'Setting up network time...')
         writeNTP(self.kiprofile['Kusu Install MntPt'], self.kiprofile)
         self.logger.debug('Network time set up.')
         prog_dlg.close()

         prog_dlg = self.selector.popupProgress('Making Repository', 'Making repository...')
         makeRepo(self.kiprofile)
         self.logger.debug('installer repository is created')
         prog_dlg.close()
            
         prog_dlg = self.selector.popupProgress('Creating Auto-install Script', 'Creating Auto-install script...')
         disk_profile = self.kiprofile['Partitions']['DiskProfile']
         genAutoInstallScript(disk_profile, self.kiprofile)
         self.logger.debug('Auto install script generated.')
         prog_dlg.close()

         prog_dlg = self.selector.popupProgress('Migrating Kusu Logs', 'Migrating kusu logs...')
         migrate(self.kiprofile['Kusu Install MntPt'])
         self.logger.debug('Migrated kusu.db and kusu.log')
         prog_dlg.close()
