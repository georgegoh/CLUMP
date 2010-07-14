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

class InitKusuDBCommand(Command):
    """
    This is the command class for initializing kusudb.
    """
    def __init__(self, receiver, nicCheck, dhcpCheck, envCheck, systemSettings):
        super(InitKusuDBCommand, self).__init__()
        self._receiver = receiver
        self._nicCheck = nicCheck
        self._dhcpCheck = dhcpCheck
        self._envCheck = envCheck
        self._systemSettings = systemSettings

    def execute(self):
        result = self._receiver.createDB(self._nicCheck, self._dhcpCheck,
                                         self._envCheck, self._systemSettings)

        if result:
            self._proceedStatus = True
            #message.success()
        else:
            self._proceedStatus = False
            self._quitMessage = "Not able to initialize kusudb database. Exiting..."

