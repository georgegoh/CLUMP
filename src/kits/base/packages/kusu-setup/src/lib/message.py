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
except:
    from popen5 import subprocess


def display(desc):
    print '%s%s' % (' '*3, desc or ''),
    sys.stdout.flush()


def failure():
    cmd = 'source /lib/lsb/init-functions && log_failure_msg "$@"'
    failureP = subprocess.Popen(cmd,
                                shell=True)
    failureP.communicate()
    sys.stdout.flush()

def success():
    cmd = 'source /lib/lsb/init-functions && log_success_msg "$@"'
    successP = subprocess.Popen(cmd,
                                shell=True)
    successP.communicate()
    sys.stdout.flush()

def warning():
    cmd = 'source /lib/lsb/init-functions && log_warning_msg "$@"'
    successP = subprocess.Popen(cmd,
                                shell=True)
    successP.communicate()
    sys.stdout.flush()

