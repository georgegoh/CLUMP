#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import subprocess 
import os
import re
from path import path


def getInterfaces():
    f = open('/proc/net/dev', 'r')
    dev = f.readlines()
    f.close()

    ifnames = []
    for line in dev[2:]:
        ifname = line.split(':')[0].strip()
        ifnames.append(ifname)

    return ifnames

class Interface:

    interface = None
    ip = None
    broadcast = None
    netmask = None
        
    def __init__(self, interface):
        self.interface = interface
        self._getIPNetmask()

    def up(self):
        try:
            p = subprocess.Popen('ifconfig %s up' % self.interface,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode
        except Exception, e:
            print e

        if retcode:
            raise Exception, 'interface %s cannot be brought up' % self.interface


    def down(self):
        try:
            p = subprocess.Popen('ifconfig %s down' % self.interface,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode
        except Exception, e:
            print e

        if retcode:
            raise Exception, 'interface %s cannot be brought down' % self.interface


    def _getIPNetmask(self):
        try:
            p = subprocess.Popen('ifconfig ' + self.interface,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            retcode = p.returncode
        except Exception, e:
            print e

        if retcode:
            raise Exception, 'interface %s not found' % self.interface

        #From http://www.regular-expressions.info
        regex_str = '\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b'
        addr =  re.findall(regex_str, out)

        if len(addr): # IP is configured
            self.ip = addr[0]
            
            if len(addr) > 2:
                self.broadcast = addr[1]
                self.netmask = addr[2]
            else:
                self.ip = addr[0]
                self.netmask = addr[1]

    def setStaticIP(self, IPNetmask):
        cmd = 'ifconfig %s %s netmask %s' % (self.interface, IPNetmask[0], IPNetmask[1])

        try:
            p = subprocess.Popen(cmd,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

            out, err = p.communicate()
            retcode = p.returncode
        except Exception, e:
            raise e

        if not retcode:
            self._getIPNetmask()
        else:
            raise Exception, 'Failed to set static IP'

 
            
    def setDHCP(self):
        kusu_root = os.environ.get('KUSU_ROOT', None)

        if not kusu_root:
            raise Exception, 'KUSU_ROOT not found'

        script = path(kusu_root) / 'bin' / 'udhcpc.script'

        
        if  os.uname()[0] in ['Linux']:

            # Check for distro & ver 
            #os.environ.get('KUSU_DIST', None) 
            #os.environ.get('KUSU_DISTVER', None) 
            cmd = 'udhcpc -q -n -i %s -s %s' % (self.interface, script)
        else:
            raise Exception, 'Not supported operating system'
    

        try:
            p = subprocess.Popen(cmd,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except Exception, e:
            raise e

        retcode = p.returncode
       
        if not retcode:
            self._getIPNetmask()
        else:
            raise Exception, 'Failed to get ip from dhcp'

        
    def getIPNetmask(self):
        return (self.ip, self.netmask)
      
