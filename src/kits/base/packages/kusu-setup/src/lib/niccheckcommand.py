#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

from command import Command
import message

class NicCheckCommand(Command):
    """
    This is the command class for gathering information on the provisioning network.
    """
    def __init__(self, receiver, configuredNicCount):
        super(NicCheckCommand, self).__init__()
        self._receiver = receiver
        self._configuredNicCount = configuredNicCount

        ## We gather information on the provisioning network interface,
        ## and expose a tuple consisting of : (interface, properties)
        self.provisionInterfaceTuple = None
        self.publicInterfaceTuple = None

    def _interface_prompt(self, interfaces, properties, network_type):
        count = 1
        message.display("\nSelect one of the following interfaces to use for the %s network:" % network_type)
        for interface in interfaces:
            if properties[interface]['ip'] is not None and properties[interface]['ip'].strip() != '':
                if network_type == 'public':
                    message.display("\n\t %d) Interface: %s, IP: %s, Netmask: %s " % (count, interface, properties[interface]['ip'], properties[interface]['netmask']))
                    count += 1
                elif network_type == 'provisioning':
                    message.display("\n\t %d) Interface: %s, IP: %s, Netmask: %s " % (count, interface, properties[interface]['ip'], properties[interface]['netmask']))
                    count += 1

         # If we do not find any interface then exit
        if count == 1:
            self._quitMessage = "Not able to detect any statically configured network interfaces\nfor use as your public network. At least two statically configured network interfaces\nare required to install Kusu."
            self._proceedStatus = False
            return self._proceedStatus
        return True

    def _promptForNic(self, interfaces, properties, network_type):
        status = self._interface_prompt(interfaces, properties, network_type)
        if not status:
            return status, ()
        while True:
            try:
                value = int(message.input("\nEnter the number corresponding to your selected interface: ")) - 1
                if value in range(0, len(interfaces)):
                    break
                else:
                    value = None
                    message.display("\nSelection is not valid. Choose correct number from the given options.")
            except ValueError:
                    message.display("\nSelection is not valid. Choose correct number from the given options.")

        return status, (interfaces[value], properties[interfaces[value]])

    def _promptForPublicNic(self):
        interfaces, properties = self._receiver.physicalInterfacesAndProperties
        if self.provisionInterfaceTuple:
            del properties[self.provisionInterfaceTuple[0]]
            interfaces.remove(self.provisionInterfaceTuple[0])
        return self._promptForNic(interfaces, properties, "public")

    def _promptForProvisioningNic(self):
        interfaces, properties = self._receiver.physicalInterfacesAndProperties
        return self._promptForNic(interfaces, properties, "provisioning")

    def execute(self):

        self.singleNicInstall = False

        status, self.provisionInterfaceTuple = self._promptForProvisioningNic()
        if not status:
            return

        #if we have more than one configured nic, we prompt for whether the user want's to configure
        # a second/public nic.
        if self._configuredNicCount > 1 and \
                self.getYesNoAsBool("\nWould you like to configure a public network", 'Y'):
            status, self.publicInterfaceTuple = self._promptForPublicNic()
            if not status:
                return
        else:
            self.singleNicInstall = True

        self._proceedStatus = True

