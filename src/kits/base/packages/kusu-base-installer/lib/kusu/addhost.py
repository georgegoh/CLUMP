#!/usr/bin/python
#
# Kusu add host
#
# Copyright (C) 2007 Platform Computing Inc.

# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

# Author: Shawn Starr <sstarr@platform.com>

""" AddHostPluginBase: These class methods may be overwriteable as needed """

class AddHostPluginBase:
    def __init__(self, dbconn):
        self.dbconn = dbconn

    def enabled(self):
        """virtual"""
        return True

    def added(self, nodename, info):
        """virtual"""
        pass

    def deleted(self, nodename, info):
        """virtual"""
        pass

    def replaced(self, nodename, info):
        """virtual"""
        pass

    def updated(self):
        """virtual"""
        pass

    def finished(self, nodelist):
        """virtual"""
        pass
