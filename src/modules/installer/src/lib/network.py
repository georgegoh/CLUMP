#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Network Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.

import socket
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

        self.buttonsDict[_('Configure')].setCallback_(\
            ConfigureIntfScreen.configureIntf, (ConfigureIntfScreen(self), ))

class ConfigureIntfScreen:

    def __init__(self, baseScreen):
        self.baseScreen = baseScreen
        self.screen = baseScreen.screen
        self.selector = baseScreen.selector
        self.database = baseScreen.database
        self.context = baseScreen.context

    def configureIntf(self):
        # listbox stores interface names as string objects (ie 'eth0')
        self.intf = self.baseScreen.listbox.current()

        gridForm = snack.GridForm(self.screen,
                                   _('Configuring [%s]' % self.intf), 1, 3)

        # DHCP/activate on boot checkboxes
        self.use_dhcp = snack.Checkbox(_('Configure using DHCP'), isOn=1)
        self.active_on_boot = snack.Checkbox(_('Activate on boot'), isOn=1)

        # IP address/netmask text fields
        entryWidth = 22
        self.ip_address = kusuwidgets.LabelledEntry(labelTxt=_('IP Address '),
                                                    width=entryWidth)
        self.ip_address.addCheck(kusuwidgets.verifyIP)
        self.netmask = \
            kusuwidgets.LabelledEntry(labelTxt=_('Netmask '.rjust(11)),
                                      width=entryWidth)
        self.netmask.addCheck(kusuwidgets.verifyIP)

        # initialize fields with data from database or reasonable defaults
        self.populateIPs()

        subgrid = snack.Grid(1, 4)
        subgrid.setField(self.use_dhcp, 0, 0, (0, 1, 0, 1), anchorLeft=1)
        subgrid.setField(self.ip_address, 0, 1, anchorLeft=1)
        subgrid.setField(self.netmask, 0, 2, anchorLeft=1)
        subgrid.setField(self.active_on_boot, 0, 3, (0, 1, 0, 1), anchorLeft=1)
        gridForm.add(subgrid, 0, 1)

        # add OK and Cancel buttons
        ok_button = kusuwidgets.Button(_('OK'))
        cancel_button = kusuwidgets.Button(_('Cancel'))
        subgrid = snack.Grid(2, 1)
        subgrid.setField(ok_button, 0, 0, (0, 1, 1, 0))
        subgrid.setField(cancel_button, 1, 0, (0, 1, 0, 0))
        gridForm.add(subgrid, 0, 2)

        # add callback for toggling static IP fields
        self.use_dhcp.setCallback(enabledByValue, (self.use_dhcp,
                                   self.ip_address, self.netmask))
        enabledByValue((self.use_dhcp, self.ip_address, self.netmask))

        while True:
            # all done, draw and run
            gridForm.draw()
            exitCmd = gridForm.run()

            if exitCmd is ok_button:
                if self.configureIntfVerify():
                    self.configureIntfOK()
                    break

            if exitCmd is cancel_button:
                    break

        self.screen.popWindow()
        return NAV_NOTHING

    def configureIntfVerify(self):
        if self.use_dhcp.value():
            return True

        errList = []

        rv, msg = self.ip_address.verify()
        if rv is None:
            errList.append(_('IP address field is empty.'))
        elif not rv:
            errList.append(_('IP address: ') + msg)

        rv, msg = self.netmask.verify()
        if rv is None:
            errList.append(_('Netmask field is empty.'))
        elif not rv:
            errList.append(_('Netmask: ') + msg)

        if errList:
            errMsg = _('Please correct the following errors:')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i + 1) + '. ' + string
            self.selector.popupMsg(_('Error'), errMsg, height=10)
            return False

        return True

    def configureIntfOK(self):
        # verify IP and netmask fields

        # store information
        self.database.put(self.context, 'use_dhcp:' + self.intf,
                          str(self.use_dhcp.value()))
        self.database.put(self.context, 'active_on_boot:' + self.intf,
                          str(self.active_on_boot.value()))

        if not self.use_dhcp.value():
            self.database.put(self.context, 'ip_address:' + self.intf,
                              self.ip_address.value())
            self.database.put(self.context, 'netmask:' + self.intf,
                              self.netmask.value())

        # decide whether to show Gateway/DNS screen next
        self.controlDNSScreen()

    def controlDNSScreen(self):
        from gatewaydns import GatewayDNSSetupScreen
        dnsscreen = GatewayDNSSetupScreen(self.database,
                                          kusuApp=self.baseScreen.kusuApp)

        dnsscreen_exists = False
        for screen in self.selector.screens:
            if screen.name is dnsscreen.name:
                dnsscreen_exists = True
                dnsscreen = screen
                break

        # if no interfaces use DHCP, skip the Gateway/DNS screen
        using_dhcp = False
        network_entries = self.database.get(self.context)
        for network_entry in network_entries:
            if 'use_dhcp:' in network_entry[2] and network_entry[3] == u'1':
                # remove DNS screen if exists, since we won't be using it
                if dnsscreen_exists:
                    self.selector.screens.remove(dnsscreen)

                return

        # add the screen if it does not already exists
        if not dnsscreen_exists:
            self.selector.screens.insert(\
                self.selector.screens.index(self.baseScreen) + 1, dnsscreen)

    def populateIPs(self):
        """
        Populate fields with data from database or reasonable defaults.
        """
        
        network_entries = self.database.get(self.context)

        # defaults: DHCP & active on boot enabled, ip & netmask blank
        self.use_dhcp.setValue('*')
        self.active_on_boot.setValue('*')

        for network_entry in network_entries:
            if 'use_dhcp:' + self.intf in network_entry[2]:
                if network_entry[3] == u'1':
                    self.use_dhcp.setValue('*')
                else:
                    self.use_dhcp.setValue(' ')
            elif 'active_on_boot:' + self.intf in network_entry[2]:
                if network_entry[3] == u'1':
                    self.active_on_boot.setValue('*')
                else:
                    self.active_on_boot.setValie(' ')
            elif 'ip_address:' + self.intf in network_entry[2]:
                self.ip_address.setEntry(network_entry[3])
            elif 'netmask:' + self.intf in network_entry[2]:
                self.netmask.setEntry(network_entry[3])

def enabledByValue(args):
    """
    Sets the enabled bit of widgets based on value of controlling widget.

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
