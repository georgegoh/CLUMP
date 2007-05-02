#!/usr/bin/env python
# $Id: confirm.py 248 2007-04-10 09:35:57Z ggoh $
#
# Kusu Text Installer Setup Confirmation Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision: 248 $"

import logging
import snack
from gettext import gettext as _
from kusu.partitiontool import partitiontool
from kusu.ui.text import screenfactory

NAV_RESTART = -2
NAV_NOTHING = -1
NAV_FORWARD = 0
NAV_BACK = 1
NAV_QUIT = 2

class ConfirmScreen(screenfactory.BaseScreen):
    """This screen confirms all settings made."""
    name = _('Finalise')
    context = 'Finalise'
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
        self.screenGrid = snack.Grid(1, 2)
        self.screenGrid.setField(snack.Label(self.msg), col=0, row=0)
        confirmText = ''
        for context_key in self.database.getContexts():
            if context_key in self.render_exceptions.keys():
                renderFunc = self.render_exceptions[context_key]
                if renderFunc: 
                    confirmText = confirmText + \
                                  eval(renderFunc + '()')
            else:
                confirmText = confirmText + '[' + context_key + ']' + '\n'
                settings_for_context = self.database.get(context_key)
                for setting in settings_for_context:
                    confirmText = confirmText + '  ' + str(setting[2]) + '=' + \
                                  str(setting[3]) + '\n'
                confirmText = confirmText + '\n'
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
        result = snack.ButtonChoiceWindow(self.screen, title='Really continue?',
                                          text='If you click yes, then your disks will be formatted.\n' + \
                                               'You cannot recover data on a disk once it has been formatted.')
        if result == 'ok':
            disk_profile = self.kusuApp['DiskProfile']
            self.formatDisk(disk_profile)
            self.setupNetwork()
            self.copyKits(disk_profile)
            #self.makeRepo()
            self.genAutoInstallScript(disk_profile)
            self.database.close()

    def formatDisk(self, disk_profile):
        disk_profile.formatAll()

    def setupNetwork(self):
        # Use dhcpc from busybox
        # Assume eth0 for now
        from kusu.networktool import networktool

        interface = networktool.Interface('lo')
        interface.up()
        #interface = interface.setStaticIP(('127.0.0.1', '255.0.0.0'))

        interface = networktool.Interface('eth0')
        interface.up()
        interface = interface.setDHCP()
       
    def copyKits(self, disk_profile):
        # Assume a Fedora 6 repo
        # Assume a fedora 6 distro: /mnt/sysimage
        import subprocess
        import os
        from path import path
        from kusu.util import util

        def mount_dir(disk_profile, mntpnt, repo_dir):
            for disk in disk_profile.disk_dict.values():
                for id, p in disk.partitions_dict.items():
                    #print id, p.path, p.mountpoint, fs_type, p.type
                    if p.mountpoint == mntpnt: 
                        cmd = 'mount -t %s %s %s' % (p.fs_type, p.path, repo_dir)
                        os.system(cmd)
                    

        url = str(self.database.get('Kits', 'FedoraURL')[0])

        # Mount /repo for now
        repo_dir = path('/mnt/kusu/repo')
        repo_dir.makedirs()
        mount_dir(disk_profile, path('/repo'), repo_dir)

        util.verifyDistro(url, 'fedora', '6')
        util.copy(url, repo_dir)

        
    def makeRepo(self):
        pass

    def genAutoInstallScript(self, disk_profile):
        from kusu.autoinstall.scriptfactory import KickstartFactory
        from kusu.autoinstall.autoinstall import Script
        from kusu.autoinstall.installprofile import Kickstart
        from kusu.networktool.network import Network
        from path import path
        import os


        # redhat based for now
        #kusu_dist = os.environ.get('KUSU_DIST', None)
        #kusu_distver = os.environ.get('KUSU_DISTVER', None)


        install_script = '/tmp/install_script'

        k = Kickstart()
        k.rootpw = self.database.get('Root Password', 'RootPasswd')[0]
        k.networkprofile = [Network('eth0', 'DHCP')]
        k.diskprofile = disk_profile
        k.packageprofile = ['@Base']
        k.tz = self.database.get('Time zone', 'Zone')[0]
        k.installsrc = 'http://127.0.0.1/'
        k.lang = self.database.get('Language', 'Language')[0]
        k.keyboard = self.database.get('Keyboard', 'Keyboard')[0]

        template = path(os.getenv('KUSU_ROOT', None)) / \
                   'etc' / \
                   'templates' / \
                   'kickstart.tmpl'

        kf = KickstartFactory(str(template))
        script = Script(kf)
        script.setProfile(k)
        script.write(install_script)


