#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright 2010 Platform Computing Inc.
#
#This file contains library functions to detect Os name, ver and arch

import os
import os.path
import platform
import subprocess
import re

from primitive.support.osfamily import getOSNames
from errors import *

X86_ARCHES = ['i386','i486','i586','i686']

def OS_full_version():
    name = ver = ''
    if 'linux' == platform.system().lower():

        if os.path.exists('/etc/redhat-release'):
            splits = open('/etc/redhat-release').readline().split()

            if 'centos' == splits[0].lower():
                name = splits[0]
                ver = splits[2]

            elif 'red' == splits[0].lower():
                name = 'RHEL'
                try:
                    ver = splits[6]
                except IndexError:
                    # RHEL 5.4 format
                    ver = splits[3]
            elif 'cern' == splits[2].lower():
                name = splits[0] + splits[1] + splits[2]
                ver = splits[5]

            elif 'scientific' == splits[0].lower():
                name = splits[0] + splits[1]
                ver = splits[4]

        elif os.path.exists('/etc/SuSE-release'):
            lines = open('/etc/SuSE-release').readlines()
            splits = lines[0].split()

            if 'suse' == splits[0].lower():
                name = 'SLES'
                if splits[4] == '10' and len(lines) == 3:
                    ver = '10.' + lines[2].split()[2]

            elif 'opensuse' == splits[0].lower():
                name = splits[0]
                ver = splits[1]

        else:
            name, ver = platform.dist()[:2]

    else:
        name = platform.system()
        ver = platform.release()

    arch = getArch()

    ### FIXME: This is a temporary fix for KUSU-1073.
    # In installer environment, the release files are not present.
    # Get the name, ver and arch from the environment variables instead.
    if name == '':
        name = os.getenv('KUSU_DIST', '').upper()
    if ver == '':
        ver = os.getenv('KUSU_DISTVER', '')
    if arch == '':
        arch = os.getenv('KUSU_DIST_ARCH', '')

    return name, ver, arch

def OS():
    name, ver, arch = OS_full_version()
    if name.lower() in ['centos', 'scientificlinux', 'scientificlinuxcern'] or \
            (name.lower() == 'sles' and not ver == '10.1'):
        ver = ver.split('.')[0]

    return name, ver, arch

def getArch():
    '''Returns the arch , collapses archs in X86_ARCHES to i386'''
    arch = platform.machine()
    if arch in X86_ARCHES:
        return 'i386'
    if arch ==  'x86_64':
        return arch
    return 'noarch' # fallback , should not be here. Things will break


def getSelinuxStatus():
    """Parse the output of the 'sestatus' command and return boolean"""

    name, ver, arch = OS()
    if name.lower() not in getOSNames('rhelfamily') + ['fedora']:
        return False

    p = subprocess.Popen('sestatus', shell=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    bSELinuxEnabled = False

    for line in p.stdout.readlines():
        if re.compile("^SELinux status:").search(line):
            try:
                (one, two, three) = line.split()

                bSELinuxEnabled = three.rstrip() != 'disabled'
            except ValueError, e:
                pass

            break

    retval = p.wait()

    return bSELinuxEnabled


def getKeyboard():
    if not os.path.exists('/etc/sysconfig/keyboard'):
        raise KeyboardMissingException, '/etc/sysconfig/keyboard not found.'
    keyb = 'us'
    try:
        f = open('/etc/sysconfig/keyboard', 'r')
        for line in f:
            if not line.strip().startswith('#') and \
               line.split('=', 1)[0] == 'KEYTABLE':
                try:
                    keyb = line.split('=', 1)[1].strip().strip('"')
                    keyb = keyb.split('.', 1)[0]
                except:
                    continue
    finally:
        f.close()
    return keyb


def getTimezone():

    if not os.path.exists('/etc/sysconfig/clock'):
        raise TimeZoneMissingException, '/etc/sysconfig/clock not found'

    f = open('/etc/sysconfig/clock', 'r')

    lines = f.readlines()
    f.close()

    name, ver, arch = OS()
    timezone = None
    utc = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line[0] == "#":
            continue
        try:
            key,val = line.split('=', 1)
        except:
            continue

        val = val.strip().strip('"')
        name = name.lower()

        if name in getOSNames('rhelfamily') + ['fedora']:
            if key == 'ZONE':
                timezone = val
            elif key == 'UTC':
                if val == 'false':
                    utc = False
                else:
                    utc = True
        elif name in ['sles', 'opensuse', 'suse']:
            if key == 'TIMEZONE':
                timezone = val
            elif key == 'HWCLOCK':
                if val == '--localtime':
                    utc = False
                elif val == '-u':
                    utc = True

    return (timezone, utc)


if __name__ == '__main__':
    print getArch()
    print OS()
