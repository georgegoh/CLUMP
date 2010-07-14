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
    This is the command class for prompting and installing additional kits.
    """
    def __init__(self, receiver):
        super(InstallExtraKitCommand, self).__init__()
        self._receiver = receiver

    def execute(self):
        self._prompt_for_additional_kits()

    def _prompt_for_additional_kits(self):

        while True:
            kits_delete = False
            input_msg = "\nChoose one of the following actions:" +\
                        "\n[A]dd extra kits"
            if self._receiver.has_kits_to_delete():
                input_msg += "\n[D]elete extra kit (i.e. not base or OS kit)"
                kits_delete = True
            input_msg += "\n[C]ontinue with installation" +\
                         "\n>>"

            value = message.input(input_msg).strip()
            if value.lower() in ['a']:
                try:
                    value = int(message.input('\nSelect the kit media to add the kit from: \n'
                                          '1)\tCD/DVD drive \n'
                                          '2)\tISO image or mount point\n'
                                          '>> '))
                except ValueError:
                    message.display("Selection is not valid.")
                    continue

                if value == 1:
                    #Prompt for and install the additional kits
                    message.input("Insert the CD/DVD media containing your kits. Press ENTER to continue...")
                    status, msg = self._receiver.add_kits('cdrom')
                    if not status:
                        message.display(msg)
                elif value == 2:
                    status, msg = self._receiver.add_kits('iso')
                    if not status:
                        message.display(msg)
                else:
                    message.display("Selection is not valid.")
                    continue
            elif kits_delete and value.lower() in ['d']:
                status, msg =  self._receiver.delete_kits()
                if not status:
                    message.display(msg)
            elif value.lower() in ['c', '']:
                break
            else:
                if kits_delete:
                    message.display("Input is not valid. Enter either A, D or C.")
                else:
                    message.display("Input is not valid. Enter either A or C.")
                continue

        kits = self._receiver.find_incompatible_kits()
        if kits:
            message.warning(msg, 0)
            message.display('\nRemoving incompatible kits.')
            self._receiver.delete_kits(kits)
            message.success()
            self._prompt_for_additional_kits()

        self._proceedStatus = True

