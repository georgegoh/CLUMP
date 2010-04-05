#!/usr/bin/env python
#
# $Id: net.py 476 2008-01-25 12:36:55Z hirwan $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import re
from path import path
from kusu.hardware.pci import PCI

def getAllInterfaces():
    sys_net = path('/sys/class/net/')

    d = {}
    for p in sys_net.dirs():
        intf = p.basename()
        n = Net(intf) 

        d[intf] = {}
        d[intf]['vendor'] = n.vendor
        d[intf]['device'] = n.device
        d[intf]['module'] = n.module
        d[intf]['isPhysical'] = n.isPhysical()
        d[intf]['hwaddr'] = n.mac
        
    return d

def getPhysicalInterfaces():
    d = getAllInterfaces()

    dkeys = d.keys()

    # remove non-physical interfaces from dictionary
    for key in dkeys:
        if not d[key]['isPhysical']:
            d.pop(key)

    return d

class Net:
    sys_net = path('/sys/class/net/')

    interface = None
    vendor = None
    device = None
    module = None
    mac = None

    def __init__(self, interface):
        if interface not in self._getInterfaces():
            raise Exception, 'Interface not found'

        self.interface = interface
        self.dev_path = self.sys_net / interface / 'device'    

        if self.isPhysical():
            self._getVendorDevice()
            self._getModule()
            self._getMAC()

    def _getInterfaces(self):
        sys_net = path('/sys/class/net/')
        return [p.basename() for p in sys_net.dirs()]

    def isPhysical(self):
        if self.dev_path.exists():
            return True
        else:
            return False

    def _getVendorDevice(self):
        vendor_path = self.dev_path / 'vendor'
        f = open(vendor_path, 'r')
        vendor = f.read()
        f.close()
    
        device_path = self.dev_path / 'device'
        f = open(device_path, 'r')
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

        self.pci = PCI([vendor])

        if self.pci.ids.has_key(vendor):
            self.vendor = self.pci.ids[vendor]['NAME']

            if self.pci.ids[vendor]['DEVICE'].has_key(device):
                self.device = self.pci.ids[vendor]['DEVICE'][device]['NAME']
   
    def _getModule(self):
        # Attempt /sys/class/net/<if>/driver symlink
        driver_path = path(self.sys_net / self.interface / 'driver')
        if driver_path.exists():
            self.module = driver_path.realpath().basename()
        else:
            # Attempt /sys/class/net/<if>/devce/driver symlink
            driver_path = self.dev_path / 'driver'
            if driver_path.exists(): 
                self.module = driver_path.realpath().basename()

    def _getMAC(self):
        address = '/sys/class/net/%s/address' % self.interface
        
        f = open(address, 'r')
        self.mac = f.read().strip()
        f.close()

        
