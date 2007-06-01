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
from kusu.util.verify import *
import kusu.util.log as kusulog
from kusu.util import profile
NAV_NOTHING = -1

kl = kusulog.getKusuLog('installer.network')

class GatewayDNSSetupScreen(screenfactory.BaseScreen, profile.PersistantProfile):
    """This screen asks for DNS and Gateway setups."""

    name = _('Gateway & DNS')
    profile = 'Network'
    netProfile = None   # we assign the Network profile to this local variable
    msg = _('Please configure your Gateway/DNS settings')
    buttons = [_('Clear All')]

    def __init__(self, kiprofile):
        screenfactory.BaseScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistantProfile.__init__(self, kiprofile)        

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
        if not self.kiprofile.has_key(self.profile): self.setDefaults()
        self.netProfile = self.kiprofile[self.profile]

        self.screenGrid = snack.Grid(1, 6)
        entryWidth = 28

        self.use_dhcp = snack.Checkbox(_('Use DHCP'), isOn=1)

        self.gateway = kusuwidgets.LabelledEntry(
                                   labelTxt=_('Default Gateway ').rjust(24), 
                                   width=entryWidth)
        self.gateway.addCheck(verifyIP)

        self.dns1 = kusuwidgets.LabelledEntry(
                                    labelTxt=_('DNS Server 1 ').rjust(24),
                                    width=entryWidth)
        self.dns1.addCheck(verifyIP)

        self.dns2 = kusuwidgets.LabelledEntry(
                            labelTxt=_('DNS Server 2 (optional) ').rjust(24),
                            width=entryWidth)
        self.dns2.addCheck(verifyIP)

        self.dns3 = kusuwidgets.LabelledEntry(
                            labelTxt=_('DNS Server 3 (optional) ').rjust(24), 
                            width=entryWidth)
        self.dns3.addCheck(verifyIP)

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
        
        # enable the use_dhcp checkbox, if no dhcp configured, disable it
        self.use_dhcp.setFlags(snack.FLAG_DISABLED, snack.FLAGS_RESET)

        try:
            if not self.netProfile['have_dhcp']:
                self.use_dhcp.setValue(' ')
                self.use_dhcp.setFlags(snack.FLAG_DISABLED, snack.FLAGS_SET)
            if not self.netProfile['gw_dns_use_dhcp']:
                self.use_dhcp.setValue(' ')
        except KeyError:
            pass

        # try to set field with data, or leave blank if no data
        try:
            self.gateway.setEntry(self.netProfile['default_gw'])
        except KeyError:
            pass

        try:
            self.dns1.setEntry(self.netProfile['dns1'])
        except KeyError:
            pass

        try:
            self.dns2.setEntry(self.netProfile['dns2'])
        except KeyError:
            pass

        try:
            self.dns3.setEntry(self.netProfile['dns3'])
        except KeyError:
            pass

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

        if self.kiprofile[self.profile]['have_dhcp']:
            return True, ''

        interfaces = self.kiprofile[self.profile]['interfaces']

        for intf in interfaces.keys():
            if interfaces[intf]['configure']:
                if isHostRoutable(interfaces[intf]['ip_address'],
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

    def save(self, db, profile, kiprofile):
        pass

    def restore(self, db, profile, kiprofile):
        pass

    def restoreProfileFromSQLCollection(db, context, kiprofile):
        """
        Reads data from SQLiteCollection db according to context and fills
        profile.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db and profile
        kiprofile -- the complete profile (a dictionary) which we fill in
        """

        profile = {}
        profile['gw_dns_use_dhcp'] = True
        profile['default_gw'] = ''
        profile['dns1'] = ''
        profile['dns2'] = ''
        profile['dns3'] = ''

        data = db.get(context, 'gw_dns_use_dhcp')
        if data:
            profile['gw_dns_use_dhcp'] = bool(int(data[0]))

        if profile['gw_dns_use_dhcp']:
            kl.info('Read default gateway and DNS is determined via DHCP')
        else:
            data = db.get(context, 'default_gw')
            if data:
                profile['default_gw'] = data[0]

            data = db.get(context, 'dns1')
            if data:
                profile['dns1'] = data[0]

            data = db.get(context, 'dns2')
            if data:
                profile['dns2'] = data[0]

            data = db.get(context, 'dns3')
            if data:
                profile['dns3'] = data[0]

            kl.info('Read default gateway: %s, DNS 1-3: %s' %
                    (profile['default_gw'], ', '.join((profile['dns1'],
                                                       profile['dns2'],
                                                       profile['dns3']))))

        # need to update because network screen already assigned
        kiprofile[context].update(profile)

        return True

    def saveProfileToSQLCollection(db, context, kiprofile):
        """
        Writes data from profile to SQLiteCollection db according to context.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db and profile
        kiprofile -- the profile (a dictionary) with data to commit
        """

        profile = kiprofile[context]
        db.put(context, 'gw_dns_use_dhcp',
               str(int(profile['gw_dns_use_dhcp'])))

        if profile['gw_dns_use_dhcp']:
            kl.info('Set default gateway and DNS via DHCP')
        else:
            db.put(context, 'default_gw', profile['default_gw'])
            db.put(context, 'dns1', profile['dns1'])
            db.put(context, 'dns2', profile['dns2'])
            db.put(context, 'dns3', profile['dns3'])

            kl.info('Set default gateway: %s, DNS 1-3: %s' %
                    (profile['default_gw'], ', '.join((profile['dns1'],
                                                       profile['dns2'],
                                                       profile['dns3']))))

        return True

