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
from kusu.installer.language import getLangMap
from kusu.installer.keyboard import modelDict as keyboardDict
import kusu.util.log as kusulog
logger = kusulog.getKusuLog('installer.confirm')

class ConfirmScreen(InstallerScreen):
    """This screen confirms all settings made."""
    name = _('Confirm')
    profile = 'Confirm'
    msg = _('Please confirm the following:')
    buttons = [_('Restart Installation')]
    isCommitment = True

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        # Unless specified in render_exceptions, all keys in the kiprofile
        # will be rendered as strings.
        self.render_exceptions = {'Partitions':self.renderPartition,
                                  'RootPasswd':None,
                                  'Kusu Install MntPt':None,
                                  'OS_ARCH':None,
                                  'OS_VERSION':None,
                                  'Kits':None,
                                  'OS':None,
                                  'Network':self.renderNetwork,
                                  'Language':self.renderLanguage,
                                  'Keyboard':self.renderKeyboard,
                                  'Timezone':self.renderTimezone,
                                  'InstNum':self.renderInstNum}

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Restart Installation')].setCallback_(self.reinit)

    def reinit(self):
        self.selector.selectScreen(0)
        return NAV_NOTHING
 
    def drawImpl(self):
        import kusu.util.log as kusulog
        self.logger = kusulog.getKusuLog('installer.confirm')
        self.screenGrid = snack.Grid(1, 2)
        self.screenGrid.setField(snack.Label(self.msg), col=0, row=0)
        confirmText = ''
        for context_key in self.kiprofile.keys():
            if context_key in self.render_exceptions.keys():
                renderFunc = self.render_exceptions[context_key]
                if renderFunc: 
                    confirmText = confirmText + \
                                  renderFunc()
            else:
                confirmText = confirmText + '\n[' + context_key + ']\n'
                settings_for_context = self.kiprofile[context_key]
                for setting in settings_for_context:
                    confirmText += str(setting) + '\n'
                confirmText += '\n'
        textBox = snack.Textbox(40, 10, confirmText, 1)
        self.screenGrid.setField(textBox, col=0, row=1, padding=(0,0,0,-2))

    def renderTimezone(self):
        tz = self.kiprofile['Timezone']
        dispTxt = '\n[Timezone]\n'  
        dispTxt += 'Timezone: %s\n' % tz['zone']
        dispTxt += 'NTP Server: %s\n' % tz['ntp_server']

        if tz['utc']:
            dispTxt += 'System uses UTC\n'
        else:
            dispTxt += 'System not using UTC\n'

        logger.debug(dispTxt)
        return dispTxt + '\n'

    def renderKeyboard(self):
        keyb_key = self.kiprofile['Keyboard']
        dispTxt = '\n[Keyboard]\n'
        dispTxt += keyboardDict[keyb_key][0] + '\n'
        return dispTxt

    def renderLanguage(self):
        lang_key = self.kiprofile['Language']
        dispTxt = '\n[Language]\n'
        langMap = getLangMap()
        for k,v in langMap.iteritems():
            if v[0] == lang_key:
                dispTxt += k + '\n'
                break
        return dispTxt

    def renderNetwork(self):
        network_profile = self.kiprofile['Network']
        dispTxt = '\n[Network]\n'
        dispTxt += 'Admin Email: %s\n' % network_profile['admin_email']
        dispTxt += 'Hostname: %s\n' % network_profile['fqhn_host']
        dispTxt += 'Domain: %s\n' % network_profile['fqhn_domain']
        dispTxt += 'Gateway: %s\n' % network_profile['default_gw']
        dispTxt += 'DNS 1: %s\n' % network_profile['dns1']
        if network_profile['dns2']:
            dispTxt += 'DNS 2: %s\n' % network_profile['dns2']
        if network_profile['dns3']:
            dispTxt += 'DNS 3: %s\n' % network_profile['dns3']

        interfaces = network_profile['interfaces']
        for name, intf in sorted(interfaces.iteritems()):
            if intf['configure']:
                dispTxt += '\n' + name + '\n'
                dispTxt += '-' * len(name)
                dispTxt += '\n  MAC Addr: %s\n' % intf['hwaddr']

                if intf['use_dhcp']:
                    dispTxt += '  Using DHCP\n'
                else:
                    dispTxt += '  IP: %s\n' % intf['ip_address']
                    dispTxt += '  Netmask: %s\n' % intf['netmask']

                dispTxt += '  Active on Boot: %s\n' % intf['active_on_boot']
                dispTxt += '  Net Name: %s\n' % intf['netname']
                dispTxt += '  Net Type: %s\n' % intf['nettype']
        return dispTxt + '\n'

    def renderInstNum(self):
        dispTxt = '\n[Installation Number]\n'

        if self.kiprofile['InstNum']:
            dispTxt += self.kiprofile['InstNum'] + '\n'
        else:
            dispTxt += 'Skipped\n'
 
        return dispTxt


    def renderPartition(self):
        """Partitions are rendered as follows:
           [Partitions]
           Name(15 chars) Size(M)(8 chars) FS type(9 chars) Mountpoint(12 chars)
        """
        disk_profile = self.kiprofile['Partitions']['DiskProfile']
        dispTxt = '\n[Partitions]\n'
        dispTxt = dispTxt + 'Name            Size(M)  FS type   Mountpoint\n'
        dispTxt = dispTxt + '----            -------  -------   ----------\n'
        for vg_name, vg in sorted(disk_profile.lvg_dict.iteritems()):
            dispTxt = dispTxt + vg_name[0:15] + '\n'
            for lv in vg.lv_dict.values():
                dispTxt += '  ' + lv.name[0:13].ljust(13)
                dispTxt += ' ' + str(lv.size_MB)[0:8].ljust(8)
                dispTxt += ' ' + str(lv.fs_type)[0:9].ljust(9)
                mountpoint = lv.mountpoint or ''
                dispTxt += ' ' + mountpoint[0:12].ljust(12) + '\n'
            
        for disk_name, disk in sorted(disk_profile.disk_dict.iteritems()):
            dispTxt = dispTxt + disk_name[0:15] + '\n'
            for part_id, partition in sorted(disk.partition_dict.iteritems()):
                dispTxt += '  ' + partition.path[0:13].ljust(13) + ' '
                dispTxt += str(partition.size_MB)[0:8].ljust(8) + ' '
                fs_type = partition.fs_type or ''
                dispTxt += fs_type[0:9].ljust(9) + ' '
                mountpoint = partition.mountpoint or ''
                dispTxt += mountpoint[0:12].ljust(12) + '\n'

        return dispTxt + '\n'


    def formAction(self):
        result = snack.ButtonChoiceWindow(self.screen, title='Really continue?',
                                          text='If you click ok, then your disks will be formatted.\n' + \
                                               'You cannot recover data on a disk once it has been formatted.')
        if result != 'ok': 
            self.selector.currentStep = self.selector.currentStep - 1
            return

        from finalactions import setupDisks, mountKusuMntPts
        prog_dlg = self.selector.popupProgress('Formatting Disks', 'Formatting disks...')
        disk_profile = self.kiprofile['Partitions']['DiskProfile']
        setupDisks(disk_profile)
        mountKusuMntPts(self.kiprofile['Kusu Install MntPt'], disk_profile)
        prog_dlg.close()
