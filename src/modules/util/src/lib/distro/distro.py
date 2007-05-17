#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import urlparse
import ConfigParser
from path import path
from urlcheck import URLCheck
from kusu.util.distro.errors import *

class CheckDistro:
    dirlayout = {}
    filelayout = {}
    distroLayout = {}

    def __init__(self):

        kusu_root = os.getenv('KUSU_ROOT', None)

        if not kusu_root:
            kusu_root = '/opt/kusu'

        filename = path(kusu_root) / 'etc' / 'distro.conf'
        self.distroLayout = self._loadConf(str(filename))
      
    def _loadConf(self, filename):
        try:
            config = ConfigParser.RawConfigParser()
            f = open(filename)
            config.readfp(f)
            f.close()
        
            d = {}
            for sec in config.sections():
                os, version = sec.split('-')

                if not d.has_key(os):
                    d[os] = {}

                d[os][version] = {}

                for key, value in config.items(sec):
                    lst = value.split(':')
                    
                    dir = lst[0]
                    if len(lst) > 1:
                        files = lst[1].split(',')
                    else:
                        files = []
                
                    d[os][version][dir] = files

            return d
        except:
            raise LoadDistroConfFailed, 'Cannot load distro.conf'

    def _checkPathExist(self, p):
        # Checks http/ftp/path. 
      
        if urlparse.urlsplit(p)[0] in ['http', 'ftp']:
            u = URLCheck()
            u.verify(p)
        else:
            if not os.path.exists(p):
                raise InvalidPath, '%s does not exist' % p


    def verify(self, p, os_name, version_name):
        """ verifies a given http/ftp url or local path for a specific distribution """

        if urlparse.urlsplit(p)[0] in ['http', 'ftp']:
            net = True
        else:
            net = False
            if os.path.exists(p):
                root_path = path(p) 
            else:
                raise InvalidPath, '%s does not exists' % p

            
        distroLayout = self.distroLayout[os_name][version_name]

        for dir in distroLayout.keys():
            if distroLayout[dir]: 
                for file in distroLayout[dir]:
                    if net:
                        self._checkPathExist('%s/%s/%s' % (p, dir, file))
                    else:
                        self._checkPathExist(root_path / dir / file)
            else:
                if net:
                    self._checkPathExist('%s/%s/' % (p, dir))
                else:
                    self._checkPathExist(root_path / dir )

