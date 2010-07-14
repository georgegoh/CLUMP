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

class InstallExtraKitCommand(Command):
    """
    This is the command class for prompting and installing additional kits
    """
    def __init__(self, receiver):
        super(InstallExtraKitCommand, self).__init__()
        self._receiver = receiver

    def execute(self):
        self._prompt_for_additional_kit()

    def _prompt_for_additional_kit(self):

        while True:
            value = message.input('\nDo you want to add any additional kits[Y|N]: ')
            if value.lower() in ['y', 'yes']:
                try:
                    value = int(message.input('\nSelect the kit media to add the kit from: \n'
                                          '1)\tCD/DVD drive \n'
                                          '2)\tISO image or mount point\n'
                                          '>> '))
                except:
                    message.display("Invalid option is given.")
                    continue

                if value == 1:
                    #Prompt for and install the additional kits
                    message.input("Insert the CD/DVD media containing your kits. Press ENTER to continue...")
                    status, msg = self._receiver.install_kits('cdrom')
                    if not status:
                        message.display(msg)
                elif value == 2:
                    status, msg = self._receiver.install_kits('iso')
                    if not status:
                        message.display(msg)
                else:
                    message.display("Invalid option is given.")
                    continue
            elif value.lower() in ['n', 'no']:
                break
            else:
                message.display("Wrong Input enter [Y|N]")
                continue

        self._proceedStatus = True
