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

X86_ARCHES = ['i386','i486','i586','i686']

def OS():
    name = ver = ''
    if 'linux' == platform.system().lower():
        
        if os.path.exists('/etc/redhat-release'):
            splits = open('/etc/redhat-release').readline().split()
            
            if 'centos' == splits[0].lower():
                name = splits[0]
                ver = splits[2].split('.')[0] ## Major version only
            
            elif 'red' == splits[0].lower():
                name = 'RHEL'
                try:
                    ver = splits[6]
                except IndexError:
                    # RHEL 5.4 format
                    ver = splits[3]
            elif 'cern' == splits[2].lower():
                name = splits[0] + splits[1] + splits[2]
                ver = splits[5].split('.')[0] ## Major version only
            
            elif 'scientific' == splits[0].lower():
                name = splits[0] + splits[1]
                ver = splits[4].split('.')[0] ## Major version only
       
        elif os.path.exists('/etc/SuSE-release'):
            lines = open('/etc/SuSE-release').readlines()
            splits = lines[0].split()
            
            if 'suse' == splits[0].lower():
                name = 'SLES'
                if splits[4] == '10' and len(lines) == 3 and lines[2].split()[2] == '1':
                    ver = '10.1'
                else:
                    ver = splits[4]
            
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

def getArch():
    '''Returns the arch , collapses archs in X86_ARCHES to i386'''
    arch = platform.machine()
    if arch in X86_ARCHES:
        return 'i386'
    if arch ==  'x86_64':
        return arch
    return 'noarch' # fallback , should not be here. Things will break
    

if __name__ == '__main__':
    print getArch()
    print OS()
