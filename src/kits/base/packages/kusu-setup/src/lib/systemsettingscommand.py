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
import kusu.ipfun as ipfun
from diskspacecheckreceiver import MINIMUM_DISK_SPACE_REQ


class SystemSettingsCommand(Command):
    """
    This is the command class for checking system settings
    """
    def __init__(self, networkReceiver, kb_receiver, locale_receiver, timezone_receiver, fqdn_receiver, diskspace_receiver):
        super(SystemSettingsCommand, self).__init__()
        self._networkReceiver = networkReceiver

        self._kb_receiver = kb_receiver
        self._locale_receiver = locale_receiver
        self._timezone_receiver = timezone_receiver
        self._fqdn_receiver = fqdn_receiver
        self._diskspace_receiver = diskspace_receiver

    def execute(self):

        # Handle existing '/depot' mountpoint
        message.display("Checking for existing '/depot' mountpoint")
        if self._diskspace_receiver.is_depot_mountpoint():
            if self._diskspace_receiver.is_depot_valid_installdir():
                message.success()
            else:
                message.failure()
                print "   Kusu Setup has found existing '/depot' mountpoint with insufficient diskspace.\n    Please make sure that the '\depot' partition has atleast %dGB of free diskspace. \n" % (MINIMUM_DISK_SPACE_REQ/1024)
                self._quitMessage = "\nBye!"
                self._proceedStatus = False
                return
        else:
            message.success()

        interfaces, properties = self._networkReceiver.physicalInterfacesAndProperties

        #iterate over all the interfaces, validating at least 2 static, configured interfaces
        message.display("Checking for at least 1 configured NIC")
        ipCount=0
        for interface in interfaces:
           if properties[interface]['ip'] is not None and\
                properties[interface]['ip'].strip() != 0 and\
                 not properties[interface]['dhcp'] :
                    ipCount = ipCount + 1

        if ipCount >= 1:
            message.success()
            self._proceedStatus = True
        else:
            self._proceedStatus = False
            self._quitMessage = "Not enough statically configured network interfaces.\n    Kusu installation requires at least 1 statically configured network interfaces"
            return

        #make a note of how many configured interfaces we have
        self.configuredNicCount = ipCount

        message.display("Checking for the public hostname.")
        if not self._fqdn_receiver.pub_dns_discover():
            message.failure()
            print "   Kusu-setup failed to discover the public hostname.\n    Please set a valid public FQDN for your machine."
            self._quitMessage = "\nBye!"
            self._proceedStatus = False
            return
        else:
            message.success()

        message.display("Checking for existing DNS server.")
        if self._networkReceiver.is_dns_installed():
                print "\n    A previously installed DNS server has been detected.\n    Proceeding will overwrite existing settings."
                message.warning()
                if not self.getYesNoAsBool("    Would you like to proceed"):
                    self._quitMessage = "\nBye!"
                    self._proceedStatus = False
                    return
        else:
            message.success()

        message.display("Checking for existing DHCP server")
        if self._networkReceiver.is_dhcp_installed():
                print "\n    A previously installed DHCP server has been detected.\n    Proceeding will overwrite existing settings."
                message.warning()
                if not self.getYesNoAsBool("    Would you like to proceed"):
                    self._quitMessage = "\nBye!"
                    self._proceedStatus = False
                    return
        else:
            message.success()

        try:
            self._kb_receiver.probe_keyboard()
            self.keyboardLayout = self._kb_receiver.keyboardLayout

            self._locale_receiver.probe_locale()
            self.language = self._locale_receiver.language

            self._timezone_receiver.probe_timezone()
            self.timezone = self._timezone_receiver.timezone

            self._proceedStatus = True

        except KusuProbePluginError, msg:
            message.failure()
            self._proceedStatus = False
            self._quitMessage = "Failed to properly detect system settings [%s]. Quitting." % msg
            return

        message.display("Probing for DNS settings")
        resolvList = self._networkReceiver.nameservers
        if len(resolvList) == 0:
            message.warning()
            print("\n    No 'nameserver' entries were found in /etc/resolv.conf")
            nameservers = ""
            while nameservers == "":
                nameservers = raw_input("    Please enter the IP addresses of your nameservers separated by commas: ")
                if nameservers.strip() == "":
                    continue

                nslist = nameservers.split(',')
                validList = []
                if len(nslist) > 0:
                    for ip in nslist:
                        if ipfun.validIP(ip):
                            #remove invalid ips from list
                            validList.append(ip)

                if len(validList) > 0:
                    message.success()
                    self.nameservers = validList
                    self._proceedStatus = True
                    break
                else:
                    print "Node of the entered addresses is a valid IP address."
                    nameservers = ""
        else:
            self.nameservers = resolvList
            message.success()

