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

def getIDE(type):
    if type not in ['disk', 'cdrom', 'tape']:
        raise Exception, 'Unknown type'

    ide_path = path('/proc/ide')

    d = {}
    for hd in ide_path.listdir('hd*'):
        media = hd / 'media'
        
        if readFile(media) == type:
            model = hd / 'model'
            model = readFile(model)

            d[hd.basename()] = {'model': model}

    return d



