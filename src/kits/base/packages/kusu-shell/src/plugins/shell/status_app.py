#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import sys

from kusu.shell import Status, KusuShellApp

KUSU_SHELL_COMMAND = 'status'
KUSU_SHELL_COMMAND_CLASS = 'StatusApp'

class StatusApp(KusuShellApp):
    def __init__(self, args, db=None, **kwargs):
        super(StatusApp, self).__init__(args, db, **kwargs)
        self.result = None

        if not self._remaining_args:
            raise ValueError, "'%s' called with no arguments" % args[0]
        elif self._remaining_args[0] == 'summary' and len(self._remaining_args) < 2:
            raise ValueError, "'%s %s' called with no arguments" % (args[0], self._remaining_args[0])

    def run(self):
        if self._remaining_args[0] == 'summary':
            self._run_summary(self._remaining_args[1:])
        elif self._remaining_args[0] == 'nodegroups':
            self._needs_database()
            status = Status(self._db)
            self.result = status.nodegroups()
        else:
            raise RuntimeError, "invalid command: %s" % self._remaining_args[0]

    def _run_summary(self, args):
        if args[0] == 'nodes':
            self._needs_database()
            status = Status(self._db)
            self.result = status.nodes_summary()
        else:
            raise RuntimeError, "invalid summary command: %s" % args[0]

    def print_result(self):
        self.result.writexml(self._out, indent="  ", addindent="  ", newl="\n")
