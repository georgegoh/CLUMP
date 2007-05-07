#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Network Screen.
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
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
from kusu.hardware import net

NAV_NOTHING = -1

class NetworkScreen(screenfactory.BaseScreen):
    """This is the network screen."""

    name = _('Network')
    context = 'Network'
    msg = _('Please configure your network')
    buttons = [_('Configure')]

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)

        self.listbox = snack.Listbox(8, scroll=1, returnExit=1)
        for intf, v in net.getInterfaces().items():
            if v['isPhysical']:
                vendor = v['vendor']
                device = v['device']
                entrystr = '%s - %s %s' % (intf, vendor, device)
                self.listbox.append(entrystr[:50], intf)

        self.screenGrid.setField(self.listbox, col=0, row=1,
                                 padding=(0, 1, 0, -1))

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """

        self.buttonsDict[_('Configure')].setCallback_(self.configureIntf)

    def configureIntf(self):
        # listbox stores interface names as string objects (ie 'eth0')
        intf = self.listbox.current()

        gridForm = snack.GridForm(self.screen,
                                   _('Configuring [%s]' % intf), 1, 3)

        # DHCP/activate on boot checkboxes
        use_dhcp = snack.Checkbox(_('Configure using DHCP'), isOn=1)
        active_on_boot = snack.Checkbox(_('Activate on boot'), isOn=1)

        # IP address/netmask text fields
        entryWidth = 22
        ip_address = kusuwidgets.LabelledEntry(labelTxt=_('IP Address '),
                                               width=entryWidth)
        ip_address.addCheck(kusuwidgets.verifyIP)
        netmask = kusuwidgets.LabelledEntry(labelTxt=_('Netmask '.rjust(11)),
                                            width=entryWidth)
        netmask.addCheck(kusuwidgets.verifyIP)

        # initialize fields with data from database or reasonable defaults
        self.populateIPs(intf, use_dhcp, active_on_boot, ip_address, netmask)

        subgrid = snack.Grid(1, 4)
        subgrid.setField(use_dhcp, 0, 0, (0, 1, 0, 1), anchorLeft=1)
        subgrid.setField(ip_address, 0, 1, anchorLeft=1)
        subgrid.setField(netmask, 0, 2, anchorLeft=1)
        subgrid.setField(active_on_boot, 0, 3, (0, 1, 0, 1), anchorLeft=1)
        gridForm.add(subgrid, 0, 1)

        # add OK and Cancel buttons
        ok_button = kusuwidgets.Button(_('OK'))
        cancel_button = kusuwidgets.Button(_('Cancel'))
        subgrid = snack.Grid(2, 1)
        subgrid.setField(ok_button, 0, 0, (0, 1, 1, 0))
        subgrid.setField(cancel_button, 1, 0, (0, 1, 0, 0))
        gridForm.add(subgrid, 0, 2)

        # add callback for toggling static IP fields
        use_dhcp.setCallback(toggleEnabled, (use_dhcp, ip_address, netmask))
        toggleEnabled((use_dhcp, ip_address, netmask))

        # all done, draw and run
        gridForm.draw()
        exitCmd = gridForm.run()
        self.screen.popWindow()

        if exitCmd is ok_button:
            # store information
            pass

        return NAV_NOTHING

    def populateIPs(self, intf, use_dhcp, active_on_boot, ip_address, netmask):
        """
        Populate fields with data from database or reasonable defaults.
        """

        use_dhcp.setValue('*')
        active_on_boot.setValue('*')
        ip_address.setEntry('192.168.1.50')
        netmask.setEntry('255.255.255.0')

def toggleEnabled(args):
    """
    Toggles the enabled bit of widgets based on value of controlling widget.

    args -- a tuple of arguments. The first argument's value will be checked,
            all other arguments will be set accordingly.
    """

    control = args[0]
    if control.value():
        for arg in args[1:]:
            arg.setEnabled(False)
    else:
        for arg in args[1:]:
            arg.setEnabled(True)
