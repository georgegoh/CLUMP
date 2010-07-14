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
from primitive.system.software import probe
import message

class SELinuxCheckCommand(Command):
    def __init__(self):
        super(SELinuxCheckCommand, self).__init__()

    def execute(self):

        message.display("Checking if SELinux is disabled")

        if probe.getSelinuxStatus():
            self._proceedStatus = False
            self._quitMessage = "SELinux is enabled. Kusu cannot be installed on a system with SELinux enabled. Disable SELinux and then restart the kusu-setup installation. NOTE: A system restart may be required after disabling SELinux."

        else:
            self._proceedStatus = True
            message.success('')



