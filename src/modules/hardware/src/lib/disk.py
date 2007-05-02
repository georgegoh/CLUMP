#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
from path import path

def getDisks():
    d = _getIDE('disk')
    d.update(_getSCSI('disk'))

    return d


def _readFile(filename):
    f = open(filename, 'r')
    content = f.read()
    f.close()

    return content.strip()

def _getIDE(type):
    ide_path = path('/proc/ide')

    d = {}
    for hd in ide_path.listdir('hd*'):
        media = hd / 'media'
        
        if _readFile(media) == type:
            model = hd / 'model'
            model = _readFile(model)

            d[hd.basename()] = {'model': model}

    return d


def _getSCSI(type):

    # Based on scsi.h, scsi.c(kudzu) 
    type_map = {'disk': [0x00, 0x07, 0x0e]}

    scsi_path = path('/sys/bus/scsi/devices')

    d = {}
    for s in scsi_path.listdir():
        if os.path.exists(s / 'type') and \
           int(_readFile(s / 'type')) in type_map[type]:

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
            d[dev]['vendor'] = _readFile(s / 'vendor')
            d[dev]['model'] = _readFile(s / 'model')
        

    return d 


        


