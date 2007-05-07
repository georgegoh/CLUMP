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

#import logging
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
        import kusu.util.log as kusulog
        self.logger = kusulog.getKusuLog('installer.confirm')
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
            mntpnt = '/mnt/kusu'

            disk_profile = self.kusuApp['DiskProfile']
            self.formatDisk(disk_profile)
            self.logger.debug('Formatted Disks.')
            self.setupNetwork()
            self.logger.debug('Network set up.')
            self.mountKusuMntPts(mntpnt, disk_profile)
            self.logger.debug('Kusu mount points set up')
            self.copyKits(mntpnt)
            self.logger.debug('Kits copied.')
            #self.makeRepo()
            self.genAutoInstallScript(disk_profile)
            self.logger.debug('Auto install script generated.')
            self.database.close()
            self.logger.debug('Closed database connection.')
            self.migrate(mntpnt)
            self.logger.debug('Migrated kusu.db and kusu.log')

    def formatDisk(self, disk_profile):
        disk_profile.commit()
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
       
    def copyKits(self, prefix):
        # Assume a Fedora 6 repo
        # Assume a fedora 6 distro: /mnt/sysimage
        from path import path
        from kusu.util import util

        url = str(self.database.get('Kits', 'FedoraURL')[0])

        prefix = path(prefix)
        util.verifyDistro(url, 'fedora', '6')
        util.copy(url, prefix + '/depot')

        
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

    def migrate(self, prefix):
        from path import path
        import os

        dest = path(prefix) + '/root'
        
        kusu_tmp = os.environ.get('KUSU_TMP', None)
        kusu_log = os.environ.get('KUSU_LOGFILE', None)

        if not kusu_tmp or not kusu_log:
            raise Exception

        kusu_tmp = path(kusu_tmp)
        kusu_log = path(kusu_log)

        #files = [kusu_tmp / 'kusu.db', kusu_log]
        files = [path('/kusu.db'), kusu_log]

        for f in files:
            if f.exists():
                self.logger.debug('Moved %s -> %s' % (f, dest))
                f.move(dest)

    def mountKusuMntPts(self, prefix, disk_profile):
        from path import path
 
        prefix = path(prefix)

        d = {}
        for disk in disk_profile.disk_dict.values():
            for id, p in disk.partition_dict.items():
                d[p.mountpoint] = p
       
        for lv in disk_profile.lv_dict.values():
            d[lv.mountpoint] = lv
 
        # Mount /, /root, /depot in order
        for m in ['/', '/root', '/depot']:
            mntpnt = prefix + m

            if not mntpnt.exists():
                mntpnt.makedirs()
                self.logger.debug('Made %s dir' % mntpnt)
            
            # mountpoint has an associated partition,
            # and mount it at the mountpoint
            if d.has_key(m):
                d[m].mount(mntpnt)
                self.logger.debug('Mounted %s on %s' % (d[m].mountpoint, mntpnt))

