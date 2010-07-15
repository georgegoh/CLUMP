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
from setup_errors import KusuProbePluginError

class SystemSettingsCommand(Command):
    """
    This is the command class for checking system settings.
    """
    def __init__(self, installer_receiver, networkReceiver, locale_receiver,
            fqdn_receiver, diskspace_receiver):
        super(SystemSettingsCommand, self).__init__()
        self._networkReceiver = networkReceiver

        self._installer_receiver = installer_receiver
        self._locale_receiver = locale_receiver
        self._fqdn_receiver = fqdn_receiver
        self._diskspace_receiver = diskspace_receiver

    def _check_valid_mountpoint(self):
        message.display("Checking for valid mountpoint for '/depot'")
        if not self._diskspace_receiver.freeDiskSpace:
            self._quitMessage = ("\nNo valid mountpoint found for '/depot'."
                                 "\nEnsure that there is at least one partition with a"
                                 "\nminimum of %sGB disk space available.") \
                                 % (self._diskspace_receiver.MINIMUM_DISK_SPACE_REQ/1024)
            return False

        if self._diskspace_receiver.is_depot_mountpoint():
            if self._diskspace_receiver.is_depot_valid_installdir():
                message.success()
            else:
                self._quitMessage = ("\nFound existing '/depot' mountpoint with insufficient diskspace."
                                     "\nMake sure that '/depot' has at least %dGB of free diskspace.") \
                                     % (self._diskspace_receiver.MINIMUM_DISK_SPACE_REQ/1024)
                return False

        message.success()
        return True

    def execute(self):

        if not self._check_valid_mountpoint():
            self._proceedStatus = False
            return

        interfaces, properties = self._networkReceiver.physicalInterfacesAndProperties

        #iterate over all the interfaces, validating at least
        #1 statically configured interfaces
        message.display("Checking for at least 1 statically configured NIC")
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
            self._quitMessage = "Not enough statically configured network interfaces.\nAt least 1 statically configured network interface required."
            return

        #make a note of how many configured interfaces we have
        self.configuredNicCount = ipCount

        message.display("Checking for the public hostname")
        if not self._fqdn_receiver.pub_dns_discover():
            self._quitMessage = ("\nNot able to discover the public hostname."
                                 "\nDo configure a valid public FQDN for your machine.")
            self._proceedStatus = False
            return
        else:
            message.success()

        message.display("Checking for existing DNS server")
        if self._networkReceiver.is_dns_installed():
                message.warning("\nA previously installed DNS server has been detected.\nProceeding will overwrite existing settings.")
                if not self.getYesNoAsBool("Would you like to proceed"):
                    self._quitMessage = "\nBye!"
                    self._proceedStatus = False
                    return
        else:
            message.success()

        message.display("Checking for existing DHCP server")
        if self._networkReceiver.is_dhcp_installed():
                message.warning("\nA previously installed DHCP server has been detected.\nProceeding will overwrite existing settings.")
                if not self.getYesNoAsBool("\nWould you like to proceed"):
                    self._quitMessage = "\nBye!"
                    self._proceedStatus = False
                    return
        else:
            message.success()

        try:
            self.keyboardLayout = self._installer_receiver.keyboardLayout
            self.timezone = self._installer_receiver.timezone
            self._locale_receiver.probe_locale()
            self.language = self._locale_receiver.language
            self._proceedStatus = True

        except KusuProbePluginError, msg:
            self._proceedStatus = False
            self._quitMessage = "\n%s" % msg
            return

        message.display("Probing for DNS settings")
        resolvList = self._networkReceiver.nameservers
        if len(resolvList) == 0:
            message.warning("No 'nameserver' entries were found in /etc/resolv.conf")
            nameservers = ""
            while nameservers == "":
                nameservers = message.input("\nEnter the IP addresses of your nameservers separated by commas: ")
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
                    message.display("None of the entered addresses is a valid IP address.")
                    nameservers = ""
        else:
            self.nameservers = resolvList
            message.success()

