#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from kusu.hardware.read import readFile
from path import path
import subprocess

def getSCSI(type):

    # Based on scsi.h, scsi.c(kudzu) 
    type_map = {'disk': [0x00, 0x07, 0x0e]}

    scsi_path = path('/sys/bus/scsi/devices')

    d = {}
    for s in scsi_path.listdir():
        if os.path.exists(s / 'type') and \
           int(readFile(s / 'type')) in type_map[type]:

            dev = s.listdir('block:*')
            
            # block:<dev> exists
            if dev: 
                dev = dev[0].realpath().basename()
            else: # block exists
                dev = (s / 'block').realpath().basename()

            # Handle cciss!c0d0 in /sys/block
            if dev.find('cciss!') != -1:
                dev = dev.replace('!', os.sep)
            
            d[dev] = {}
            d[dev]['vendor'] = readFile(s / 'vendor')
            d[dev]['model'] = readFile(s / 'model')
        

    return d 


        


