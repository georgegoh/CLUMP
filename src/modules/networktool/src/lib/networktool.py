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

class Interface:

    interface = None
    ip = None
    broadcast = None
    netmask = None
        
    def __init__(self, interface):
        self.interface = interface
        self._getIPNetmask()

    def _getIPNetmask(self):
        p = subprocess.Popen('ifconfig ' + self.interface,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out = p.stdout.read()

        #From http://www.regular-expressions.info
        regex_str = '\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b'
        addr =  re.findall(regex_str, out)

        self.ip = addr[0]
        self.broadcast = addr[1]
        self.netmask = addr[2]

    def setStaticIP(self, (ip, netmask)):
        pass

    def setDHCP(self):
        kusu_root = os.environ.get('KUSU_ROOT', None)

        if not kusu_root:
            raise Exception, 'KUSU_ROOT not found'

        script = path(kusu_root) / 'bin' / 'udhcpc.script'

        cmd = 'udhcpc -q -n -i %s -s %s' % (self.interface, script)
        retcode = subprocess.call(cmd, shell=True)

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
      
