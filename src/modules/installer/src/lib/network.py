#!/usr/bin/env python
#
# $Id$
#
# Kusu Text Installer Network Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.

import socket
import snack
from gettext import gettext as _
from IPy import IP
from kusu.ui.text import kusuwidgets
from kusu.hardware import probe
import kusu.util.log as kusulog
from kusu.util.verify import *
from kusu.util.errors import *
from kusu.util import profile
from screen import InstallerScreen
from kusu.ui.text.navigator import NAV_NOTHING

kl = kusulog.getKusuLog('installer.network')

class NetworkScreen(InstallerScreen, profile.PersistentProfile):
    """
    The network screen lists all available network interfaces and provides
    their configuration.
    """

    name = _('Network')
    profile = 'Network'
    msg = _('Please configure your network')
    buttons = [_('Configure')]

    def __init__(self, kiprofile):
        InstallerScreen.__init__(self, kiprofile=kiprofile)
        profile.PersistentProfile.__init__(self, kiprofile)        

    def setCallbacks(self):
        """
        Implementation of the setCallbacks interface defined in parent class
        screenfactory.BaseScreen. Initialise button callbacks here.
        """

        self.buttonsDict[_('Configure')].setCallback_(\
            ConfigureIntfScreen.configureIntf, (ConfigureIntfScreen(self), ))

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

        rv, dups = self.checkDuplicates('netname')
        if not rv:
            msg = _('Identical %s %s assigned to more than one interface.')
            if len(dups) > 1:
                errList.append(msg % ('host names',
                               ', '.join(dups[:len(dups) - 1]) +
                               ' and %s' % dups[len(dups) - 1]))
            else:
                errList.append(msg % ('host name', dups[0]))

        rv = self.checkProvisionNetPresent()
        if not rv:
            msg = _('Define at least one provision type network.')
            errList.append(msg)

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

    def checkProvisionNetPresent(self):
        """
        Return False if no provision network is defined.
        """

        interfaces = self.kiprofile[self.profile]['interfaces']

        for intf in interfaces:
            if interfaces[intf]['configure'] \
                and interfaces[intf]['nettype'] == 'provision':
                return True

        return False

    def drawImpl(self):
        """
        Draw the window.
        """

        self.screenGrid = snack.Grid(1, 3)
        
        instruction = snack.Label(self.msg)
        self.screenGrid.setField(instruction, col=0, row=0)

        self.listbox = snack.Listbox(6, scroll=1, returnExit=0, width=55)
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

        if not self.kiprofile.has_key(self.profile):
            self.setDefaults()
        if not self.kiprofile[self.profile].has_key('interfaces'):
            self.setDefaults()
        interfaces = self.kiprofile[self.profile]['interfaces']

        # we want interfaces in alphabetical order
        intfs = sorted(interfaces)
        for intf in intfs:
            entrystr = '  ' + intf + ' not configured'
            if interfaces[intf]['configure']:
                if interfaces[intf]['use_dhcp']:
                    entrystr = 'DHCP'
                else:
                    entrystr = interfaces[intf]['ip_address'] + '/' + \
                               interfaces[intf]['netmask']

                entrystr += ' ' + interfaces[intf]['netname']
                entrystr += ' (' + interfaces[intf]['nettype'] + ')'

                if interfaces[intf]['active_on_boot']:
                    entrystr = '* ' + intf + ' ' + entrystr
                else:
                    entrystr = '  ' + intf + ' ' + entrystr

            kl.debug('Adding interface %s: %s.' % (intf, interfaces[intf]))
            listbox.append(entrystr[:50], intf)

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

    def save(self, db, profile):
        master = db.NodeGroups.selectfirst_by(type='installer')
        master_node = db.Nodes.selectfirst_by(ngid=master.ngid)
        primary_installer = db.AppGlobals(kname='PrimaryInstaller',
                                          kvalue=master_node.name)

        # this needs to be made node name agnostic
        other_ngs = \
            db.NodeGroups.select_by(db.NodeGroups.c.ngname.in_('compute-diskless',
                   'compute-imaged', 'compute', 'unmanaged'))

        interfaces = profile['interfaces']

        for intf in interfaces:
            if interfaces[intf]['configure']:
                newnic = db.Nics(mac=interfaces[intf]['hwaddr'], boot=False)
                master_node.nics.append(newnic)

                newnic.boot = interfaces[intf]['active_on_boot']
 
                newnet = db.Networks(usingdhcp=interfaces[intf]['use_dhcp'],
                                     device=intf,
                                     netname=interfaces[intf]['netname'],
                                     type=interfaces[intf]['nettype'],
                                     suffix='-' + intf)
 
                if not interfaces[intf]['use_dhcp']:
                    newnic.ip = interfaces[intf]['ip_address']

                    # the network is stored as IP & netmask (& = bitwise and)
                    ip = interfaces[intf]['ip_address']
                    nm = interfaces[intf]['netmask']
                    newnet.network = IP(ip).make_net(nm).strNormal(0)
                    newnet.subnet = interfaces[intf]['netmask']
                    newnet.gateway = interfaces[intf]['ip_address']

                master.networks.append(newnet)

                # copy network with eth0 if not already eth0
                if intf != 'eth0' \
                    and interfaces[intf]['nettype'] == 'provision':
                    net_copy = db.Networks()

                    for col in newnet.cols:
                        setattr(net_copy, col, getattr(newnet, col))

                    net_copy.device = 'eth0'
                    net_copy.netname = newnet.netname + '-eth0'
                    net_copy.suffix = '-eth0'
 
                # DANGER!!!! HARDCODING OCS-STYLE NETWORKS
                if intf == 'eth0':
                    for ng in other_ngs:
                        ng.networks.append(newnet)

                newnic.network = newnet

        db.flush()

    def setDefaults(self):
        interfaces = probe.getPhysicalInterfaces()    # we get a dictionary

        # we want interfaces in alphabetical order
        intfs = sorted(interfaces)
        for intf in intfs:
            # default to using DHCP and active on boot
            interfaces[intf].update({'configure': False,
                                     'use_dhcp': False,
                                     'netname': '',
                                     'ip_address': '',
                                     'netmask': '',
                                     'active_on_boot': True,
                                     'nettype': 'provision'})

            # DHCP config for first interface
            if len(intfs) > 0 and intf == intfs[0]:
                interfaces[intf]['configure'] = True
                interfaces[intf]['use_dhcp'] = False
                interfaces[intf]['netname'] = 'cluster'
                interfaces[intf]['ip_address'] = '172.20.0.1'
                interfaces[intf]['netmask'] = '255.255.0.0'
                interfaces[intf]['active_on_boot'] = True
                interfaces[intf]['nettype'] = 'provision'

            # static IP for second interface
            if len(intfs) > 1 and intf == intfs[1]:
                interfaces[intf]['configure'] = True
                interfaces[intf]['use_dhcp'] = False
                interfaces[intf]['netname'] = 'public'
                interfaces[intf]['ip_address'] = '192.168.0.100'
                interfaces[intf]['netmask'] = '255.255.255.0'
                interfaces[intf]['active_on_boot'] = True
                interfaces[intf]['nettype'] = 'public'

        self.kiprofile[self.profile] = {}
        self.kiprofile[self.profile]['interfaces'] = interfaces

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
        self.ip_address = \
            kusuwidgets.LabelledEntry(labelTxt=_('IP Address '.rjust(13)),
                                      width=entryWidth)
        self.ip_address.addCheck(verifyIP)
        self.netmask = \
            kusuwidgets.LabelledEntry(labelTxt=_('Netmask '.rjust(13)),
                                      width=entryWidth)
        self.netmask.addCheck(verifyIP)
        self.netname = \
            kusuwidgets.LabelledEntry(labelTxt=_('Network Name '.rjust(13)),
                                                  width=entryWidth)
        self.netname.addCheck(verifyHostname)
        self.nettype = snack.Label(_('Network Type '.rjust(13)))
        self.nettypes = snack.Listbox(3, scroll=1, returnExit=0,
                                      width=entryWidth)

        for type in self.baseScreen.kiprofile.getDatabase().Networks.types:
            self.nettypes.append(type, type)

        # initialize fields
        self.populateIPs()

        subgrid = snack.Grid(2, 1)

        namegrid = snack.Grid(1, 2)
        namegrid.setField(self.netname, 0, 0, (0, 0, 0, 0), anchorLeft=1)
        namesubgrid = snack.Grid(2, 1)
        namesubgrid.setField(self.nettype, 0, 0, anchorLeft=1, anchorTop=1)
        namesubgrid.setField(self.nettypes, 1, 0, anchorLeft=1)
        namegrid.setField(namesubgrid, 0, 1)

        ipgrid = snack.Grid(1, 4)
        ### Removing DHCP temporarily, fix in KUSU-207
        #ipgrid.setField(self.use_dhcp, 0, 0, (0, 0, 0, 1), anchorLeft=1)
        ###
        ipgrid.setField(self.ip_address, 0, 1, anchorLeft=1)
        ipgrid.setField(self.netmask, 0, 2, anchorLeft=1)
        ipgrid.setField(self.active_on_boot, 0, 3, (0, 1, 0, 0), anchorLeft=1)
        subgrid.setField(ipgrid, 0, 0, (0, 1, 0, 0), anchorTop=1)
        subgrid.setField(namegrid, 1, 0, (1, 1, 0, 0), anchorTop=1)
        gridForm.add(subgrid, 0, 2)

        # add OK and Cancel buttons
        ok_button = kusuwidgets.Button(_('OK'))
        cancel_button = kusuwidgets.Button(_('Cancel'))
        subgrid = snack.Grid(2, 1)
        subgrid.setField(ok_button, 0, 0, (0, 1, 1, 0))
        subgrid.setField(cancel_button, 1, 0, (0, 1, 0, 0))
        gridForm.add(subgrid, 0, 3, (0, 0, 0, -1))

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
                               self.netname, self.ip_address, self.netmask,
                               self.nettypes),
                   'enable': (self.netname, self.use_dhcp, self.active_on_boot,
                              self.nettypes),
                   'invert': False}
        dhcpd = {'control': self.use_dhcp,
                 'disable': (self.ip_address, self.netmask),
                 'enable': (self.ip_address, self.netmask),
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

        rv, msg = self.netname.verify()
        if rv is None:
            errList.append(_('Network name is empty.'))
        elif not rv:
            # Workaround; msg contains reference to Host name.
            msg = msg.replace('Host name', 'Network name')
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

        # check for valid ip/netmask combination
        try:
            IP(self.ip_address.value() + '/' + self.netmask.value(),
               make_net=True)
        except ValueError:
            errList.append(_('The address %s/%s is invalid.' %
                             (self.ip_address.value(), self.netmask.value())))

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

        self.interface['netname'] = self.netname.value()
        self.interface['nettype'] = self.nettypes.current()
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

        self.netname.setEntry(self.interface['netname'])
        self.nettypes.setCurrent(self.interface['nettype'])
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
