#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Kits Setup Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.

import os
import snack
from gettext import gettext as _
from kitops import *
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from kusu.kitops.kitops import KitOps
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_NOTHING
from kusu.util import profile
from kusu.installer.finalactions import *
from path import path

kl = kusulog.getKusuLog('installer.kits')

class KitsScreen(InstallerScreen, profile.PersistentProfile):
    """Collects kits information."""
    name = _('Kits')
    profile = 'Kits'
    msg = _('Please enter a Fedora 6 URL:')
    buttons = [_('Add'), _('Remove')]
    backButtonDisabled = True

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistentProfile.__init__(self, kiprofile)

        db = self.kiprofile.getDatabase()
        self.kitops = KitOps(installer=True)
        self.kitops.setDB(db)
        self.kitops.setPrefix(self.kiprofile['Kusu Install MntPt'])
        self.kitops.setTmpPrefix(os.environ.get('KUSU_TMP', ''))

        self.installedBootMediaKits = False

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """
        self.buttonsDict[_('Add')].setCallback_(kitAdd, self)
        self.buttonsDict[_('Remove')].setCallback_(kitRemove, self)

    def drawImpl(self):
        prog_dlg = self.selector.popupProgress('Detecting Kits', 'Detecting kits...')

        self.screenGrid = snack.Grid(1, 1)

        self.listbox = kusuwidgets.ColumnListbox(height=8, 
                                 colWidths=[12,7,3,8],
                                 colLabels=[_('Kit Name'), _('Ver'), _('Rel'), ('Arch  ')],
                                 justification=[LEFT, RIGHT, RIGHT, RIGHT],
                                 returnExit=0)

        if not self.installedBootMediaKits:
            self.installKitsOnBootMedia()

        self.detectAndDisplayKits()

        prog_dlg.close()
        self.screenGrid.setField(self.listbox, col=0, row=0,
                                 padding=(0,0,0,0), anchorLeft=1)

    def detectAndDisplayKits(self):
        """Detect kits already existing in the system."""

        kit_list = self.kitops.listKit()
        for kit in kit_list:
            if kit.is_os():
                version = '%s.%s' % (kit.os.major,kit.os.minor)
                release = ''
            else:
                version = kit.version
                if self.kitops.getKitApi(kit.kid) == '0.1':
                    release = ''
                else:
                    release = str(kit.release)

            self.listbox.addRow([kit.rname, version, release, kit.arch], kit)

    def installKitsOnBootMedia(self):
        """Install the kits on boot media (most likely base kit only)."""

        import primitive.system.hardware.probe
        cdrom_dict = primitive.system.hardware.probe.getCDROM()
        cdrom_list = ['/dev/' + cd for cd in sorted(cdrom_dict.keys())]

        kl.debug('Media device list: %s', cdrom_list)

        boot_cd = ''
        for cd in cdrom_list:
            try:
                self.kitops.mountMedia(cd)
                boot_kits = self.kitops.getAvailableKits()
                self.kitops.unmountMedia()

                for boot_kit in boot_kits:
                    if boot_kit[1]['name'] == 'base':
                        boot_cd = cd
                        break
                if boot_cd:
                    break
            except CannotMountKitMediaError:
                pass

        if boot_cd:
            from kusu.installer.kits_sourcehandlers import addKitFromCDAction
            kl.debug('About to install base kit before showing kit screen')
            addKitFromCDAction(self, self.kitops, boot_cd)

        self.installedBootMediaKits = True

    def setDefaults(self):
        self.kiprofile[self.profile] = {}

    def validate(self):
        return True, ''

    def formAction(self):
        """
        Store
        """
        kl.debug('Store the kits.')
        kit_list = self.kitops.listKit()
        names = [kit.rname for kit in kit_list]
        os = [kit.rname for kit in kit_list if kit.isOS]
        missing = []

        if 'base' not in names:
            missing.append('base')
        if not os:
            missing.append(self.kiprofile['OS'])
        if missing:
            errMsg = 'Cannot continue installation unless the following ' + \
                     'kits are added:'
            for name in missing: errMsg += '\n\t%s' % name
            self.selector.currentStep -= 1
            self.selector.popupMsg('Missing Kits', errMsg)
            return

        self.kiprofile.save()

        prog_dlg = self.selector.popupProgress('Setting Up Network', 'Setting up networking...')
        setupNetwork()
        kl.debug('Network set up.')
        prog_dlg.close()

        #prog_dlg = self.selector.popupProgress('Setting Up Network Time', 'Setting up network time...')
        #writeNTP(self.kiprofile['Kusu Install MntPt'], self.kiprofile)
        #kl.debug('Network time set up.')
        #prog_dlg.close()

        setInstallFlag(self.kiprofile['Kusu Install MntPt'], self.kiprofile)
        kl.debug('Set the installation flag')

        kl.debug('Making repository')
        prog_dlg = self.selector.popupProgress('Making Repository', 'Making repository...')
        try:
            makeRepo(self.kiprofile)
        except NodeGroupNotFoundError, e:
            raise NodeGroupNotFoundError, 'Node Group %s not found.' % str(e)
        except NodeGroupHasRepoAlreadyError, e:
            raise NodeGroupHasRepoAlreadyError, \
                  'Repo already exists for % node group.' % str(e)
 
        kl.debug('installer repository is created')
        prog_dlg.close()

        kl.debug('Creating Auto-install script')
        prog_dlg = self.selector.popupProgress('Creating Auto-install Script', 'Creating Auto-install script...')
        disk_profile = self.kiprofile['Partitions']['DiskProfile']
        genAutoInstallScript(disk_profile, self.kiprofile)
        kl.debug('Auto install script generated.')
        prog_dlg.close()

        prog_dlg = self.selector.popupProgress('Migrating Kusu Logs', 'Migrating kusu logs...')
        migrate(self.kiprofile['Kusu Install MntPt'])
        kl.debug('Migrated kusu.db and kusu.log')
        prog_dlg.close()
                
        prog_dlg = self.selector.popupProgress('Ejecting cdrom(s)', 'Ejecing cdrom(s)...')
        from kusu.installer.kits_sourcehandlers import eject
        import primitive.system.hardware.probe
        cdrom_dict = primitive.system.hardware.probe.getCDROM()
        cdrom_list = [path('/dev/' + cd) for cd in cdrom_dict.keys()]

        for cdrom in cdrom_list:
            if cdrom.exists():
                try:
                    eject(cdrom)  
                    kl.info('ejected cdrom: %s', cdrom)
                except:
                    kl.warn('unable to eject cdrom: %s', cdrom)
        prog_dlg.close()
     
    def save(self, db, profile):
        ngs = db.NodeGroups.select()
        ngids = [row.ngid for row in db.NGHasComp.select()]

        for ng in ngs:
            if ng.ngid in ngids:
                ng.ngname = ng.ngname + '-' +  profile['longname']
        
                if ng.installtype == 'package':
                    ng.initrd = profile['initrd']
                    ng.kernel = profile['kernel']

        db.flush()
