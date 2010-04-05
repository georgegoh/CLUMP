#!/usr/bin/python

# servicefun.py - A collection of functions for manipulating services

#   Copyright 2007 Platform Computing Inc
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
# 	
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#
#


import string
import os

def getrunlevel():
    """To get current runlevel"""
    ri,ro,re=os.popen3("runlevel | awk '{print $2}'")
    try:
        # return default run level
        return string.atoi(ro.read()[0])
    finally:
        ro.close()

def chkonlevels(servicename):
    """Return a list contains all the levels with on status when chkconfig the service"""
    levels = []
    pi,po,pe=os.popen3("chkconfig --list %s" % (servicename))
    try:
        # get all the "on" levels
        statusarray = po.read().split("\t")
        for status in statusarray:
            tmp = status.split(":")
            if len(tmp) > 1:
                if tmp[1] == "on":
                    levels.append(string.atoi(tmp[0]))

        return levels
    finally: po.close()
