#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import xmlrpclib
import urllib2
import re

from kusu.util import rpmtool

class RHN:
    headers = ['X-RHN-Server-Id',
               'X-RHN-Auth-User-Id',
               'X-RHN-Auth',
               'X-RHN-Auth-Server-Time',
               'X-RHN-Auth-Expire-Offset']

    rhnURL = 'http://rhn.redhat.com/rpc/api'
    up2dateURL = 'http://xmlrpc.rhn.redhat.com/XMLRPC'

    def __init__(self, username, password):
        self.rhnServer = xmlrpclib.Server(self.rhnURL)

        cfg = self.getRHNConfig()
        self.up2dateServer = xmlrpclib.Server(cfg['up2dateURL'])

        self.username = username
        self.password = password

    def getRHNConfig(self):
        #f = open('/etc/sysconfig/rhn/up2date', 'r')
        return {'up2dateURL': self.up2dateURL}
    
    def login(self):
        """login to RHN"""
        self.session = self.rhnServer.auth.login(self.username, self.password)
        self.loginInfo = self.up2dateServer.up2date.login(self.getSystemID())
    
    def logout(self):
        """logout from RHN"""
        self.rhnServer.auth.logout(self.session)
        self.session = None
        self.loginInfo = None

    def getChannels(self, rhnServerID):
        """Get avalable available for rhnServer ID"""
        channels = self.rhnServer.channel.software.listSystemChannels(self.session, rhnServerID)
        return channels

    def getLatestPackages(self, channelLabel):
        """Get latest rpms from a channel"""
        rpms = self.rhnServer.channel.software.listLatestPackages(self.session, channelLabel)

        pkgs = []
        for r in rpms:
            name = r['package_name']
            version = r['package_version']
            release = r['package_release']
            epoch = r['package_epoch']
            arch = r['package_arch_label']

            # None epoch is returned as " "
            if not epoch.strip():
                epoch = None

            r = rpmtool.RPM(name = name,
                            version = version,
                            release = release,
                            epoch = epoch,
                            arch = arch)

            pkgs.append(r)
        return pkgs
       
    def getSystemID(self):
        f = open('/etc/sysconfig/rhn/systemid', 'r')
        systemid = f.read()
        f.close()

        return systemid

    def getServerID(self):
        """Get the sever ID"""
        systemID = xmlrpclib.loads(self.getSystemID())[0][0]['system_id']

        mt = re.compile('\d+').search(systemID)
    
        if mt:
            return int(mt.group())
        else:
            return None
    
    def getPackage(self, rpm, channelLabel):
        """Get a RPM from the channel"""
        req = urllib2.Request(self.up2dateURL + '/$RHN/%s/getPackage/%s' % (channelLabel, rpm))
        for h in self.headers:
            if self.loginInfo.has_key(h):
                req.add_header(h, self.loginInfo[h])
        f = urllib2.urlopen(req)
        return f.read()
     
