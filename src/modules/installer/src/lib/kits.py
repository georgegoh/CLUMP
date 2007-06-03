#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Kits Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.

import snack
from gettext import gettext as _
from kits_add import *
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from kusu.kitops.kitops import KitOps
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_NOTHING

kl = kusulog.getKusuLog('installer.kits')

class KitsScreen(InstallerScreen):
    """Collects kits information."""
    name = _('Kits')
    profile = 'Kits'
    msg = _('Please enter a Fedora 6 URL:')
    buttons = [_('Add'), _('Remove')]

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """
        self.buttonsDict[_('Add')].setCallback_(kitAdd, self)
        self.buttonsDict[_('Remove')].setCallback_(self.removeKit)

    def addKit(self):
        return NAV_NOTHING

    def removeKit(self):
        return NAV_NOTHING

    def drawImpl(self):
        prog_dlg = self.selector.popupProgress('Detecting Kits', 'Detecting kits...')

        self.screenGrid = snack.Grid(1, 1)

        self.listbox = kusuwidgets.ColumnListbox(height=8, 
                                 colWidths=[15,7,8],
                                 colLabels=[_('Kit Name'), _('Version'), _('Arch  ')],
                                 justification=[LEFT, RIGHT, RIGHT],
                                 returnExit=0)

        self.detectAndDisplayKits()

        prog_dlg.close()
        self.screenGrid.setField(self.listbox, col=0, row=0,
                                 padding=(0,0,0,0), anchorLeft=1)

    def detectAndDisplayKits(self):
        """Detect kits already existing in the system."""
        db = self.kiprofile.getDatabase()
        self.kitops = KitOps()
        self.kitops.setDB(db)
        kit_list = self.kitops.listKit()
        for kit in kit_list:
            self.listbox.addRow([kit.rname, kit.version, kit.arch], kit)

    def validate(self):
        return True, ''

    def formAction(self):
        """
        Store
        """
        pass

