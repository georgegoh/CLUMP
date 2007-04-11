#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
# 

import md5crypt
import time

class BaseInstall:
    attr = {}
    attr['disk'] = None
    attr['lpackage'] = []
    attr['lnetwork'] = []
    attr['rootpw'] = None
    attr['tz'] = None

    def setDiskProfile(self, disk):
        self.attr['disk'] = disk 
    
    def getDiskProfile(self):
        return self.attr['disk']

    def setPackageProfile(self, pkg):
        if type(pkg) is list:
            self.attr['lpackage'].extend(pkg)
        else:
            self.attr['lpackage'].append(pkg)
            
    def getPackageProfile(self, pkg=None):
        if pkg:
            pass
        else:
            return self.attr['lpackage']

    def setNetworkProfile(self, network):
        if type(network) is list:
            self.attr['lnetwork'].extend(network)
        else:
            self.attr['lnetwork'].append(network)

    def getNetworkProfile(self, dev=None):
        if dev:
            pass
        else:
            return self.attr['lnetwork']

    def setTZ(self, tz):
        self.attr['tz'] = tz

    def getTZ(self):
        return self.attr['tz'] 

    def setRootPw(self, rootpw):
        pass

    def getRootPw(self):
        return self.attr['rootpw']

    def setInstallSRC(self, url):
        self.attr['install_src'] = url

    def getInstallSRC(self):
        return self.attr['install_src']

    def setAttr(self, key, val):
        self.attr[key] = val

    def getAttr(self, key):
        return self.attr[key]


class Kickstart(BaseInstall):

    def setRootPw(self, rootpw):
        self.attr['rootpw'] = md5crypt.md5crypt(rootpw, str(time.time()));




