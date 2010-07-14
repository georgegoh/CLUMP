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

class SanitizeInstallCommand(Command):
    """
    This is the command class for the pre-install cleanup task.
    """
    def __init__(self, receiver):
        super(SanitizeInstallCommand, self).__init__()
        self._receiver = receiver

    def execute(self):
        detected = self._receiver.detectOldKusu()
        self._proceedStatus = True

        if (detected):
            msg = "\nKusu is already installed on this machine.\nProceeding will completely remove the current installation."
            message.display("\n%s WARNING %s%s" % ('*'*20, '*'*20, msg) )

            if not self.getYesNoAsBool("\nWould you like to proceed"):
                self._proceedStatus = False
                self._quitMessage = "Exiting as requested..."
            else:
                self._receiver.cleanup()

