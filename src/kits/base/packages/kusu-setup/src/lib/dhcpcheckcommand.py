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
from string import strip
import message

class DhcpCheckCommand(Command):
    """
    This is the command class for verifying DHCP environment.
    """
    def __init__(self, receiver):
        super(DhcpCheckCommand, self).__init__()
        self._receiver = receiver
        self.dhcpLocality = None
        self.dnsLocality = None

    def prompt_for_dhcp_locality(self):
        """
            Ask the user whether their DHCP server is to be run locally or externally
        """
        message.display("\nIndicate whether you are running a local (master node) or external (on attached network) DHCP server for your provisioning network")
        message.display("\n\t1) Local DHCP server")
        message.display("\n\t2) External DHCP server")

    def prompt_for_dns_locality(self):
        """
            Ask the user whether their Domain Name server is to be run locally or externally
        """
        message.display("\nIndicate whether you are running a local (master node) or external (on attached network) Domain Name server for your provisioning network")
        message.display("\n\t1) Local Domain Name Server (DNS)")
        message.display("\n\t2) External Domain Name Server (DNS)")

    def execute(self):

        ##Ask the user if have external or local DHCP for the provisioning network.
        while True:
            self.prompt_for_dhcp_locality()
            dhcpLocality = message.input("\nEnter the number corresponding to your selection: [1]")
            if strip(dhcpLocality) not in ["1", "2", ""]:
                message.display("\nSelection is not valid. Choose either (1) or (2) from the given options.")
            else:
                break

        #handle default selection
        if dhcpLocality == "":
            dhcpLocality = "1"

        while True:
            self.prompt_for_dns_locality()
            dnsLocality = message.input("\nEnter the number corresponding to your selection: [1]")
            if strip(dnsLocality) not in ["1", "2", ""]:
                message.display("\nSelection is not valid. Choose either (1) or (2) from the given options.")
            else:
                break

        ##If external, we set the DHCP nic equal to provisioning NIC (must be on same network anyway)
            ##If local, we detect
                ##If can't find, bitch about it
                ##If we find it, we check the settings and act accordingly

        #handle default selection
        if dnsLocality == "":
            dnsLocality = "1"

        if dhcpLocality == "1":
            self.dhcpLocality = 1
        else:
            self.dhcpLocality = 0

        if dnsLocality == "1":
            self.dnsLocality = 1
        else:
            self.dnsLocality = 0

        self._proceedStatus = True


