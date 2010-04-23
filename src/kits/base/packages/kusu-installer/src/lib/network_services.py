#!/usr/bin/env python   
#
# $Id$
#
# Kusu Text Installer Network Services Screen.
#
# Copyright 2010 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.

import os
import socket
import snack
from gettext import gettext as _
from kusu.ui.text import kusuwidgets
import kusu.util.log as kusulog
from kusu.util import profile
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_NOTHING

kl = kusulog.getKusuLog('installer.network')

class NetworkServices(InstallerScreen, profile.PersistentProfile):
    """
    This screen selects whether the user wants to run dns/dhcp servers.
    """

    name = _('Network Services')
    profile = 'Network'
    msg = _('Please select network services: ')

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistentProfile.__init__(self, kiprofile)        

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """
        pass

    def validate(self):
        """
        Perform validity checks on received data.
        """
        return True, ''

    def drawImpl(self):
        """
        Draw the window.
        """

        self.screenGrid = snack.Grid(1, 3)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)

        self.dnsSelection = snack.Checkbox(_("Enable DNS Server on this machine ?"))
        self.dnsSelection.setValue('*')
        self.dhcpSelection = snack.Checkbox(_("Enable DHCP Server on this machine ?"))
        self.dhcpSelection.setValue('*')
        self.screenGrid.setField(self.dnsSelection, col=0, row=1,
                                 padding=(0, 1, 0, 0))
        self.screenGrid.setField(self.dhcpSelection, col=0, row=2,
                                 padding=(0, 1, 0, 0))

    def formAction(self):
        """
        Store the configurations options in the network profile.
        """

        try:
            self.kiprofile[self.profile]
        except KeyError:
            self.kiprofile[self.profile] = {}

        self.kiprofile[self.profile]['installer_dns'] = bool(self.dnsSelection.value())   
        self.kiprofile[self.profile]['installer_dhcp'] = bool(self.dhcpSelection.value())
  
    def rollback(self):
        self.formAction()

    def save(self, db, profile):
        dns = db.AppGlobals.selectfirst_by(kname='InstallerServeDNS')
        dhcp = db.AppGlobals.selectfirst_by(kname='InstallerServeDHCP')

        if profile['installer_dns']:
            dns.kvalue = '1'
        else:
            dns.kvalue = '0'

        if profile['installer_dhcp']:
            dhcp.kvalue = '1'
        else:
            dhcp.kvalue = '0'

        db.flush()


