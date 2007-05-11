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
from path import path
import kusu.util.log as kusulog

try:
    import subprocess
except:
    from popen5 import subprocess

logger = kusulog.getKusuLog('util')

def verifyFQDN(fqdn):
    """Verifies that text is a valid FQDN(.a-zA-Z0-9)"""

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
        return False, 'Host name can only contain the characters -a-zA-Z0-9'
    return True, None

def isHostRoutable(ip, nm, host):
    """Indicates whether host is routable from ip/nm (nm = netmask).

    All arguments are strings in dotted-quad format (xxx.xxx.xxx.xxx).
    """

    import socket
    import struct

    ip_n = struct.unpack('>L', socket.inet_aton(ip))[0]
    nm_n = struct.unpack('>L', socket.inet_aton(nm))[0]
    host_n = struct.unpack('>L', socket.inet_aton(host))[0]

    return ip_n & nm_n == host_n & nm_n

def verifyIP(ip):
    """Verifies that text is a valid IP"""

    li = ip.split('.')

    errmsg = 'IP address must be in the form XXX.XXX.XXX.XXX, where ' + \
               '0 <= XXX <= 255'

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

    logger.info('Verifying %s for %s %s' % (p, os_name, version_name))
    d = distro.CheckDistro()
    d.verify(p, os_name, version_name)


def copy(src, dest):
    """ Performs a recursive copy. Source can either be 
        http/ftp or a local path
    """

    import urlparse

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

        cmd = 'wget -m -np -nH --cut-dirs=%s %s' % (cutaway, src)

        try:
            p = subprocess.Popen(cmd,
                                 cwd = dest,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode
        except Exception, e:
            raise e    

        if retcode:
            raise Exception
        else:
            return True


    else:
        if os.path.exists(src):
            os.system('find %s -depth -print | cpio -pd %s' % (src, dest))
            return True

        else:  
            raise Exception



