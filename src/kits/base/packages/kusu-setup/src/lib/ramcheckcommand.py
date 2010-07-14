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

RECOMMENDED_RAM_SIZE = 2048

class RamCheckCommand(Command):
    """
    This is the command class for checking requisite amount of RAM in the system.
    """
    def __init__(self, receiver):
        self._receiver = receiver

    def execute(self):
        """
            By default we require the master node to have at least 2GB RAM.
        """

        message.display("Checking if at least 2GB of RAM is present")
        ramSize = self._receiver.ramSize
        if ramSize >= RECOMMENDED_RAM_SIZE:
            message.success()
            self._proceedStatus = True
        else:

            self._proceedStatus = False
            self._quitMessage = "\nInsufficient memory for a master node installation. At least 2GB is required.\n You have only %dMB available." % int(ramSize)

