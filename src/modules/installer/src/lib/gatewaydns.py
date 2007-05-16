#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Gateway and DNS Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.

import socket
import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.installer import network
import kusu.util.util as kusutil
import kusu.util.log as kusulog

NAV_NOTHING = -1

kl = kusulog.getKusuLog('installer.network')

class GatewayDNSSetupScreen(screenfactory.BaseScreen):
    """This screen asks for DNS and Gateway setups."""

    name = _('Gateway & DNS')
    context = 'Network'
    profile = context
    msg = _('Please configure your Gateway/DNS settings')
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

        self.netProfile['gw_dns_use_dhcp'] = bool(self.use_dhcp.value())
        self.netProfile['default_gw'] = self.gateway.value()
        self.netProfile['dns1'] = self.dns1.value()
        self.netProfile['dns2'] = self.dns2.value()
        self.netProfile['dns3'] = self.dns3.value()

        if not self.netProfile['gw_dns_use_dhcp']:
            self.netProfile['default_gw'] = ''
            self.netProfile['dns1'] = ''
            self.netProfile['dns2'] = ''
            self.netProfile['dns3'] = ''
        return NAV_NOTHING

    def drawImpl(self):
        """
        Draw the window.
        """

        self.netProfile = self.kiprofile[self.profile]

        self.screenGrid = snack.Grid(1, 6)
        entryWidth = 28

        self.use_dhcp = snack.Checkbox(_('Use DHCP'), isOn=1)

        self.gateway = kusuwidgets.LabelledEntry(
                                   labelTxt=_('Default Gateway ').rjust(24), 
                                   width=entryWidth)
        self.gateway.addCheck(kusutil.verifyIP)

        self.dns1 = kusuwidgets.LabelledEntry(
                                    labelTxt=_('DNS Server 1 ').rjust(24),
                                    width=entryWidth)
        self.dns1.addCheck(kusutil.verifyIP)

        self.dns2 = kusuwidgets.LabelledEntry(
                            labelTxt=_('DNS Server 2 (optional) ').rjust(24),
                            width=entryWidth)
        self.dns2.addCheck(kusutil.verifyIP)

        self.dns3 = kusuwidgets.LabelledEntry(
                            labelTxt=_('DNS Server 3 (optional) ').rjust(24), 
                            width=entryWidth)
        self.dns3.addCheck(kusutil.verifyIP)

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        self.screenGrid.setField(self.use_dhcp, col=0, row=1, anchorLeft=1,
                                 padding=(0, 1, 0, 0))
        self.screenGrid.setField(self.gateway, col=0, row=2, anchorLeft=1,
                                 padding=(3, 0, 0, 0))
        self.screenGrid.setField(self.dns1, col=0, row=3, anchorLeft=1,
                                 padding=(3, 0, 0, 0))
        self.screenGrid.setField(self.dns2, col=0, row=4, anchorLeft=1,
                                 padding=(3, 0, 0, 0))
        self.screenGrid.setField(self.dns3, col=0, row=5, anchorLeft=1,
                                 padding=(3, 0, 0, 0))

        self.initializeFields()

        dhcpd = {'control': self.use_dhcp,
                 'disable': (self.gateway, self.dns1, self.dns2, self.dns3),
                 'enable': (self.gateway, self.dns1, self.dns2, self.dns3),
                 'invert': True}
        self.use_dhcp.setCallback(network.enabledByValue, [dhcpd])
        network.enabledByValue([dhcpd])

    def initializeFields(self):
        """
        Populate fields with data.
        """
        
        self.use_dhcp.setFlags(snack.FLAG_DISABLED, snack.FLAGS_RESET)

        try:
            if not self.netProfile['have_dhcp']:
                self.use_dhcp.setValue(' ')
                self.use_dhcp.setFlags(snack.FLAG_DISABLED, snack.FLAGS_SET)
            if not self.netProfile['gw_dns_use_dhcp']:
                self.use_dhcp.setValue(' ')
        except KeyError:
            pass

        try:
            self.gateway.setEntry(self.netProfile['default_gw'])
        except KeyError:
            self.gateway.setEntry('')

        try:
            self.dns1.setEntry(self.netProfile['dns1'])
        except KeyError:
            self.dns1.setEntry('')

        try:
            self.dns2.setEntry(self.netProfile['dns2'])
        except KeyError:
            self.dns2.setEntry('')

        try:
            self.dns3.setEntry(self.netProfile['dns3'])
        except KeyError:
            self.dns3.setEntry('')

    def validate(self):
        """
        Perform validity checks on received data.
        """

        if not self.use_dhcp.value():
            errList = []

            result, msg = self.gateway.verify()
            if result is None:
                errList.append(_('Default Gateway field is empty'))
            elif not result:
                errList.append(_('Default Gateway: ') + msg)

            # we only want to check this if valid IP is provided
            if result:
                result, msg = self.checkGatewayWithSubnets()
                if not result:
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

        return True, ''

    def checkGatewayWithSubnets(self):
        """
        Checks whether the provided default gateway is routable by an interface.
        """

        interfaces = network.retrieveNetworkContext(self.database)

        for intf in interfaces.keys():
            if not int(interfaces[intf]['configure']):
                continue
            if int(interfaces[intf]['use_dhcp']):
                return True, ''
            if kusutil.isHostRoutable(interfaces[intf]['ip_address'],
                                      interfaces[intf]['netmask'],
                                      self.gateway.value()):
                return True, ''

        return False, _('Not routable by any configured device.')

    def formAction(self):
        """
        Store the gateway settings.
        """

        self.netProfile['gw_dns_use_dhcp'] = bool(self.use_dhcp.value())
        self.netProfile['default_gw'] = self.gateway.value()
        self.netProfile['dns1'] = self.dns1.value()
        self.netProfile['dns2'] = self.dns2.value()
        self.netProfile['dns3'] = self.dns3.value()

        self.database.put(self.context, 'gw_dns_use_dhcp',
                          str(int(self.netProfile['gw_dns_use_dhcp'])))
        self.database.put(self.context, 'default_gw',
                          self.netProfile['default_gw'])
        self.database.put(self.context, 'dns1', self.netProfile['dns1'])
        self.database.put(self.context, 'dns2', self.netProfile['dns2'])
        self.database.put(self.context, 'dns3', self.netProfile['dns3'])

        if self.netProfile['gw_dns_use_dhcp']:
            kl.info('Set default gateway and DNS via DHCP.')
        else:
            kl.info('Set default gateway: %s, DNS 1-3: %s.' %
                    (self.netProfile['default_gw'],
                     ', '.join((self.netProfile['dns1'],
                                self.netProfile['dns2'],
                                self.netProfile['dns3']))))

        #self.kiprofile.update(self.kusuApp)

    def saveProfileToSQLCollection(db, context, profile):
        return True

    dbSaveFunctions = {'MySQL': None,
                       'SQLite': None,
                       'SQLColl': saveProfileToSQLCollection}
