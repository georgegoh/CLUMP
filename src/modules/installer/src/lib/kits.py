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

kl = kusulog.getKusuLog('installer.kits')

class KitsScreen(InstallerScreen, profile.PersistentProfile):
    """Collects kits information."""
    name = _('Kits')
    profile = 'Kits'
    msg = _('Please enter a Fedora 6 URL:')
    buttons = [_('Add'), _('Remove')]


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
                                 colWidths=[15,7,8],
                                 colLabels=[_('Kit Name'), _('Version'), _('Arch  ')],
                                 justification=[LEFT, RIGHT, RIGHT],
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
            self.listbox.addRow([kit.rname, kit.version, kit.arch], kit)

    def installKitsOnBootMedia(self):
        """Install the kits on boot media (most likely base kit only)."""

        import kusu.hardware.probe
        cdrom_dict = kusu.hardware.probe.getCDROM()
        cdrom_list = ['/dev/' + cd for cd in sorted(cdrom_dict.keys())]

        kl.debug('Media device list: %s', cdrom_list)

        boot_cd = ''
        for cd in cdrom_list:
            try:
                self.kitops.mountMedia(cd)
                boot_kit = self.kitops.determineKitName()
                self.kitops.unmountMedia()

                if boot_kit == 'base':
                    boot_cd = cd
                    break
            except CannotMountKitMediaError:
                pass
            except NoKitsFoundError:
                self.kitops.unmountMedia()

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


    def save(self, db, profile):
        ngs = db.NodeGroups.select()
        ngids = [row.ngid for row in db.NGHasComp.select()]

        for ng in ngs:
            if ng.ngid in ngids:
                ng.ngname = ng.ngname + '-' +  profile['longname']
                ng.initrd = profile['initrd']
                ng.kernel = profile['kernel']

        db.flush()
