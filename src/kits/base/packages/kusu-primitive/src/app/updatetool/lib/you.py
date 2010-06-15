#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# 
# $Id$ 
# 
# Copyright (C) 2010 Platform Computing Inc. 
# 

from primitive.support import yum
from primitive.support import rpmtool
from primitive.support.proxy import Proxy

from path import path

class YouUpdate:

    def __init__(self, username, password, channel, arch, uri='https://%s:%s@nu.novell.com/repo/$RCE', proxy=None):
        self.username = username
        self.password = password
        self.channel = channel
        self.arch = arch

        self.uri = uri
        self.proxy = proxy

    def getUpdates(self, repo):

        # ported from kusu repoman:updates.py

        # Get the latest list of rpms from os kits and the
        # updates dir

        repo = path(repo)

        searchPath = []
        searchPath.append(repo / 'suse' / 'noarch')
        searchPath.append(repo / 'suse' / 'i586')
        searchPath.append(repo / 'suse' / 'i686')
        if self.arch == 'x86_64':
            searchPath.append(repo / 'suse' / 'x86_64')
        rpmPkgs = rpmtool.getLatestRPM(searchPath, True)

        uri = self.uri + '/' + self.channel + '/sles-10-' + self.arch
        uri = uri % (self.username, self.password)
        primarys = {uri : yum.YumRepo(uri,proxy=self.proxy).getPrimary()}

        # Filter out the packages that are newer and
        # needs to be downloaded
        downloadPkgs = []
        for r in self.getLatestRPM(primarys):
            name = r.getName()
            arch = r.getArch()

            if arch == 'src': continue

            if rpmPkgs.RPMExists(name, arch):
                # There's a newer rpm, so download it
                if r > rpmPkgs[name][arch][0]:
                    downloadPkgs.append(r)
            else:
                # No such existing rpm, so download it
                downloadPkgs.append(r)
       
        return downloadPkgs

    def getLatestRPM(self, primarys):
        """Return the latested rpms from yum repos"""

        c = rpmtool.RPMCollection()
        for uri, pri in primarys.items():
            for name, value in pri.items():
                for arch, rpms in value.items():
                    for r in rpms:
                        name = r.getName()
                        arch = r.getArch()

                        if c.RPMExists(name, arch):
                            if r > c[name][arch][0]:
                                c[name][arch][0] = r 
                        else:
                            c.add(r)

        c.sort()
        return c.getList()

