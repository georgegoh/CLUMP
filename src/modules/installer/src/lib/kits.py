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
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT

NAV_NOTHING = -1

class KitsScreen(screenfactory.BaseScreen):
    """Collects kits information."""
    name = _('Kits')
    context = 'Kits'
    msg = _('Please enter a Fedora 6 URL:')
    buttons = [_('Clear All')]

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Clear All')].setCallback_(self.clearAllFields)

    def clearAllFields(self):
        self.database.put(self.context, 'FedoraURL', '')
        return NAV_NOTHING

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        entryWidth = 33

        value = self.database.get(self.context, 'FedoraURL')
        if not value: value = 'http://172.25.208.218/repo/fedora/6/i386/os/'
        else: value = value[0]
 
        self.url = kusuwidgets.LabelledEntry(
                        labelTxt=_('URL ').rjust(4), 
                        width=entryWidth, text=value)

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.url, col=0, row=1,
                                 padding=(0,1,0,1), anchorLeft=1)

    def validate(self):
        return True, ''
    def formAction(self):
        """
        
        Store
        
        """
        self.database.put(self.context, 'FedoraURL', self.url.value())
