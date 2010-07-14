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

from primitive.system.software import probe

class InstallerInitReceiver(object):

    def __init__(self):
        self.distroName, self.distroRelease, self.distroArch = probe.OS()
        self.keyboard_layout = probe.getKeyboard()
        self._timezone, self._utc = probe.getTimezone()

    def get_keyboard_layout(self):
        """ This method returns the keyboard layout as probed by this class. """
        return self.keyboard_layout

    def get_time_zone(self):
        """ Interface to expose the timezone property """
        return {'zone': self._timezone, 'utc' : self._utc, 'ntp': 'pool.ntp.org'}

    timezone = property(get_time_zone)
    keyboardLayout = property(get_keyboard_layout)

if __name__ == '__main__':
    probe_os = InstallerInitReceiver()

