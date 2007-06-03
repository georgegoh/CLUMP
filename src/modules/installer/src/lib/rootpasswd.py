#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Root Password Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import snack
from gettext import gettext as _
from kusu.ui.text import kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
import kusu.util.log as kusulog
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_NOTHING

kl = kusulog.getKusuLog('installer.rootpasswd')

class RootPasswordScreen(InstallerScreen):
    """Collects info about the cluster."""
    name = _('Root Password')
    profile = 'RootPasswd'
    msg = _('Please enter a secure root password:')
    buttons = [_('Clear All')]

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Clear All')].setCallback_(self.clearAllFields)

    def clearAllFields(self):
        self.password0.setEntry('')
        self.password1.setEntry('')
        return NAV_NOTHING

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 3)
        entryWidth = 20
        self.password0 = kusuwidgets.LabelledEntry(
                        labelTxt=_('Enter root password ').rjust(26), 
                        width=entryWidth, password=1)

        self.password1 = kusuwidgets.LabelledEntry(
                        labelTxt=_('Verify root password ').rjust(26), 
                        width=entryWidth, password=1)

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.password0, col=0, row=1, anchorLeft=1,
                                 padding=(0,1,0,0))
        self.screenGrid.setField(self.password1, col=0, row=2, anchorLeft=1,
                                 padding=(0,0,0,1))

    def validate(self):
        errList = []
        result, msg = self.password0.verify()
        if result is None:
            errList.append(_('Password field is empty'))

        if self.password0.value() != self.password1.value():
            errList.append(_('Both entries must be matching strings.'))

        if errList:
            errMsg = _('Please correct the following error(s):')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
            self.clearAllFields()
            return False, errMsg
        else:
            return True, ''

    def formAction(self):
        """
        Store
        """

        self.kiprofile[self.profile] = self.password0.value()

