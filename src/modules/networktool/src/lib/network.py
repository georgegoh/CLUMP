#!/usr/bin/env python
#
# $Id: network.py 197 2007-03-29 09:34:52Z ltsai $
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

class Network:
    dev = None
    bootproto = None
    ip = None
    netmask = None
    gateway = None
    nameserver = None

    def __init__(self, dev, bootproto='DHCP'):
        self.dev = dev
        self.bootproto = bootproto

    def add(self, dev, bootproto):
        pass

    def addIP(self, ip):
        if self.bootproto != 'DHCP':
            self.ip = ip


