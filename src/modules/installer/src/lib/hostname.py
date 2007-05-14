#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Host Name Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.

import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
from kusu.installer import network
import kusu.util.util as kusutil
import kusu.util.log as kusulog

NAV_NOTHING = -1

kl = kusulog.getKusuLog('installer.network')

class FQHNScreen(screenfactory.BaseScreen):
    """Collects fully-qualified host name."""

    name = _('Host Name')
    context = 'Network'
    msg = _('Please specify a fully-qualified host name for this computer:')
    buttons = [_('Clear All')]

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """

        self.buttonsDict[_('Clear All')].setCallback_(self.clearAllFields)

    def clearAllFields(self):
        """
        Erase all data entered by the user.
        """

        self.netProfile['fqhn_use_dhcp'] = self.use_dhcp.value()
        self.netProfile['fqhn'] = self.hostname.value()

        if not self.netProfile['fqhn_use_dhcp']:
            self.netProfile['fqhn'] = ''
        return NAV_NOTHING

    def drawImpl(self):
        """
        Draw the window.
        """

        self.netProfile = self.kusuApp['netProfile']

        self.screenGrid = snack.Grid(1, 3)
        entryWidth = 33

        self.use_dhcp = snack.Checkbox(_('Use DHCP'), isOn=1)
        self.use_dhcp.setFlags(snack.FLAG_DISABLED, snack.FLAGS_RESET)

        try:
            if not self.netProfile['have_dhcp']:
                self.use_dhcp.setValue(' ')
                self.use_dhcp.setFlags(snack.FLAG_DISABLED, snack.FLAGS_SET)
            if not self.netProfile['fqhn_use_dhcp']:
                self.use_dhcp.setValue(' ')
        except KeyError:
            pass

        self.hostname = kusuwidgets.LabelledEntry(
                    labelTxt=_('Host name '), width=entryWidth)
        self.hostname.addCheck(kusutil.verifyFQDN)

        try:
            self.hostname.setEntry(self.netProfile['fqhn'])
        except KeyError:
            pass

        dhcpd = {'control': self.use_dhcp,
                 'disable': (self.hostname, ),
                 'enable': (self.hostname, ),
                 'invert': True}
        self.use_dhcp.setCallback(network.enabledByValue, [dhcpd])
        network.enabledByValue([dhcpd])

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.use_dhcp, col=0, row=1,
                                 padding=(0, 1, 0, 0), anchorLeft=1)
        self.screenGrid.setField(self.hostname, col=0, row=2,
                                 padding=(3, 0, 0, 1), anchorLeft=1)

    def validate(self):
        """
        Perform validity checks on received data.
        """

        if not self.use_dhcp.value():
            rv, msg = self.hostname.verify()
            if rv is None:
                return False, _('Host name field is empty')
            if not rv:
                return False, msg

        return True, ''

    def formAction(self):
        """
        Store the gateway settings.
        """

        self.netProfile['fqhn_use_dhcp'] = bool(self.use_dhcp.value())
        self.netProfile['fqhn'] = self.hostname.value()
        self.netProfile['fqhn_host'] = self.netProfile['fqhn'].split('.')[0]
        self.netProfile['fqhn_domain'] = \
                                '.'.join(self.netProfile['fqhn'].split('.')[1:])

        self.database.put(self.context, 'fqhn_use_dhcp',
                          str(int(self.netProfile['fqhn_use_dhcp'])))
        self.database.put(self.context, 'fqhn_host',
                          self.netProfile['fqhn_host'])
        self.database.put(self.context, 'fqhn_domain',
                          self.netProfile['fqhn_domain'])

        if self.netProfile['fqhn_use_dhcp']:
            kl.info('Set FQHN via DHCP.')
        else:
            kl.info('Set FQHN: %s.' % self.netProfile['fqhn'])
