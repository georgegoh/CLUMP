#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# 
# $Id$ 
# 
# Copyright (C) 2010 Platform Computing Inc. 
# 

import socket
import xmlrpclib
import urllib2
import urlparse
import re

from primitive.support.proxy import HTTPSProxyTransport, Proxy
from primitive.support import rpmtool
from primitive.core.errors import RHNException
from primitive.core.errors import RHNServerException
from primitive.core.errors import RHNUnknownMethodException
from primitive.core.errors import RHNInvalidLoginException
from primitive.core.errors import RHNNoBaseChannelException
from primitive.core.errors import RHNInvalidSystemException
from primitive.core.errors import RHNURLNotFoundException

from path import path

class RHNUpdate(object):

    #More error codes and detail infomation about RHN XMLRPC interface, please refer to rhn-client-tools(rhnserver.py)
    rhnErrors = { -1: RHNUnknownMethodException,
                  -2: RHNInvalidLoginException,
                  -9: RHNInvalidSystemException,
                  -19: RHNNoBaseChannelException,
                  -208: RHNInvalidSystemException}

    rhnErrorsMsg = { -1: 'This username is already taken, or the password is incorrect.',
                     -2: 'Invalid username and password combination.',
                     -9: 'Invalid system. Please check your subscription.',
                     -19: 'Invalid channel. Pleae check your subscription.'}

    rhnProtoErrors = { 302: RHNURLNotFoundException,
                       404: RHNURLNotFoundException}

    def __init__(self, username, password, yumrhnURL=None, serverid=None, arch=None, version=None, proxy=None):
        self.yumrhnURL = 'https://rhn.redhat.com/rpc/api'
        self.proxy = proxy

        if yumrhnURL:
            if urlparse.urlsplit(yumrhnURL)[1] != 'rhn.redhat.com':
                self.yumrhnURL = yumrhnURL

        self.username = username
        self.password = password
        self.serverid = serverid
        self.os_arch = arch
        self.os_version = version
        
    def call(self, method, *args):
        """Wrapper function for all xmlrpc operation""" 
        try:
            return method(*args)
        except (socket.error, socket.herror, socket.gaierror, socket.timeout), e:
            raise RHNServerException, e

        except xmlrpclib.ProtocolError, e:
            errCode = e.errcode
            url = e.url
            errMsg = e.errmsg

            if errCode in self.rhnProtoErrors.keys():
                raise self.rhnProtoErrors[errCode], (errCode, url, errMsg)
            else:
                raise RHNServerException, (errCode, url, errMsg)

        except xmlrpclib.Fault, e:
            faultCode = e.faultCode
            faultStr = e.faultString

            if self.rhnErrors.has_key(faultCode):
                if self.rhnErrorsMsg.has_key(faultCode):
                    errMsg = self.rhnErrorsMsg[faultCode]
                else:
                    errMsg = faultStr

                raise self.rhnErrors[faultCode],  errMsg
            else:
                raise RHNException, (faultCode, faultStr)

    def login(self):
        """login to RHN"""
        self.session = self.call(self.rhnServer.auth.login, self.username, self.password)

    def logout(self):
        """logout from RHN"""
        self.call(self.rhnServer.auth.logout, self.session)
        self.session = None

    def getChannels(self):
        """Get available channel for the server"""
        channels = self.call(self.rhnServer.channel.software.listSystemChannels, self.session, self.serverid)
        channelnames = []
        # validate available channel name, for example:
        # 'rhel-x86_64-server-5'
        # 'rhel-x86_64-server-hpc-5'
        # 'rhel-x86_64-server-5-mrg-grid-1'
        for channel in channels:
            if not re.compile('^rhel-%s-(.*)-%s(.*)' % (self.os_arch, self.os_version)).match(channel['channel_label']):
                raise RHNServerException, 'Invalid Server ID given. Please check /opt/kusu/etc/updates.conf'

            channelnames.append(channel['channel_label'])
        return channelnames

    def getUpdates(self, repo):
        """ Get the latest list of rpms from os kits and the updates dir"""
        if self.proxy:
            self.rhnServer = xmlrpclib.Server(self.yumrhnURL, transport=HTTPSProxyTransport(self.proxy))
        else:
            self.rhnServer = xmlrpclib.Server(self.yumrhnURL)

        self.login()
        channels = self.getChannels()

        # Get the latest list of rpms from os kits and the
        # updates dir
        repo = path(repo)
        searchPaths = []
        searchPaths.append(repo / 'Server')
        searchPaths.append(repo / 'Cluster')
        searchPaths.append(repo / 'ClusterStorage')
        searchPaths.append(repo / 'VT')
        rpmPkgs = rpmtool.getLatestRPM(searchPaths, True)

        downloadPkgs={} 
        for channel in channels:
            downloadPkgs[channel] = []
            for r in self.getLatestPackages(channel):
                name = r.getName()
                arch = r.getArch()

                if rpmPkgs.RPMExists(name, arch):
                    # There's a newer rpm, so download it
                    if r > rpmPkgs[name][arch][0]:
                        downloadPkgs[channel].append(r)
                else:
                    # No such existing rpm, so download it
                    downloadPkgs[channel].append(r)

        systemid = self.getSystemID()
        self.logout()
        return downloadPkgs, systemid

    def getLatestPackages(self, channelLabel):
        """Get latest rpms from a channel"""
        rpms = self.call(self.rhnServer.channel.software.listLatestPackages, self.session, channelLabel)

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

            r = rpmtool.RPM(name = 'rhn://%s/%s' % (channelLabel, name),
                            version = version,
                            release = release,
                            epoch = epoch,
                            arch = arch)

            pkgs.append(r)
        return pkgs

    def getSystemID(self):
        """Get the systemid xml"""
        try:
            systemid = self.call(self.rhnServer.system.downloadSystemId, self.session, self.serverid) 
        except:
            raise RHNServerException, 'System (%s) not registered with rhn' % self.serverid

        return systemid
