#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from path import path
import subprocess

def getRAID():
    # list of devices under raid
    #dmraid -b -c 

    dmraidP = subprocess.Popen('dmraid -s -c', 
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = dmraidP.communicate()

    returncode = dmraidP.returncode

    if not returncode:
        return [ str(path('/dev/mapper') / d)for d in out.split() ]
    
    
