#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from IPy import IP

def nextIP(nw, nm, inc=1, exclusion_list=[]): 
    """
    Returns the next available IP based on network (nw), netmask (nm)
    and IP increment (inc) not occuring in exclusion_list. If no available IPs
    are found, None is returned.
    """

    nwnm = IP(nw + '/' + nm)
    for x in xrange(1, len(nwnm) / inc + 1):
        ip = nwnm[x * inc].strNormal()
        if ip not in exclusion_list:
            return ip
