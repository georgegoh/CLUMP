#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer License Entry Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
from gettext import gettext as _
from kusu.ui.text import kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_FORWARD
import instnum

kl = kusulog.getKusuLog('installer.instnum')

class LicenseScreen(InstallerScreen):
    name = _('Installation Number')
    profile = 'InstNum'
    msg = _('Please enter the Installation number')
    buttons = [_('Skip')]

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Skip')].setCallback_(self.skip)

    def skip(self):
        return NAV_FORWARD

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        entryWidth = 20
        self.license = kusuwidgets.LabelledEntry(
                       labelTxt=_('Installation number ').rjust(26), 
                       width=entryWidth)

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.license, col=0, row=1, anchorLeft=1,
                                 padding=(0,1,0,0))

    def validate(self):

        key = self.license.value()

        # Reference from anaconda, installclasses/rhel.py
        try:
            inum = instnum.InstNum(key)
        except:
            return False, 'Invalid installation number'

        if inum:
            # make sure the base products match
            buildstamp = path('/.buildstamp')
            
            if buildstamp.exists():
                f = buildstamp.open()
                productPath = f.readlines()[3].strip()
                f.close()

                if inum.get_product_string().lower() != productPath.lower():
                    return False, "Installation number incompatible with media"
     
    def formAction(self):
        """
        Store
        """

        self.kiprofile[self.profile] = self.license.value()
