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

import kusu.util.log as kusulog

kl = kusulog.getKusuLog()
kl.addFileHandler('/var/log/kusu/kusu-setup.log')

def display(desc):
    ignore_first_print = 1
    for msg in desc.split('\n'):
        if not ignore_first_print:
            print
        print '%s%s' % (' '*3, msg or ''),
        sys.stdout.flush()
        ignore_first_print = 0

def input(desc):
    if desc:
        display(desc)
        return raw_input()

def print_log_msg(cmd):
    runP = subprocess.Popen(cmd,
                                shell=True, stdout=subprocess.PIPE)
    out = runP.stdout.readlines()
    if out:
        print out[0].rstrip()

def failure(msg=None, print_status=1 ):
    if msg:
        kl.error(msg)

    if print_status:
        cmd = 'source /lib/lsb/init-functions && log_failure_msg "$@"'
        print_log_msg(cmd)

def success(msg=None, print_status=1):
    if msg:
        kl.info(msg)
        display(msg)

    if print_status:
        cmd = 'source /lib/lsb/init-functions && log_success_msg "$@"'
        print_log_msg(cmd)

def warning(msg=None, print_status=1):
    if msg:
        kl.warning(msg)
        display(msg)

    if print_status:
        cmd = 'source /lib/lsb/init-functions && log_warning_msg "$@"'
        print_log_msg(cmd)
