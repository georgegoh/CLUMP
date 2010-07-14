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

class InstallOSKitCommand(Command):
    """
    This is the command class for prompting and installing the OS kit
    """
    def __init__(self, receiver):
        super(InstallOSKitCommand, self).__init__()
        self._receiver = receiver

    def execute(self):
        self._proceedStatus = False
        while True:
            try:
                value = int(message.input('\nSelect the media to install KUSU from: \n' +
                                      '1)\tCD/DVD drive \n' +
                                      '2)\tISO image or mount point\n' +
                                      '>> '))
            except:
                message.display("\nInvalid option is given.")
                continue

            if value == 1:
                #Prompt for and install the additional kits
                message.input("Insert the CD/DVD media containing your KUSU Installation. Press ENTER to continue...")
                status, msg = self._receiver.installKitsOnBootMedia('cdrom')
            elif value == 2:
                status, msg = self._receiver.installKitsOnBootMedia('iso')
            else:
                message.display("\nInvalid option is given.")
                continue

            if not status:
                message.display(msg)
                message.display("\nInstallation can't continue until the 'base kit' has been installed")
                self._proceedStatus = False
            else:
                self._proceedStatus = True
                break

        #Prompt for and install the OS kit
        while True:
            try:
                value = int(message.input('\nSelect the media to install the OS kit from: \n' +
                                      '1)\tCD/DVD drive \n' +
                                      '2)\tISO image or mount point\n' +
                                      '>> '))
            except:
                message.display("\nInvalid option is given.")
                continue

            if value == 1:
                #Prompt for and install the base kit
                message.input("\nInsert the CD/DVD media containing your OS. Press ENTER to continue...")
                status, msg = self._receiver.install_os_kit('cdrom')
            elif value == 2:
                status, msg = self._receiver.install_os_kit('iso')
            else:
                message.display("\nInvalid option is given.")
                continue

            if not status:
                message.display(msg)
                message.display("\nInstallation can't continue until the 'OS kit' has been installed")
                self._proceedStatus = False
            else:
                self._proceedStatus = True
                break

