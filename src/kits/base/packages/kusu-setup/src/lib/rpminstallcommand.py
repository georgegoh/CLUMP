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
import os
import message

class RpmInstallCommand(Command):
    def __init__(self, receiver, repoid):
        super(RpmInstallCommand, self).__init__()
        self._receiver = receiver
        self._repoid = repoid

    def execute(self):
        message.display("\nInstalling Kusu RPMs. This will take a while...")
        status = self._receiver.installRPMs(self._repoid)

        if status:
            message.success()
            self._proceedStatus = True
        else:
            message.failure()
            self._proceedStatus = False
            self._quitMessage = "\nNot able to install RPMs. Exiting."

