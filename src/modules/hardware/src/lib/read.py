#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

def readFile(filename):
    f = open(filename, 'r')
    content = f.read()
    f.close()

    return content.strip()
