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
from kusu.hardware import probe
import kusu.util.log as kusulog
from kusu.util.verify import *
from kusu.util.errors import *

NAV_NOTHING = -1

kl = kusulog.getKusuLog('installer.network')

class NetworkScreen(screenfactory.BaseScreen):
    """
    The network screen lists all available network interfaces and provides
    their configuration.
    """

    name = _('Network')
    context = 'Network'
    profile = context
    msg = _('Please configure your network')
    buttons = [_('Configure')]

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """

        self.buttonsDict[_('Configure')].setCallback_(\
            ConfigureIntfScreen.configureIntf, (ConfigureIntfScreen(self), ))

    def formAction(self):
        """
        Store the configurations options in the network profile.
        """

        try:
            self.kiprofile[self.profile]
        except KeyError:
            self.kiprofile[self.profile] = {}

        self.kiprofile[self.profile]['have_dhcp'] = False
        self.kiprofile[self.profile]['have_static'] = False

        interfaces = self.kiprofile[self.profile]['interfaces']
        for intf in interfaces:
            if interfaces[intf]['configure']:
                if interfaces[intf]['use_dhcp']:
                    self.kiprofile[self.profile]['have_dhcp'] = True
                else:
                    self.kiprofile[self.profile]['have_static'] = True

        # decide whether to show Gateway/DNS screen next
        self.controlDNSScreen()

    def controlDNSScreen(self):
        """
        Dynamically insert or remove Gateway/DNS screen based on configuration
        of network interfaces.
        """

        from gatewaydns import GatewayDNSSetupScreen
        dnsscreen = GatewayDNSSetupScreen(self.database, None,
                                          self.kiprofile)

        dnsscreen_exists = False
        for screen in self.selector.screens:
            if screen.name is dnsscreen.name:
                dnsscreen_exists = True
                dnsscreen = screen
                break

        # if no interfaces are configured (or none exist), remove dns screen
        if dnsscreen_exists \
            and not self.kiprofile[self.profile]['have_static'] \
            and not self.kiprofile[self.profile]['have_dhcp']:
            self.selector.screens.remove(dnsscreen)
            return

        # add the screen if it does not already exists
        if not dnsscreen_exists:
            self.selector.screens.insert(\
                self.selector.screens.index(self) + 1, dnsscreen)

    def validate(self):
        """
        Perform validity checks on received data.
        """

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
        """
        Checks whether the same prop is specified for more than one interface.

        Returns False and the list of properties duplicated, or True and empty
        list if all props are unique.

        Arguments:
        prop -- string index of property from interfaces dictionary to check
        """

        interfaces = self.kiprofile[self.profile]['interfaces']
        if len(interfaces) <= 1:
            return True, []

        dup_props = []
        props = []

        for intf in interfaces:
            if interfaces[intf]['configure'] \
                and not interfaces[intf]['use_dhcp'] \
                and interfaces[intf][prop] not in dup_props:
                if interfaces[intf][prop] in props:
                    dup_props.append(interfaces[intf][prop])
                else:
                    props.append(interfaces[intf][prop])

        if dup_props:
            return False, dup_props

        return True, []
 
    def drawImpl(self):
        """
        Draw the window.
        """

        self.screenGrid = snack.Grid(1, 3)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)

        self.listbox = snack.Listbox(6, scroll=1, returnExit=1, width=55)
        self.populateListbox(self.listbox)
        if len(self.listbox.key2item) < 1:
            raise KusuError, 'The setup cannot continue because no network ' + \
                             'interface devices could be found. Please ' + \
                             'check your system hardware to make sure that ' + \
                             'you have installed your network interface ' + \
                             'devices correctly.'

        self.screenGrid.setField(self.listbox, col=0, row=1,
                                 padding=(0, 1, 0, 0))

        footnote = '* activate interface on boot'
        footnote = snack.Textbox(len(footnote), 1, footnote)
        self.screenGrid.setField(footnote, 0, 2, padding=(0, 0, 0, -1))

    def populateListbox(self, listbox):
        """
        Populate the listbox with interfaces.
        """

        interfaces = self.kiprofile[self.profile]['interfaces']

        # we want interfaces in alphabetical order
        intfs = interfaces.keys()
        intfs.sort()

        for intf in intfs:
            # DHCP config for first interface
            if len(intfs) and intf == intfs[0] \
                and interfaces[intf]['first_seen']:
                interfaces[intf]['configure'] = True
                interfaces[intf]['use_dhcp'] = True
                interfaces[intf]['active_on_boot'] = True

            # static IP for second interface
            if len(intfs) > 1 and intf == intfs[1] \
                and interfaces[intf]['first_seen']:
                interfaces[intf]['configure'] = True
                interfaces[intf]['use_dhcp'] = False
                interfaces[intf]['hostname'] = 'cluster-' + intf
                interfaces[intf]['ip_address'] = '172.20.0.1'
                interfaces[intf]['netmask'] = '255.255.0.0'
                interfaces[intf]['active_on_boot'] = True
            interfaces[intf]['first_seen'] = False

            entrystr = '  ' + intf + ' not configured'
            if interfaces[intf]['configure']:
                if interfaces[intf]['use_dhcp']:
                    entrystr = 'DHCP'
                else:
                    entrystr = interfaces[intf]['ip_address'] + '/' + \
                               interfaces[intf]['netmask'] + ' ' + \
                               interfaces[intf]['hostname']

                if interfaces[intf]['active_on_boot']:
                    entrystr = '* ' + intf + ' ' + entrystr
                else:
                    entrystr = '  ' + intf + ' ' + entrystr

            kl.debug('Adding interface %s: %s.' % (intf, interfaces[intf]))
            listbox.append(entrystr[:50], intf)

    def restoreProfileFromSQLCollection(db, context, kiprofile):
        """
        Reads data from SQLiteCollection db according to context and fills
        profile.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db and profile
        kiprofile -- the complete profile (a dictionary) which we fill in
        """

        adapters = {}
        network_entries = db.get(context)
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

        kl.info('Adapters from DB: %s.' % adapters)
 
        interfaces = probe.getPhysicalInterfaces()    # we get a dictionary
        for intf in interfaces:
            # default to using DHCP and active on boot
            interfaces[intf].update({'configure': '',
                                     'use_dhcp': '',
                                     'hostname': '',
                                     'ip_address': '',
                                     'netmask': '',
                                     'active_on_boot': '',
                                     'first_seen': False})

            try:
                interfaces[intf].update(adapters[intf])
            except KeyError:
                interfaces[intf]['first_seen'] = True

            # SQLite stores these values as unicode strings
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

        kl.info('Read interfaces into profile: %s' % interfaces)
        kiprofile[context]['interfaces'] = interfaces

        return True

    def saveProfileToSQLCollection(db, context, kiprofile):
        """
        Writes data from profile to SQLiteCollection db according to context.

        Arguments:
        db -- an SQLiteCollection object ready to accept data
        context -- the context to use to access data in db and profile
        kiprofile -- the profile (a dictionary) with data to commit
        """

        interfaces = kiprofile[context]['interfaces']

        for intf in interfaces.keys():
            # these are bools,
            # we do str(int(bool)) to convert True to '1' and False to '0'
            db.put(context, 'configure:' + intf,
                              str(int(interfaces[intf]['configure'])))
            if interfaces[intf]['configure']:
                db.put(context, 'use_dhcp:' + intf,
                                  str(int(interfaces[intf]['use_dhcp'])))
                db.put(context, 'active_on_boot:' + intf,
                                  str(int(interfaces[intf]['active_on_boot'])))

                if not interfaces[intf]['use_dhcp']:
                    db.put(context, 'hostname:' + intf,
                                      interfaces[intf]['hostname'])
                    db.put(context, 'ip_address:' + intf,
                                      interfaces[intf]['ip_address'])
                    db.put(context, 'netmask:' + intf,
                                      interfaces[intf]['netmask'])

            kl.info('Wrote to DB %s: %s.' % (intf, interfaces[intf]))

        return True

    dbFunctions = {'MySQL': (None, None),
                   'SQLite': (None, None),
                   'SQLColl': (restoreProfileFromSQLCollection,
                               saveProfileToSQLCollection)}

class ConfigureIntfScreen:
    """
    Class implements the individual network adapter configuration.

    The dialog controls whether the interface is configured, the interface's IP
    and netmask or whether to configure it via DHCP, and whether to bring the
    interface up at boot.
    """

    def __init__(self, baseScreen):
        """
        Instantiation, set a few member variables from main network screen.
        """

        self.baseScreen = baseScreen
        self.screen = baseScreen.screen
        self.selector = baseScreen.selector
        self.context = baseScreen.context

    def configureIntf(self):
        """
        Draw the window, add callbacks, etc.
        """

        try:
            # listbox stores interface names as string objects (ie 'eth0')
            intf = self.baseScreen.listbox.current()
        except KeyError:
            # the listbox is empty
            return NAV_NOTHING

        self.interface = \
          self.baseScreen.kiprofile[self.baseScreen.profile]['interfaces'][intf]

        gridForm = snack.GridForm(self.screen,
                                  _('Configuring [%s]' % intf), 1, 4)

        device = snack.Textbox(40, 1, 'Device: ' + intf)
        vendor = snack.Textbox(40, 1, 'Vendor: ' + self.interface['vendor'])
        model = snack.Textbox(40, 1, 'Model: ' + self.interface['device'])
        module = snack.Textbox(40, 1, 'Module: ' + self.interface['module'])

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
        self.ip_address.addCheck(verifyIP)
        self.netmask = \
            kusuwidgets.LabelledEntry(labelTxt=_('Netmask '.rjust(11)),
                                      width=entryWidth)
        self.netmask.addCheck(verifyIP)
        self.hostname = \
            kusuwidgets.LabelledEntry(labelTxt=_('Host name '.rjust(11)),
                                                  width=entryWidth)
        self.hostname.addCheck(verifyHostname)

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
        """
        Adds callback functions to the use_dhcp and configdevice fields.
        """

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
        """
        Perform validity checks on received data.
        """

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
        """
        Store the configurations options.
        """

        self.interface['configure'] = bool(self.configdevice.value())
        self.interface['use_dhcp'] = bool(self.use_dhcp.value())
        self.interface['active_on_boot'] = bool(self.active_on_boot.value())

        self.interface['hostname'] = self.hostname.value()
        self.interface['ip_address'] = self.ip_address.value()
        self.interface['netmask'] = self.netmask.value()

    def populateIPs(self):
        """
        Populate fields with data.
        """
        
        if self.interface['configure']:
            self.configdevice.setValue('*')
        else:
            self.configdevice.setValue(' ')

        if self.interface['use_dhcp']:
            self.use_dhcp.setValue('*')
        else:
            self.use_dhcp.setValue(' ')

        if self.interface['active_on_boot']:
            self.active_on_boot.setValue('*')
        else:
            self.active_on_boot.setValue(' ')

        self.hostname.setEntry(self.interface['hostname'])
        self.ip_address.setEntry(self.interface['ip_address'])
        self.netmask.setEntry(self.interface['netmask'])

def enabledByValue(args):
    """
    Sets the enabled bit of widgets based on value of controlling widget.

    args -- a dictionary containing the controlling and controlled elements.
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
    """
    Obtains information about system's network interfaces from the database and
    pci.inf file via probe.getPhysicalInterfaces.
    """

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

    kl.info('Adapters in DB: %s.' % adapters)
    
    interfaces = probe.getPhysicalInterfaces()    # we get a dictionary
    for intf in interfaces:
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


