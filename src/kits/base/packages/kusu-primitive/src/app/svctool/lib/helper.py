#!/usr/bin/env python
# $Id$
#
# Copyright 2008 Platform Computing Inc.
#
''' Helper functions for Svctool:
    - checkForRequiredArgs
    - runServiceCommand
    - printOutErr
    - dispatcherNameVerArch
'''
from primitive.core.command import CommandFailException
from primitive.support import osfamily
import subprocess

class SvcCommandException(CommandFailException): pass

def checkForRequiredArgs(input_dict, required_args):
    ''' Ensure that required arguments are present in the input
        dictionary.
    '''
    missing = filter(lambda x: x not in input_dict.keys(), required_args)
    if not missing:
        return True, []
    else:
        return False, missing

def runServiceCommand(cmd):
    """ Run one command only, when you don't want to bother setting up
        the Popen stuff.
    """
    try:
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError,e:
        raise SvcCommandException, 'SvcTool failed due to OSError %s' % e
    if p.returncode and err:
        return False, (out, p.returncode, err)
    return True, (out, p.returncode, err)

def runServiceCommandDiscardOutput(cmd):
    """ Does the same thing as runServiceCommand, except that
        stdout and stderr are sent to /dev/null.
    """
    f = open('/dev/null', 'w+')
    try:
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout=f,
                             stderr=f)
        out, err = p.communicate()
    except OSError,e:
        raise SvcCommandException, 'SvcTool failed due to OSError %s' % e
    f.close()
    if p.returncode and err:
        return False, (out, p.returncode, err)
    return True, (out, p.returncode, err)

def printOutErr((out, ret_code, err)):
    if err:
        if len(err) > 0:
            print 'ERROR: ' + err
    if ret_code:
        print 'Exit with code: %d' % ret_code
    if out:
        if len(out) > 0:
            print out

def dispatcherNameVerArch((name, ver, arch)):
    if name.lower() in osfamily.getOSNames('rhelfamily'):
        return ('RHEL', ver, arch)
    elif 'opensuse' == name.lower():
        return ('SLES', ver, arch)
    else:
        return (name, ver, arch)

