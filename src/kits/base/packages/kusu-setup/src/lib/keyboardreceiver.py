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

import sys
try:
    import subprocess
except ImportError:
    from popen5 import subprocess

from path import path
from setup_errors import KusuProbePluginError
import message

GREP_COMMAND = 'grep -P \'^KEYTABLE\' '
KEYBOARD_FILE = '/etc/sysconfig/keyboard'

class KeyboardReceiver(object):

    def __init__(self, args=None):
        super(KeyboardReceiver, self).__init__()
        self.keyboard_layout = None

    def probe_keyboard(self):
        message.display("Probing keyboard settings")
        if not path(KEYBOARD_FILE).exists():
            raise KusuProbePluginError, "Not able to probe keyboard layout."

        command = GREP_COMMAND + KEYBOARD_FILE
        run_cmd = subprocess.Popen(command, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        out, err = run_cmd.communicate()
        if out:
             try:
                 self.keyboard_layout = out.rstrip().split('=')[1].split('.')[0]
             except:
                 raise KusuProbePluginError, "Not able to probe keyboard layout."
        else:
            message.failure()
            raise KusuProbePluginError, "Not able to probe keyboard layout."

        message.success()
        return True

    def get_keyboard_layout(self):
        """ This method returns the keyboard layout as probed by this class. """
        return self.keyboard_layout

    keyboardLayout = property(get_keyboard_layout)


if __name__ == "__main__":
    keyboard = KeyboardCommandReceiver()
    keyboard.run()
