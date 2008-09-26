#!/usr/bin/env python
#
# $Id: verify.py 1347 2008-06-11 10:49:27Z hsaliak $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import re
from path import path
import kusu.util.log as kusulog
from kusu.util.errors import *

try:
    import subprocess
except:
    from popen5 import subprocess

logger = kusulog.getKusuLog('util.verify')

def verifyFQDN(fqdn):
    """Verifies that text is a valid FQDN(.a-zA-Z0-9)"""

    oc = re.compile('[a-zA-Z]')
    li = oc.findall(fqdn)
    if not li:
        return False, 'Fully-qualified host name must contain at least ' + \
                      'one letter'

    p = re.compile('[^.\-a-zA-Z0-9]')
    li = p.findall(fqdn)
    if li:
        return False, 'Fully-qualified host name can only contain the ' + \
                      'characters .-a-zA-Z0-9'
    return True, None

def verifyHostname(hostname):
    """Verifies that text is a valid host name (-a-zA-Z0-9)"""
    
    p = re.compile('[^\-a-zA-Z0-9]')
    li = p.findall(hostname)

    if li:
        return False, \
            'Host name can only contain the characters -, a-z, A-Z, and 0-9.'
    return True, None

def verifyIP(ip):
    """Verifies that text is a valid IP"""

    li = ip.split('.')

    errmsg = 'IP address must be in the form XXX.XXX.XXX.XXX, where ' + \
               '0 <= XXX <= 255.'

    if len(li) != 4:
        return False, errmsg

    for octet in li:
        if len(octet) == 0:
            return False, errmsg

        if len(octet) > 1 and octet[0] == '0':
            return False, errmsg + ', leading zeros are not permitted'

        try:
            octet_int = int(octet)
            if octet_int < 0 or octet_int > 255:
                return False, errmsg
        except ValueError:
            return False, errmsg

    return True, None

def verifyEmail(email):
    """Verifies that text is a valid email"""
    p = re.compile('^[a-zA-Z][\w\.-]*[a-zA-Z0-9]' + '@' + \
                  '[a-zA-Z0-9][\w.-]*[a-zA-Z0-9]\.[a-zA-Z][a-zA-Z\.]*[a-zA-Z]$')
    li = p.findall(email)
    if len(li) != 1:
        return False, 'Ensure a valid email is entered (e.g. someone@yyy.zzz)'
    return True, None

def verifyURL(url):
    """Verifies that text is a valid URL"""
    p = re.compile('^http://[a-zA-Z0-9][\w.-]*[a-zA-Z0-9]' + '\.' + \
                   '[a-zA-Z][a-zA-Z\.]*[a-zA-Z]')
    li = p.findall(url)
    if len(li) != 1:
        return False, 'Ensure a valid url is entered(e.g. http://www.xyz.com)'
    return True, None


def verifyDistro(p, os_name, version_name):
    """ Verify a distribution source 
        
        path - Either a HTTP/FTP URL or a local path
        os   - The distro/os name in lower caps
        version - The version of the os
    """
    
    from kusu.util.distro import distro

    logger.info('Verifying %s for %s %s' % (p, os_name, version_name))
    d = distro.CheckDistro()
    d.verify(p, os_name, version_name)



