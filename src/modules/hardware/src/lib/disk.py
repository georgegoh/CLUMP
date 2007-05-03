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
from kusu.hardware import ide, scsi

def getDisks():
    d = ide.getIDE('disk')
    d.update(scsi.getSCSI('disk'))

    return d



