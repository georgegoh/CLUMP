#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import re

class PCI:
"""
Parses the pci.ids file and returning a dictionary, keyed by the vendor code

{'DEVICE': {'0009': {'NAME': 'MegaRAID 428 Ultra RAID Controller (rev 03)'},
            '1960': {'NAME': 'MegaRAID',
                     'SUBVENDOR': {'101e': {'0471': 'MegaRAID 471 Enterprise 1600 RAID Controller',
                                            '0475': 'MegaRAID 475 Express 500/500LC RAID Controller',
                                            '0477': 'MegaRAID 477 Elite 3100 RAID Controller',
                                            '0493': 'MegaRAID 493 Elite 1600 RAID Controller',
                                            '0494': 'MegaRAID 494 Elite 1650 RAID Controller',
                                            '0503': 'MegaRAID 503 Enterprise 1650 RAID Controller',
                                            '0511': 'MegaRAID 511 i4 IDE RAID Controller',
                                            '0522': 'MegaRAID 522 i4133 RAID Controller'},
                                   '1028': {'0471': 'PowerEdge RAID Controller 3/QC',
                                            '0475': 'PowerEdge RAID Controller 3/SC',
                                            '0493': 'PowerEdge RAID Controller 3/DC',
                                            '0511': 'PowerEdge Cost Effective RAID Controller ATA100/4Ch'},
                                   '103c': {'60e7': 'NetRAID-1M'}}},
            '9010': {'NAME': 'MegaRAID 428 Ultra RAID Controller'},
            '9030': {'NAME': 'EIDE Controller'},
            '9031': {'NAME': 'EIDE Controller'},
            '9032': {'NAME': 'EIDE & SCSI Controller'},
            '9033': {'NAME': 'SCSI Controller'},
            '9040': {'NAME': 'Multimedia card'},
            '9060': {'NAME': 'MegaRAID 434 Ultra GT RAID Controller'},
            '9063': {'NAME': 'MegaRAC',
                     'SUBVENDOR': {'101e': {'0767': 'Dell Remote Assistant Card 2'}}}},
 'NAME': 'American Megatrends Inc'}
"""
    ids = '/usr/share/hwdata/pci.ids'
    d = {}
    
    def __init__(self):

        f = open(self.ids, 'r')
        content = f.readlines()
        f.close()

        self._parse(content)

    def _parse(self, content):
        # Syntax:
        # vendor  vendor_name
        #	device  device_name				<-- single tab
        #		subvendor subdevice  subsystem_name	<-- two tabs

        for line in content:
            # Ignore comments
            m = re.match('#.*$', line)
            if m: continue
           
            # vendor  vendor_name
            m = re.match('[^\t][\w ]+', line)

            if m:
                line = m.group()
                line = line.split()

                vendor_code = line[0]
                if vendor_code == 'ffff':
                    break
                
                vendor_name = ' '.join(line[1:])
                self.d[vendor_code] = {}
                self.d[vendor_code]['NAME'] = vendor_name

            else:
                #	device  device_name				<-- single tab
                m = re.match('\t[\w ]+', line)
                
                if m:
                    line = line.split()
                    device_code = line[0]
                    device_name = ' '.join(line[1:])

                    if not self.d[vendor_code].has_key('DEVICE'):
                        self.d[vendor_code]['DEVICE'] = {}

                    if not self.d[vendor_code]['DEVICE'].has_key(device_code):
                        self.d[vendor_code]['DEVICE'][device_code] = {} 
                    
                    self.d[vendor_code]['DEVICE'][device_code]['NAME'] = device_name

                    
                else:
                    #		subvendor subdevice  subsystem_name	<-- two tabs
                    m = re.match('\t\t[\w ]+', line)
                    
                    if m:
                        line = line.split()
                        subvendor_code = line[0]
                        subdevice_code = line[1]
                        subsystem_name = ' '.join(line[2:])

                        if not self.d[vendor_code]['DEVICE'][device_code].has_key('SUBVENDOR'):
                            self.d[vendor_code]['DEVICE'][device_code]['SUBVENDOR'] = {}
                      
                        if not self.d[vendor_code]['DEVICE'][device_code]['SUBVENDOR'].has_key(subvendor_code): 
                            self.d[vendor_code]['DEVICE'][device_code]['SUBVENDOR'][subvendor_code] = {}
                       
                        self.d[vendor_code]['DEVICE'][device_code]['SUBVENDOR'][subvendor_code][subdevice_code] = subsystem_name



if __name__ == '__main__':
        p = PCI()
        
