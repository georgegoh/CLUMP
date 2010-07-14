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

import message
from command import Command
from primitive.support import osfamily

KUSU_DISTRO_NAME = '${KUSU_DISTRO_NAME}'
KUSU_DISTRO_VERSION = '${KUSU_DISTRO_VERSION}'

class RpmCheckCommand(Command):
    """
    This is the command class for pre-installation rpm compatibility check
    """
    def __init__(self, receiver):
        super(RpmCheckCommand, self).__init__()
        self._receiver = receiver
        self.distroName = None

    def distro_and_system_is_of_rhelfamily(self):
        return self._receiver.distroName.lower() in osfamily.getOSNames('rhelfamily') and \
                KUSU_DISTRO_NAME.lower() in osfamily.getOSNames('rhelfamily')

    def execute(self):
        message.display("Checking for OS compatibility")

        if (self._receiver.distroName.lower() == KUSU_DISTRO_NAME.lower() or \
                self.distro_and_system_is_of_rhelfamily()) and \
                self._receiver.distroRelease == KUSU_DISTRO_VERSION:
            message.success()
            self._proceedStatus = True
            self.distroName = self._receiver.distroName
        else:
            self._proceedStatus = False
            self._quitMessage = "This operating system is not compatible with this installer."


