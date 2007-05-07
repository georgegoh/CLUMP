#!/usr/bin/env python
# $Id: gatewaydns.py 237 2007-04-05 08:57:10Z ggoh $
#
# Kusu Text Installer Gateway and DNS Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision: 237 $"

import socket
#import logging
import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.installer.network import toggleEnabled
NAV_NOTHING = -1

class GatewayDNSSetupScreen(screenfactory.BaseScreen):
    """This screen asks for DNS and Gateway setups."""

    name = _('Gateway & DNS')
#    context = 'Gateway & DNS'
    context = 'Network'
    msg = _('Please configure your Gateway/DNS settings')
    buttons = [_('Clear All')]
#    backButtonDisabled = True

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
        self.screenGrid = snack.Grid(1, 6)
        entryWidth = 30

        self.use_dhcp = snack.Checkbox(_('Configure using DHCP'), isOn=1)

        value = self.database.get(self.context, 'Default Gateway')
        if not value: value = '192.168.111.2'
        else: value = value[0]
        self.gateway = kusuwidgets.LabelledEntry(
                           labelTxt=_('Default Gateway ').ljust(23), 
                           width=entryWidth, text=value)
        self.gateway.addCheck(kusuwidgets.verifyIP)

        value = self.database.get(self.context, 'DNS 1')
        if not value: value = '192.168.111.2'
        else: value = value[0]
        self.dns1 = kusuwidgets.LabelledEntry(
                        labelTxt=_('DNS Server 1 ').ljust(23),
                        width=entryWidth, text=value)
        self.dns1.addCheck(kusuwidgets.verifyIP)

        value = self.database.get(self.context, 'DNS 2')
        if not value: value = ''
        else: value = value[0]
        self.dns2 = kusuwidgets.LabelledEntry(
                        labelTxt=_('DNS Server 2(optional) ').ljust(23),
                        width=entryWidth, text=value)
        self.dns2.addCheck(kusuwidgets.verifyIP)

        value = self.database.get(self.context, 'DNS 3')
        if not value: value = ''
        else: value = value[0]
        self.dns3 = kusuwidgets.LabelledEntry(
                        labelTxt=_('DNS Server 3(optional) ').ljust(23), 
                        width=entryWidth, text=value)
        self.dns3.addCheck(kusuwidgets.verifyIP)

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.use_dhcp, col=0, row=1, anchorLeft=1,
                                 padding=(0,1,0,0))
        self.screenGrid.setField(self.gateway, col=0, row=2, anchorLeft=1,
                                 padding=(0,1,0,0))
        self.screenGrid.setField(self.dns1, col=0, row=3, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.dns2, col=0, row=4, anchorLeft=1,
                                 padding=(0,0,0,0))
        self.screenGrid.setField(self.dns3, col=0, row=5, anchorLeft=1,
                                 padding=(0,0,0,0))

        # add callback for toggling static IP fields
        self.use_dhcp.setCallback(toggleEnabled,
                                  (self.use_dhcp, self.gateway,
                                   self.dns1, self.dns2, self.dns3))
        toggleEnabled((self.use_dhcp, self.gateway,
                       self.dns1, self.dns2, self.dns3))

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
        self.database.put(self.context, 'Default Gateway', self.gateway.value())
        self.database.put(self.context, 'DNS 1', self.dns1.value())
        self.database.put(self.context, 'DNS 2', self.dns2.value())
        self.database.put(self.context, 'DNS 3', self.dns3.value())
