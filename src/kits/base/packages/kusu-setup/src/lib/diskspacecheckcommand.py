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

class DiskSpaceCheckCommand(Command):
    """
    This is the command class for checking requisite amount of diskspace
    in the system.
    """
    def __init__(self, receiver):
        super(DiskSpaceCheckCommand, self).__init__()
        self._receiver = receiver

    def show_partition_list(self, partitions):
        message.display("\nSelect one of the following mountpoints where "
                        "Kusu should place its '/depot':")
        count = 1
        for (mountpoint, size) in partitions:
            message.display("\n\t %d) MountPoint: '%s' FreeSpace: '%sB' " \
                    % (count, mountpoint, size))
            count += 1

    def execute(self):
        partitions = self._receiver.freeDiskSpace

        if len(partitions) == 1 and partitions[0][0] == '/depot':
            message.display("\nKusu Setup has found valid mountpoint "
                            "to place its '/depot'.")
            self._proceedStatus = True
            self.depot_partition = partitions[0]
            return

        self.show_partition_list(partitions)
        while True:
            try:
                message.display("\nType the number corresponding to your "
                                "preferred partition: ")
                value = int(raw_input()) - 1
                if value in range(0, len(partitions)):
                    self._receiver.prepareDepotFolder(partitions[value])
                    self._proceedStatus = True
                    self.depot_partition = partitions[value]
                    break
                else:
                    value = None
                    self.show_partition_list(partitions)
                    message.display("\nSelection is not valid. Choose correct "
                                    "number from the given options.")

            except ValueError:
                #in case non-integer selections or alphabetic chars are entered
                self.show_partition_list(partitions)
                message.display("\nSelection is not valid. Choose correct "
                                "number from the given options.")

