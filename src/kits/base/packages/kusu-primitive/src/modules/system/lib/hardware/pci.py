#!/usr/bin/env python
#
# $Id: pci.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

"""The class PCI parses the pci.ids file and returning a dictionary, keyed 
   by the vendor code

   It attempts to load well known location for the pci.ids file. If the 
   file cannot be found, it will just return an empy dictionary.

  >>> from kusu.hardware.pci import PCI
  >>> pci = PCI(['101e', '0b0b'])
  >>> p = pci.ids['101e']
  >>> print p['NAME'] # prints the name
"""
import os
import re
from path import path
from primitive.support import compat

class PCI:
    ids = {}
    
    def __init__(self, vcodes):
        filename = self._getIDSFile()

        if filename:
            f = open(filename, 'r')
            content = f.readlines()
            f.close()

            self._parse(content, vcodes)

    def _getIDSFile(self):

        ids_files = [path('/usr/share/hwdata/pci.ids'), \
                     path('/usr/share/pci.ids'), \
                     path('/etc/pci.ids'), \
                     path('./pci_ids')]

        kusu_root = path(os.environ.get('KUSU_ROOT', '/opt/kusu'))
        ids_files.append(kusu_root / 'etc' / 'pci.ids')
        
        for file in ids_files:
            if file.exists():
                return file
    
        # Totally give up
        return None

    def _parse(self, content, vcodes):
        # Syntax:
        # vendor  vendor_name
        #	device  device_name				<-- single tab
        #		subvendor subdevice  subsystem_name	<-- two tab

        for line in content:
            # Ignore comments
            m = re.match('#.*$', line)
            if m: continue
           
            # vendor  vendor_name
            m = re.match('[^\t\n]+', line)

            if m:
                line = m.group()
                line = line.split()

                # No more vendor code to check and is no
                # no longer the same vendor
                if len(vcodes) <= 0 and line[0] != vendor_code:
                    break

                vendor_code = line[0]

                if vendor_code == 'ffff':
                    break
                
                vendor_name = ' '.join(line[1:])

                # We are only interested in the vendor
                # codes that we want
                if vendor_code in vcodes:
                    self.ids[vendor_code] = {}
                    self.ids[vendor_code]['NAME'] = vendor_name
                    vcodes.pop(vcodes.index(vendor_code))
            
            else:
                #	device  device_name				<-- single tab
                m = re.match('\t[^\t]+', line)
                
                if m:
                    # We are only interested in the vendor
                    # codes that we want
                    if not self.ids.has_key(vendor_code):
                        continue

                    line = line.split()
                    device_code = line[0]
                    device_name = ' '.join(line[1:])

                    if not self.ids[vendor_code].has_key('DEVICE'):
                        self.ids[vendor_code]['DEVICE'] = {}

                    if not self.ids[vendor_code]['DEVICE'].has_key(device_code):
                        self.ids[vendor_code]['DEVICE'][device_code] = {} 
                    
                    self.ids[vendor_code]['DEVICE'][device_code]['NAME'] = device_name

                    
                else:
                    #		subvendor subdevice  subsystem_name	<-- two tabs
                    m = re.match('\t\t[^\t]+', line)
                    
                    if m:
                        # We are only interested in the vendor
                        # codes that we want
                        if not self.ids.has_key(vendor_code):
                            continue

                        line = line.split()
                        subvendor_code = line[0]
                        subdevice_code = line[1]
                        subsystem_name = ' '.join(line[2:])

                        if not self.ids[vendor_code]['DEVICE'][device_code].has_key('SUBVENDOR'):
                            self.ids[vendor_code]['DEVICE'][device_code]['SUBVENDOR'] = {}
                      
                        if not self.ids[vendor_code]['DEVICE'][device_code]['SUBVENDOR'].has_key(subvendor_code): 
                            self.ids[vendor_code]['DEVICE'][device_code]['SUBVENDOR'][subvendor_code] = {}
                       
                        self.ids[vendor_code]['DEVICE'][device_code]['SUBVENDOR'][subvendor_code][subdevice_code] = subsystem_name

            
