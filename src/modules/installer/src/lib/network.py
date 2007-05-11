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
from kusu.hardware import net
import kusu.util.log as kusulog
import kusu.util.util as kusutil

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

        try:
            self.kusuApp['netProfile']
        except KeyError:
            self.kusuApp['netProfile'] = {}

        self.kusuApp['netProfile']['have_dhcp'] = False
        self.kusuApp['netProfile']['have_static'] = False

        for intf in self.interfaces.keys():
            # store information
            # these are bools, we do str(int(bool)) to convert True to '1'
            # and False to '0'
            if self.interfaces[intf]['configure'] == '':
                self.interfaces[intf]['configure'] = False

            if self.interfaces[intf]['configure']:
                if self.interfaces[intf]['use_dhcp']:
                    self.kusuApp['netProfile']['have_dhcp'] = True
                else:
                    self.kusuApp['netProfile']['have_static'] = True

            self.database.put(self.context, 'configure:' + intf,
                              str(int(self.interfaces[intf]['configure'])))
            self.database.put(self.context, 'use_dhcp:' + intf,
                              str(int(self.interfaces[intf]['use_dhcp'])))
            self.database.put(self.context, 'active_on_boot:' + intf,
                              str(int(self.interfaces[intf]['active_on_boot'])))

            if not self.interfaces[intf]['use_dhcp']:
                self.database.put(self.context, 'hostname:' + intf,
                                  self.interfaces[intf]['hostname'])
                self.database.put(self.context, 'ip_address:' + intf,
                                  self.interfaces[intf]['ip_address'])
                self.database.put(self.context, 'netmask:' + intf,
                                  self.interfaces[intf]['netmask'])

            kl.info('Wrote to DB %s: %s' % (intf, self.interfaces[intf]))

        self.kusuApp['netProfile']['interfaces'] = self.interfaces

    def validate(self):
        errList = [] 

        rv, dups = self.checkDuplicates('ip_address')
        if not rv:
            msg = _('Identical IP %s %s assigned to more than one interface.')
            if len(dups) > 1:
                errList.append(msg % ('addresses',
                               ', '.join(dups[:len(dups) - 1]) +
                               ' and %s' % dups[len(dups) - 1]))
            else:
                errList.append(msg % ('address', dups[0]))

        rv, dups = self.checkDuplicates('hostname')
        if not rv:
            msg = _('Identical %s %s assigned to more than one interface.')
            if len(dups) > 1:
                errList.append(msg % ('host names',
                               ', '.join(dups[:len(dups) - 1]) +
                               ' and %s' % dups[len(dups) - 1]))
            else:
                errList.append(msg % ('host name', dups[0]))

        if errList:
            errMsg = _('Please correct the following errors:')
            for i, string in enumerate(errList):
                errMsg = errMsg + '\n\n' + str(i+1) + '. ' + string
            return False, errMsg

        return True, ''

    def checkDuplicates(self, prop):
        if len(self.interfaces) <= 1:
            return True, []

        dup_props = []
        props = []

        for intf in self.interfaces.keys():
            if self.interfaces[intf]['configure'] \
                and not self.interfaces[intf]['use_dhcp'] \
                and self.interfaces[intf][prop] not in dup_props:
                if self.interfaces[intf][prop] in props:
                    dup_props.append(self.interfaces[intf][prop])
                else:
                    props.append(self.interfaces[intf][prop])

        if dup_props:
            return False, dup_props

        return True, []
 
    def drawImpl(self):
        self.screenGrid = snack.Grid(1, 3)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)

        initial_view = False
        # returning from Configure screen provides a filled-in self.interfaces
        if not self.interfaces:
            # we get a dictionary
            self.interfaces = retrieveNetworkContext(self.database)

            for intf in self.interfaces.keys():
                try:
                    if self.interfaces[intf]['first_seen']:
                        self.interfaces[intf]['configure'] = ''
                except KeyError:
                    pass

        # we want interfaces in alphabetical order
        intfs = self.interfaces.keys()
        intfs.sort()

        self.listbox = snack.Listbox(6, scroll=1, returnExit=1, width=55)

        for intf in intfs:
            # DHCP config for first interface
            if len(intfs) and intf == intfs[0] \
                and self.interfaces[intf]['configure'] == '':
                self.interfaces[intf]['configure'] = True
                self.interfaces[intf]['use_dhcp'] = True
                self.interfaces[intf]['active_on_boot'] = True

            # static IP for second interface
            if len(intfs) > 1 and intf == intfs[1] \
                and self.interfaces[intf]['configure'] == '':
                self.interfaces[intf]['configure'] = True
                self.interfaces[intf]['use_dhcp'] = False
                self.interfaces[intf]['hostname'] = 'cluster-' + intf
                self.interfaces[intf]['ip_address'] = '172.20.0.1'
                self.interfaces[intf]['netmask'] = '255.255.0.0'
                self.interfaces[intf]['active_on_boot'] = True

            entrystr = '  ' + intf + ' not configured'
            if self.interfaces[intf]['configure']:
                if self.interfaces[intf]['use_dhcp']:
                    entrystr = 'DHCP'
                else:
                    entrystr = self.interfaces[intf]['ip_address'] + '/' + \
                               self.interfaces[intf]['netmask'] + ' ' + \
                               self.interfaces[intf]['hostname']

                if self.interfaces[intf]['active_on_boot']:
                    entrystr = '* ' + intf + ' ' + entrystr
                else:
                    entrystr = '  ' + intf + ' ' + entrystr

            kl.debug('Adding interface %s: %s' % (intf, self.interfaces[intf]))
            self.listbox.append(entrystr[:50], intf)

        self.screenGrid.setField(self.listbox, col=0, row=1,
                                 padding=(0, 1, 0, 0))

        footnote = '* Activate interface on boot'
        footnote = snack.Textbox(len(footnote), 1, footnote)
        self.screenGrid.setField(footnote, 0, 2, padding=(0, 0, 0, -1))

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
                                  _('Configuring [%s]' % self.intf), 1, 4)

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

        self.configdevice = snack.Checkbox(_('Configure this device'))

        gridForm.add(self.configdevice, 0, 1,
                     padding=(0, 1, 0, 0), anchorLeft=1)

        # DHCP/activate on boot checkboxes
        self.use_dhcp = snack.Checkbox(_('Use DHCP'))
        self.active_on_boot = snack.Checkbox(_('Activate on boot'))

        # IP address/netmask text fields
        entryWidth = 22
        self.ip_address = kusuwidgets.LabelledEntry(labelTxt=_('IP Address '),
                                                    width=entryWidth)
        self.ip_address.addCheck(kusutil.verifyIP)
        self.netmask = \
            kusuwidgets.LabelledEntry(labelTxt=_('Netmask '.rjust(11)),
                                      width=entryWidth)
        self.netmask.addCheck(kusutil.verifyIP)
        self.hostname = \
            kusuwidgets.LabelledEntry(labelTxt=_('Host name '.rjust(11)),
                                                  width=entryWidth)
        self.hostname.addCheck(kusutil.verifyHostname)

        # initialize fields
        self.populateIPs()

        subgrid = snack.Grid(1, 5)
        subgrid.setField(self.use_dhcp, 0, 0, (0, 0, 0, 1), anchorLeft=1)
        subgrid.setField(self.hostname, 0, 1, anchorLeft=1)
        subgrid.setField(self.ip_address, 0, 2, anchorLeft=1)
        subgrid.setField(self.netmask, 0, 3, anchorLeft=1)
        subgrid.setField(self.active_on_boot, 0, 4, (0, 1, 0, 0), anchorLeft=1)
        gridForm.add(subgrid, 0, 2)

        # add OK and Cancel buttons
        ok_button = kusuwidgets.Button(_('OK'))
        cancel_button = kusuwidgets.Button(_('Cancel'))
        subgrid = snack.Grid(2, 1)
        subgrid.setField(ok_button, 0, 0, (0, 1, 1, 0))
        subgrid.setField(cancel_button, 1, 0, (0, 1, 0, 0))
        gridForm.add(subgrid, 0, 3)

        self.addCheckboxCallbacks()

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

    def addCheckboxCallbacks(self):
        # add callback for toggling static IP fields
        configd = {'control': self.configdevice,
                   'disable': (self.use_dhcp, self.active_on_boot,
                                self.hostname, self.ip_address, self.netmask),
                   'enable': (self.use_dhcp, self.active_on_boot),
                   'invert': False}
        dhcpd = {'control': self.use_dhcp,
                 'disable': (self.hostname, self.ip_address, self.netmask),
                 'enable': (self.hostname, self.ip_address, self.netmask),
                 'invert': True}

        self.configdevice.setCallback(enabledByValue, [dhcpd, configd])
        self.use_dhcp.setCallback(enabledByValue, [dhcpd])

        enabledByValue([dhcpd, configd])

    def configureIntfVerify(self):
        if self.use_dhcp.value():
            return True

        errList = []

        rv, msg = self.hostname.verify()
        if rv is None:
            errList.append(_('Host name is empty.'))
        elif not rv:
            errList.append(msg)

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
            self.selector.popupMsg(_('Error'), errMsg)
            return False

        return True

    def configureIntfOK(self):
        interfaces = self.baseScreen.interfaces

        interfaces[self.intf]['configure'] = bool(self.configdevice.value())
        interfaces[self.intf]['use_dhcp'] = bool(self.use_dhcp.value())
        interfaces[self.intf]['active_on_boot'] = \
                                            bool(self.active_on_boot.value())

        interfaces[self.intf]['hostname'] = self.hostname.value()
        interfaces[self.intf]['ip_address'] = self.ip_address.value()
        interfaces[self.intf]['netmask'] = self.netmask.value()

        # decide whether to show Gateway/DNS screen next
        #self.controlDNSScreen()

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

        if interfaces[self.intf]['configure']:
            self.configdevice.setValue('*')
        else:
            self.configdevice.setValue(' ')

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

    for d in args:
        control = d['control']

        if bool(control.value()) ^ d['invert']:
            for subject in d['enable']:
                if isinstance(subject, kusuwidgets.LabelledEntry):
                    subject.setEnabled(True)
                elif isinstance(subject, snack.Checkbox):
                    subject.setFlags(snack.FLAG_DISABLED, snack.FLAGS_RESET)
        else:
            for subject in d['disable']:
                if isinstance(subject, kusuwidgets.LabelledEntry):
                    subject.setEnabled(False)
                elif isinstance(subject, snack.Checkbox):
                    subject.setFlags(snack.FLAG_DISABLED, snack.FLAGS_SET)

def retrieveNetworkContext(db):
    adapters = {}
    network_entries = db.get('Network')
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
    
    interfaces = net.getPhysicalInterfaces()    # we get a dictionary
    for intf in interfaces.keys():
        # default to using DHCP and active on boot
        interfaces[intf].update({'configure': '',
                                 'use_dhcp': '',
                                 'hostname': '',
                                 'ip_address': '',
                                 'netmask': '',
                                 'active_on_boot': ''})

        try:
            interfaces[intf].update(adapters[intf])
        except KeyError:
            interfaces[intf]['first_seen'] = True

    # SQLite stores these values as unicode strings
    for intf in interfaces.keys():
        # if use_dhcp or configure not in the DB,
        # leave as is for unconfigured interfaces
        if interfaces[intf]['configure'] == u'1':
            interfaces[intf]['configure'] = True
        else:
            interfaces[intf]['configure'] = False

        if interfaces[intf]['use_dhcp'] == u'1':
            interfaces[intf]['use_dhcp'] = True
        else:
            interfaces[intf]['use_dhcp'] = False

        if interfaces[intf]['active_on_boot'] == u'1':
            interfaces[intf]['active_on_boot'] = True
        else:
            interfaces[intf]['active_on_boot'] = False

    return interfaces
