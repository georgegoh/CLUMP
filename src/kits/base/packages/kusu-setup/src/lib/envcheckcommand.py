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
from setup_errors import KusuProbePluginError
import message

class EnvCheckCommand(Command):
    """
    This is the command class for checking/probing for timestamp, language, FQDN and Keyboard
    """
    def __init__(self, provisioningInterfaceTuple, publicInterfaceTuple, fqdn_receiver):

        super(EnvCheckCommand, self).__init__()

        (self._prov_interface, self._prov_interface_props) = provisioningInterfaceTuple

        if publicInterfaceTuple is not None:
            (self._pub_interface, self._pub_interface_props) = publicInterfaceTuple

        self._fqdn_receiver = fqdn_receiver

    def execute(self):

        try:
            (self.prov_fqdn, self.pub_fqdn) = self._fqdn_receiver.fqdn
            self._proceedStatus = True

        except KusuProbePluginError, msg:
            message.failure()
            self._proceedStatus = False
            self._quitMessage = "Failed to properly detect system settings [%s]. Quitting." % msg

