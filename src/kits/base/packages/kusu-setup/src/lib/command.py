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


class Command(object):

    def __init__(self):
        self._proceedStatus = False
        self._quitMessage = ""

    def execute(self):
       pass

    def getYesNoAsBool(self, prompt):
        answer = "INITIAL_PROMPT"

        #force a single-character Yes/No response
        while answer.strip().lower() not in ['no', 'yes', 'y', 'n', '']:
            answer = raw_input("%s ? (Y/[N])" % prompt)

        if answer.strip().lower() in ['yes','y']:
            return True

        return False

    def getQuitMessage(self):
        """
            The reason for quitting
        """
        return self._quitMessage


    def getProceedStatus(self):
        """
            This determines whether our caller can proceed with the next call or not
            _proceedStatus = True - Proceed
            _proceedStatus = False - Halt and get reason from quitMessage property
        """
        return self._proceedStatus

    ## Define our properties
    quitMessage = property(getQuitMessage)
    proceedStatus =  property(getProceedStatus)
