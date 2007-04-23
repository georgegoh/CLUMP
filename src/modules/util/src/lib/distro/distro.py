#!/usr/bin/env python
#
# $Id: distro.py 203 2007-03-29 12:18:16Z ltsai $
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import os
import urlparse
import ConfigParser
from urlcheck import URLCheck, HTTPError
from path import path

class CheckDistro:
    dirlayout = {}
    filelayout = {}
    distroLayout = {}

    def __init__(self):
        self.dirlayout['repodatadir'] = 'repodata'
        self.dirlayout['imagesdir'] = 'images'
        self.dirlayout['isolinuxdir'] = 'isolinux'
        self.dirlayout['rpmsdir'] = 'Fedora/RPMS'
        self.dirlayout['basedir'] = 'Fedora/base'

        self.filelayout['repodatadir'] = ['comps.xml', \
                                         'filelists.xml.gz', \
                                         'other.xml.gz', \
                                         'primary.xml.gz', \
                                         'repomd.xml']
        self.filelayout['imagesdir'] = ['stage2.img']
        self.filelayout['basedir'] = ['comps.xml']

        self.distroLayout['fedora'] = {}
        self.distroLayout['fedora']['6'] = {'self.dirlayout':self.dirlayout,'filelayout':self.filelayout}
      
    def _loadConf(self, filename):
        config = ConfigParser.RawConfigParser()
        f = open()
        config.readfp(filename)
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

    def _checkPathExist(self, p):
        # Checks http/ftp/path. 
       
        if urlparse.urlsplit(p)[0] in ['http', 'ftp']:
            u = URLCheck()
            u.verify(p)
        else:
            if not os.path.exists(p):
                raise Exception, (p,)


    def verify(self, p, os, version):

        original_p = path(p)
        
        for k,v in self.distroLayout[os][version]['self.dirlayout'].iteritems():
            p = original_p / v
            if self.distroLayout[os][version]['filelayout'].has_key(k):
                for f in self.distroLayout[os][version]['filelayout'][k]:
                    self._checkPathExist(p / f)
            else:
                self._checkPathExist(p)


