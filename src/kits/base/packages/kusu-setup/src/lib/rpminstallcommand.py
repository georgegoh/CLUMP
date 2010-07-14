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
        self._receiver = receiver
        self._repoid = repoid

    def execute(self):

        #installLocation = "/mnt//base" #FIXME:
        #installLocation = message.input("Please enter location of Kusu RPMs: [/media/cdrom] ")


        #if not os.path.exists(installLocation):
        #    self._proceedStatus = False
        #    self._quitMessage = "Invalid install location provided. Exiting..."
        #    return

        #if not self._receiver.verifyKusuDistroSupported(installLocation):
	    #self._proceedStatus = False
        #    self._quitMessage = "Kusu RPMs provided are not OS-compatible with the Installer machine."
        #    return

        message.display("Installing Kusu RPMs")
        status = self._receiver.installRPMs(self._repoid)

        if status:
            message.success()
            self._proceedStatus = True
        else:
            message.failure()
            self._proceedStatus = False
            self._quitMessage = "RPM Installation failed. Exiting."

