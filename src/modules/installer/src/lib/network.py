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
import kusu.util.log as kusulog

NAV_NOTHING = -1

kl = kusulog.getKusuLog('installer.network')

class NetworkScreen(screenfactory.BaseScreen):
    """This is the network screen."""

    name = _('Network')
    context = 'Network'
    msg = _('Please configure your network')
    buttons = [_('Configure')]
    interfaces = {}

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """

        self.buttonsDict[_('Configure')].setCallback_(\
            ConfigureIntfScreen.configureIntf, (ConfigureIntfScreen(self), ))

    def formAction(self):
        """
        Write self.interfaces dictionary to database.
        """

        kl.info('Writing to DB: %s' % self.interfaces)

        for intf in self.interfaces.keys():
            # store information
            if self.interfaces[intf]['use_dhcp']:
                self.database.put(self.context, 'use_dhcp:' + intf, u'1')
            else:
                self.database.put(self.context, 'use_dhcp:' + intf, u'0')

            if self.interfaces[intf]['active_on_boot']:
                self.database.put(self.context, 'active_on_boot:' + intf, u'1')
            else:
                self.database.put(self.context, 'active_on_boot:' + intf, u'0')
                                  
            if not self.interfaces[intf]['use_dhcp']:
                self.database.put(self.context, 'ip_address:' + intf,
                                  self.interfaces[intf]['ip_address'])
                self.database.put(self.context, 'netmask:' + intf,
                                  self.interfaces[intf]['netmask'])

    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 2)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)

        self.listbox = snack.Listbox(8, scroll=1, returnExit=1)

        initial_view = False
        # returning from Configure screen provides a filled-in self.interfaces
        if not self.interfaces:
            # we get a dictionary
            self.interfaces = retrieveNetworkContext(self.database)
            initial_view = True

        # we want interfaces in alphabetical order
        intfs = self.interfaces.keys()
        intfs.sort()

        for intf in intfs:
            # DHCP config for first interface
            if initial_view and len(intfs) and intf == intfs[0]:
                self.interfaces[intf]['use_dhcp'] = True
                self.interfaces[intf]['active_on_boot'] = True

            # static IP for second interface
            if initial_view and len(intfs) > 1 and intf == intfs[1]:
                self.interfaces[intf]['use_dhcp'] = False
                self.interfaces[intf]['hostname'] = 'cluster-' + intf
                self.interfaces[intf]['ip_address'] = '172.20.0.1'
                self.interfaces[intf]['netmask'] = '255.255.0.0'
                self.interfaces[intf]['active_on_boot'] = True

            entrystr = '<Unconfigured>'
            if self.interfaces[intf]['use_dhcp']:
                entrystr = '<DHCP>'
            # we check against false to account for unconfigured adapter
            elif self.interfaces[intf]['use_dhcp'] is False:
                entrystr = self.interfaces[intf]['ip_address'] + '/' + \
                           self.interfaces[intf]['netmask'] + ' <' + \
                           self.interfaces[intf]['hostname'] + '>'
            entrystr = intf + ' ' + entrystr

            kl.debug('Adding interface: %s' % self.interfaces[intf])
            self.listbox.append(entrystr[:50], intf)

        self.screenGrid.setField(self.listbox, col=0, row=1,
                                 padding=(0, 1, 0, -1))

class ConfigureIntfScreen:

    def __init__(self, baseScreen):
        self.baseScreen = baseScreen
        self.screen = baseScreen.screen
        self.selector = baseScreen.selector
        self.context = baseScreen.context

    def configureIntf(self):
        # listbox stores interface names as string objects (ie 'eth0')
        self.intf = self.baseScreen.listbox.current()

        gridForm = snack.GridForm(self.screen,
                                  _('Configuring [%s]' % self.intf), 1, 3)

        interfaces = self.baseScreen.interfaces
        device = snack.Textbox(40, 1, 'Device: ' + self.intf)
        vendor = snack.Textbox(40, 1,
                               'Vendor: ' + interfaces[self.intf]['vendor'])
        model = snack.Textbox(40, 1,
                              'Model: ' + interfaces[self.intf]['device'])
        module = snack.Textbox(40, 1,
                               'Module: ' + interfaces[self.intf]['module'])

        subgrid = snack.Grid(1, 4)
        subgrid.setField(device, 0, 0, anchorLeft=1)
        subgrid.setField(vendor, 0, 1, anchorLeft=1)
        subgrid.setField(model, 0, 2, anchorLeft=1)
        subgrid.setField(module, 0, 3, anchorLeft=1)
        gridForm.add(subgrid, 0, 0)

        # DHCP/activate on boot checkboxes
        self.use_dhcp = snack.Checkbox(_('Configure using DHCP'))
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
        self.hostname = \
            kusuwidgets.LabelledEntry(labelTxt=_('Host name '.rjust(11)),
                                                  width=entryWidth)

        # initialize fields
        self.populateIPs()

        subgrid = snack.Grid(1, 5)
        subgrid.setField(self.use_dhcp, 0, 0, (0, 1, 0, 1), anchorLeft=1)
        subgrid.setField(self.hostname, 0, 1, anchorLeft=1)
        subgrid.setField(self.ip_address, 0, 2, anchorLeft=1)
        subgrid.setField(self.netmask, 0, 3, anchorLeft=1)
        subgrid.setField(self.active_on_boot, 0, 4, (0, 1, 0, 1), anchorLeft=1)
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
                                  self.hostname, self.ip_address, self.netmask))
        enabledByValue((self.use_dhcp,
                        self.hostname, self.ip_address, self.netmask))

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
        interfaces = self.baseScreen.interfaces

        if self.use_dhcp.value():
            interfaces[self.intf]['use_dhcp'] = True
        else:
            interfaces[self.intf]['use_dhcp'] = False

        if self.active_on_boot.value():
            interfaces[self.intf]['active_on_boot'] = True
        else:
            interfaces[self.intf]['active_on_boot'] = False

        interfaces[self.intf]['hostname'] = self.hostname.value()
        interfaces[self.intf]['ip_address'] = self.ip_address.value()
        interfaces[self.intf]['netmask'] = self.netmask.value()

        # decide whether to show Gateway/DNS screen next
        self.controlDNSScreen()

    def controlDNSScreen(self):
        from gatewaydns import GatewayDNSSetupScreen
        dnsscreen = GatewayDNSSetupScreen(self.baseScreen.database,
                                          kusuApp=self.baseScreen.kusuApp)

        dnsscreen_exists = False
        for screen in self.selector.screens:
            if screen.name is dnsscreen.name:
                dnsscreen_exists = True
                dnsscreen = screen
                break

        interfaces = self.baseScreen.interfaces

        # if any interface uses DHCP, skip the Gateway/DNS screen
        using_dhcp = False
        for intf in interfaces.keys():
            if interfaces[intf]['use_dhcp']:
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
        Populate fields with data.
        """
        
        interfaces = self.baseScreen.interfaces

        if interfaces[self.intf]['use_dhcp']:
            self.use_dhcp.setValue('*')
        else:
            self.use_dhcp.setValue(' ')

        if interfaces[self.intf]['active_on_boot']:
            self.active_on_boot.setValue('*')
        else:
            self.active_on_boot.setValue(' ')

        self.hostname.setEntry(interfaces[self.intf]['hostname'])
        self.ip_address.setEntry(interfaces[self.intf]['ip_address'])
        self.netmask.setEntry(interfaces[self.intf]['netmask'])

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

def retrieveNetworkContext(db):
    interfaces = net.getPhysicalInterfaces()    # we get a dictionary
    network_entries = db.get('Network')

    adapters = {}
    for network_entry in network_entries:
        # properties stored in format property:adapter
        # ie: use_dhcp:eth0
        prop = network_entry[2].split(':')
        if len(prop) > 1:
            try: 
                adapters[prop[1]][prop[0]] = network_entry[3]
            except KeyError:
                adapters[prop[1]] = {}
                adapters[prop[1]][prop[0]] = network_entry[3]

    kl.info('Adapters in DB: %s' % adapters)
    
    for intf in interfaces.keys():
        # default to using DHCP and active on boot
        interfaces[intf].update({'use_dhcp': '',
                                 'hostname': '',
                                 'ip_address': '',
                                 'netmask': '',
                                 'active_on_boot': ''})

        try:
            interfaces[intf].update(adapters[intf])
        except KeyError:
            # this interface has not been configured
            pass

    # SQLite stores these values as unicode strings
    for intf in interfaces.keys():
        # if use_dhcp not in the DB, leave as is for unconfigured interfaces
        if interfaces[intf]['use_dhcp'] == u'1':
            interfaces[intf]['use_dhcp'] = True
        elif interfaces[intf]['use_dhcp'] == u'0':
            interfaces[intf]['use_dhcp'] = False

        if interfaces[intf]['active_on_boot'] == u'1':
            interfaces[intf]['active_on_boot'] = True
        else:
            interfaces[intf]['active_on_boot'] = False

    return interfaces
