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

from setup_errors import KusuProbePluginError
import message

GREP_COMMAND = 'grep -P '
LOCALE_CMD = '/usr/bin/locale '

class LanguageReceiver(object):

    def __init__(self):
        self._language = ''

    def probe_locale(self):
        message.display("Probing for the language/locale settings")
        command = LOCALE_CMD + '|' + GREP_COMMAND +  '^LANG'
        run_cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                stderr = subprocess.PIPE)
        out, err = run_cmd.communicate()
        if out and not out.strip() == 'LANG=':
            # e.g. LANG=en_US.UTF-8
            self._language = out.split('=')[1].split('.')[0]
        else:
            raise KusuProbePluginError, "Not able to figure out the system language/locale."

        message.success()
        return True

    def get_lang(self):
        """ Returns the selected language. """
        return self._language

    language = property(get_lang)


if __name__ == "__main__":
    lang = LanguageReceiver()
    lang.probe_locale()

