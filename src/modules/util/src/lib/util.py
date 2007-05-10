#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import re
import os

def verifyFQDN(fqdn):
    """Verifies that text is a valid FQDN(.a-zA-Z0-9)"""
    p = re.compile('[^.a-zA-Z0-9]')
    li = p.findall(fqdn)
    if li:
        return False, 'FQDN can only contain the characters .a-zA-Z0-9'
    return True, None

def verifyIP(ip):
    """Verifies that text is a valid IP"""
    li = ip.split('.')
    errmsg = 'IP address must be in the form XXX.XXX.XXX.XXX, where ' + \
               '0 <= XXX <= 255'
    if len(li) != 4:
        return False, errmsg
    for octet in li:
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
        return False, 'Ensure a valid email is entered(e.g. xxyy@zzz.com)'
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
    d = distro.CheckDistro()
    d.verify(p, os_name, version_name)


def copy(src, dest):
    """ Performs a recursive copy. Source can either be 
        http/ftp or a local path
    """

    import urlparse
    from path import path

    if urlparse.urlsplit(src)[0] in ['http', 'ftp']:
        p = path(urlparse.urlsplit(src)[2]).splitall()

        # Deals with non-ending slash. 
        # Non-ending slash url ends up with an empty string in the 
        # last index of the list when a splitall is done
        if not p[-1]:
            cutaway = len(p[1:]) - 1
        else:
            cutaway = len(p[1:])

        if cutaway <= 0:
            cutaway = 0
        
        ec = os.system('cd %s && \
                        wget -m -np -nH -q --cut-dirs=%s %s' % (dest, cutaway, src))

        if ec:
            raise Exception
        else:
            return True

    else:
        if os.path.exists(src):
            os.system('find %s -depth -print | cpio -pd %s' % (src, dest))
            return True

        else:  
            raise Exception



