#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

class NetworkProfile:
    net_dict = {}
    dns = []
    gateway = None

    def __int__(self):
        pass

    def addNetwork(self, intf):
        self.net_dict[intf] = Network(intf)

class Network:
    dev = None
    bootproto = None
    ip = None
    netmask = None
    gateway = None
    nameserver = None
    hostname = None

    def __init__(self, dev):
        self.dev = dev



