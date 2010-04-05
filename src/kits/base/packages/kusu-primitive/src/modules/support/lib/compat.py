#!/usr/bin/env python
#
# $Id: compat.py 3135 2009-10-23 05:42:58Z ltsai $
#
# Copyright 2008 Platform Computing Inc.
#

import __builtin__

if not hasattr(__builtin__, "sorted"):
    def mySorted(l):
        
        if type(l) is list:
            l.sort()
        elif type(l) in [range, xrange]:
            l = [x for x in l]
            l.sort()
        elif type(l) is str:
            l = list(l)
            l.sort()

        return l

    __builtin__.sorted = mySorted

if not hasattr(__builtin__, "reversed"):
    def myReversed(l):

        if type(l) is list:
            l.reverse()

        elif type(l) in [range, xrange]:
            l = [x for x in l]
            l.reverse()
        elif type(l) is str:
            l = list(l)
            l.reverse()

        return l

    __builtin__.reversed = myReversed
