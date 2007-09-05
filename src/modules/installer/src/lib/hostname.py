#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Host Name Setup Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.

import snack
from gettext import gettext as _
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
from kusu.installer import network
from kusu.util.verify import *
import kusu.util.log as kusulog
from kusu.util import profile
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_NOTHING

kl = kusulog.getKusuLog('installer.network')

DEFAULT_DNSZONE = 'kusu'

class FQHNScreen(InstallerScreen, profile.PersistentProfile):
    """Collects fully-qualified host name."""

    name = _('Host Name')
    profile = 'Network'
    netProfile = None   # we assign the Network profile to this local variable
    msg = _('Please specify the host name and DNS zone for this computer:')
    buttons = [_('Clear All')]

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistentProfile.__init__(self, kiprofile)

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
            self.netProfile['fqhn_host'] = ''
            self.netProfile['fqhn_domain'] = ''
        return NAV_NOTHING

    def drawImpl(self):
        """
        Draw the window.
        """

        if not self.kiprofile.has_key(self.profile): self.setDefaults()
        self.netProfile = self.kiprofile[self.profile]

        ### Removing DHCP temporarily, fix in KUSU-207
        #self.screenGrid = snack.Grid(1, 4)
        self.screenGrid = snack.Grid(1, 3)
        ###
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
                    labelTxt=_('Host Name '), width=entryWidth)
        self.hostname.addCheck(verifyFQDN)
        self.domain = kusuwidgets.LabelledEntry(
                    labelTxt=_('DNS Zone '), width=entryWidth)
        self.domain.addCheck(verifyFQDN)

        self.hostname.setEntry(self.netProfile.get('fqhn_host',
                                                   self.defaultname))
        self.domain.setEntry(self.netProfile.get('fqhn_domain',
                                                 self.defaultzone))

        dhcpd = {'control': self.use_dhcp,
                 'disable': (self.hostname, self.domain),
                 'enable': (self.hostname, self.domain),
                 'invert': True}
        self.use_dhcp.setCallback(network.enabledByValue, [dhcpd])
        network.enabledByValue([dhcpd])

        self.screenGrid.setField(snack.TextboxReflowed(text=self.msg,
                                                       width=self.gridWidth),
                                 col=0, row=0, anchorLeft=1)
        ### Removing DHCP temporarily, fix in KUSU-207
        self.screenGrid.setField(self.hostname, col=0, row=1,
                                 padding=(3, 1, 0, 0), anchorLeft=1)
        self.screenGrid.setField(self.domain, col=0, row=2,
                                 padding=(4, 0, 0, 2), anchorLeft=1)
        #self.screenGrid.setField(self.use_dhcp, col=0, row=1,
        #                         padding=(0, 1, 0, 0), anchorLeft=1)
        #self.screenGrid.setField(self.hostname, col=0, row=2,
        #                         padding=(3, 0, 0, 0), anchorLeft=1)
        #self.screenGrid.setField(self.domain, col=0, row=3,
        #                         padding=(4, 0, 0, 1), anchorLeft=1)
        ###

    def validate(self):
        """
        Perform validity checks on received data.
        """

        if not self.use_dhcp.value():
            errList = []

            rv, msg = self.hostname.verify()
            if rv is None:
                errList.append(_('Host Name field is empty'))
            elif not rv:
                errList.append(_('Host Name: ') + msg)

            rv, msg = self.domain.verify()
            if rv is None:
                errList.append(_('DNS Zone field is empty'))
            elif not rv:
                errList.append(_('DNS Zone: ') + msg)

            if errList:
                errMsg = _('Please correct the following errors:')
                for i, string in enumerate(errList):
                    errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
                return False, errMsg

        return True, ''

    def formAction(self):
        """
        Store the gateway settings.
        """

        self.netProfile['fqhn_use_dhcp'] = bool(self.use_dhcp.value())
        self.netProfile['fqhn_host'] = self.hostname.value()
        self.netProfile['fqhn_domain'] = self.domain.value()

    def setDefaults(self):
        db = self.kiprofile.getDatabase()

        dnsdomain = db.AppGlobals(kname='DNSZone', kvalue=DEFAULT_DNSZONE)
        db.flush()

        installerng = db.NodeGroups.selectfirst_by(type='installer')
        mastername = db.Nodes.selectfirst_by(ngid=installerng.ngid).name

        self.defaultname = mastername
        self.defaultzone = dnsdomain.kvalue

    def save(self, db, profile):
        if not profile['fqhn_use_dhcp']:
            if profile['fqhn_domain']:
                dnsdomain = db.AppGlobals.selectfirst_by(kname='DNSZone')
                dnsdomain.kvalue = profile['fqhn_domain']

            primaryinstaller = \
                db.AppGlobals.selectfirst_by(kname='PrimaryInstaller')
            primaryinstaller.kvalue = self.netProfile['fqhn_host']

            installerng = db.NodeGroups.selectfirst_by(type='installer')
            master = db.Nodes.selectfirst_by(ngid=installerng.ngid)
            master.name = self.netProfile['fqhn_host']

            db.flush()
