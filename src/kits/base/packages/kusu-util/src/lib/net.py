#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

from IPy import IP
from kusu.util.errors import StartIPNotInNetError, NoFreeIPError

def nextIP(nw, nm, startip='', inc=1, exclusion_list=[]): 
    """
    Returns the next available IP based on network (nw), netmask (nm),
    startip and IP increment (inc) not occuring in exclusion_list.
    """

    nwnm = IP(nw + '/' + nm)
    if startip:
        startip = IP(startip)
    else:
        startip = nwnm

    if startip not in nwnm:
        raise StartIPNotInNetError, \
                    'Start ip %s not in net: %s' % (startip, nwnm)

    # add network and broadcast to exclusion list and convert to integers
    exclusion_list.append(nwnm.net())
    exclusion_list.append(nwnm.broadcast())
    exclusion_list = [IP(x).ip for x in exclusion_list]

    # use nwnm.ip as offset as xrange cannot handle long ints
    startip = startip.ip - nwnm.ip
    if inc < 0:
        endip = 0
    else:
        endip = nwnm.broadcast().ip - nwnm.ip

    for x in xrange(startip, endip, inc):
        ip = x + nwnm.ip
        if ip not in exclusion_list:
            return IP(ip).strNormal()

    raise NoFreeIPError, 'No free ip addresses found in net: %s' % nwnm
