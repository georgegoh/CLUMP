#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Gateway and DNS Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

import socket
import logging
import snack
from gettext import gettext as _
from ui.text import screenfactory, kusuwidgets
NAV_NOTHING = -1

class GatewayDNSSetupScreen(screenfactory.BaseScreen):
    """This screen asks for DNS and Gateway setups."""
    name = _('Gateway & DNS')
    msg = _('Please enter the following information:')
    buttons = [_('Clear All')]
    backButtonDisabled = True

    def setCallbacks(self):
        """
        
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        
        """
        self.buttonsDict[_('Clear All')].setCallback_(self.clearAllFields)

    def clearAllFields(self):
        self.gateway.setEntry('')
        self.dns1.setEntry('')
        self.dns2.setEntry('')
        self.dns3.setEntry('')
        return NAV_NOTHING

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 5)
        entryWidth = 30
        self.gateway = kusuwidgets.LabelledEntry(
                           labelTxt=_('Default Gateway ').ljust(23), 
                           width=entryWidth, text='192.168.111.2')
        self.gateway.addCheck(kusuwidgets.verifyIP)

        self.dns1 = kusuwidgets.LabelledEntry(
                        labelTxt=_('DNS Server 1 ').ljust(23),
                        width=entryWidth, text='192.168.111.2')
        self.dns1.addCheck(kusuwidgets.verifyIP)

        self.dns2 = kusuwidgets.LabelledEntry(
                        labelTxt=_('DNS Server 2(optional) ').ljust(23),
                        width=entryWidth, text='')
        self.dns2.addCheck(kusuwidgets.verifyIP)

        self.dns3 = kusuwidgets.LabelledEntry(
                        labelTxt=_('DNS Server 3(optional) ').ljust(23), 
                        width=entryWidth, text='')
        self.dns3.addCheck(kusuwidgets.verifyIP)

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                 width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.gateway, col=0, row=1, anchorLeft=1,
                                 padding=(0,1,0,0))
        self.screenGrid.setField(self.dns1, col=0, row=2, anchorLeft=1,
                                 padding=(0,1,0,0))
        self.screenGrid.setField(self.dns2, col=0, row=3, anchorLeft=1,
                                 padding=(0,1,0,0))
        self.screenGrid.setField(self.dns3, col=0, row=4, anchorLeft=1,
                                 padding=(0,1,0,0))


    def validate(self):
        errList = []

        result, msg = self.gateway.verify()
        if result is None:
            errList.append(_('Default Gateway field is empty'))
        elif not result:
            errList.append(_('Default Gateway: ') + msg)

        result, msg = self.dns1.verify()
        if result is None:
            errList.append(_('DNS Server 1 field is empty'))
        elif not result:
            errList.append(_('DNS Server 1: ') + msg)

        # optional field
        result, msg = self.dns2.verify()
        if result is False:
            errList.append(_('DNS Server 2: ') + msg)

        # optional field
        result, msg = self.dns3.verify()
        if result is False:
            errList.append(_('DNS Server 3: ') + msg)

        if errList:
            errMsg = _('Please correct the following errors:')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
            return False, errMsg
        else:
            return True, ''

    def formAction(self):
        """
        
        Store the gateway settings.
        
        """
        self.database.put(self.name, 'Default Gateway', self.gateway.value())
        self.database.put(self.name, 'DNS 1', self.dns1.value())
        self.database.put(self.name, 'DNS 2', self.dns2.value())
        self.database.put(self.name, 'DNS 3', self.dns3.value())
