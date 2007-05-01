#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import re
from path import path
from kusu.hardware.pci import PCI


def getInterfaces():
    sys_net = path('/sys/class/net/')
    return [p.basename() for p in sys_net.dirs()]

class Net:
    sys_net = path('/sys/class/net/')

    def __init__(self, interface):
        if interface not in getInterfaces():
            raise Exception, 'Interface not found'


        dev_path = self.sys_net / interface / 'device'    
        f = open(dev_path / 'vendor', 'r')
        vendor = f.read()
        f.close()

        f = open(dev_path / 'device', 'r')
        device = f.read()
        f.close()

        #f = open(dev_path / 'subsystem_device', 'r')
        #subsystem_device = f.read()
        #f.close()

        #f = open(dev_path / 'subsystem_vendor', 'r')
        #subsystem_vendor = f.read()
        #f.close()


        # Strip off 0x and \n
        vendor = vendor[2:].strip()
        device = device[2:].strip()
        #subsystem_device = subsystem_device[2:].strip()
        #subsystem_vendor = subsystem_vendor[2:].strip()

        self.pci = PCI()
        self.vendor = self.pci.ids[vendor]['NAME']
        self.device = self.pci.ids[vendor]['DEVICE'][device]['NAME']



