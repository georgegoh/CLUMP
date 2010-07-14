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

class CreateOSRepoCommand(Command):
    """
    This is the command class for initializing/creating the OS repository.
    """
    def __init__(self, receiver):
        super(CreateOSRepoCommand, self).__init__()
        self._receiver = receiver

    def get_default_repo_name(self):
        return self._receiver.default_repo_name

    def get_default_repo_id(self):
        return self._receiver.default_repo_id

    def execute(self):
        self._proceedStatus = True
        try:
            self._receiver.makeRepo()
        except Exception, msg:
            self._proceedStatus = False
            self._quitMessage = msg

    default_repo_name = property(get_default_repo_name)
    default_repo_id = property(get_default_repo_id)

