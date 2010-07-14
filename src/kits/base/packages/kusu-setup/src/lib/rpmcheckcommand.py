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
from string import upper
import message

#FIXME: This must be a build-time make macro
SUPPORTED_OPERATING_SYSTEMS = ['RHEL', 'CENTOS', 'SCIENTIFICLINUXCERN', 'SCIENTIFICLINUX']

class RpmCheckCommand(Command):
    """
    This is the command class for pre-installation rpm compatibility check
    """
    def __init__(self, receiver):
        super(RpmCheckCommand, self).__init__()
        self._receiver = receiver
        self.distroName = None

    def execute(self):
        message.display("Checking for OS compatibility")

        if upper(self._receiver.distroName) in SUPPORTED_OPERATING_SYSTEMS:
            message.success()
            self._proceedStatus = True
            self.distroName = self._receiver.distroName
        else:
            #message.failure()
            self._proceedStatus = False
            self._quitMessage = "This operating system is not compatible with this installer."


