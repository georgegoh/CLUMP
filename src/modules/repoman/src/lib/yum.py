#!/usr/bin/env python
#
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import cElementTree
import md5
import sha
import gzip
import StringIO
from path import path

from kusu.util import rpmtool
from kusu.util.errors import *
from kusu.repoman import tools

class YumRepo:

    def __init__(self, uri):
        self.uri = uri
        self.repo = {}
        self.primary = {}

    def getRepoMD(self):
        """Get the repodata index file"""

        repomd = self.uri + '/repodata/repomd.xml'

        f = StringIO.StringIO(tools.getFile(repomd))
        for event, elem in cElementTree.iterparse(f): 
            if self.cleanNS(elem) == 'data':
                type = elem.get('type')
                if not self.repo.has_key(type):
                    self.repo[type] = {'location': '',
                                       'checksum': '',
                                       'timestamp': '',
                                       'open-checksum': ''}

                for elem in elem.getchildren():
                    tag = self.cleanNS(elem)

                    if tag == 'location':
                        self.repo[type]['location'] = elem.get('href')
                    elif tag == 'checksum':
                        self.repo[type]['checksum'] = (elem.get('type'),elem.text)
                    elif tag == 'timestamp':
                        self.repo[type]['timestamp'] = elem.text
                    elif tag =='open-checksum':
                        self.repo[type]['open-checksum'] = (elem.get('type'),elem.text)
                    else: pass

        return self.repo

    def getPrimary(self):
        """Get the primary list from repodata"""

        if not self.repo:
            self.getRepoMD()

        primaryFile = self.uri + '/' + self.repo['primary']['location']
        
        checksumType = self.repo['primary']['checksum'][0]
        checksum = self.repo['primary']['checksum'][1]

        if self.getCheckSum(checksumType, primaryFile) == checksum:
            blob = StringIO.StringIO(gzip.GzipFile(fileobj=StringIO.StringIO(tools.getFile(primaryFile))).read())

            checksumType = self.repo['primary']['open-checksum'][0]
            checksum = self.repo['primary']['open-checksum'][1]

            if self.getCheckSum(checksumType, blob) == checksum:
                blob.seek(0)
                for event, elem in cElementTree.iterparse(blob): 
                    if self.cleanNS(elem) == 'package':
                        for elem in elem.getchildren():
                            tag = self.cleanNS(elem)

                            if tag == 'name':
                                name = elem.text
                            elif tag == 'version':
                                version = elem.get('ver')
                                release = elem.get('rel')
                                epoch = elem.get('epoch')
                                if epoch: epoch = int(epoch)
                            elif tag == 'arch':
                                arch = elem.text
                            elif tag == 'location':
                                filename = self.uri + '/' + elem.get('href')

                        r = rpmtool.RPM(name=name, 
                                        version=version,
                                        release=release,
                                        arch=arch,
                                        epoch=epoch,
                                        filename=filename)

                        if not self.primary.has_key(name):
                            self.primary[name] = {}

                        if not self.primary[name].has_key(arch):
                           self.primary[name][arch] = []

                        self.primary[name][arch].append(r)

                return self.primary

            else:
                raise repodataChecksumError, primaryFile
        else:
            raise repodataChecksumError, primaryFile
        
    def cleanNS(self, elem):
        """Clean up namespace"""
        tag = elem.tag

        if tag.find('}') == -1: 
            return tag
        else:
            return tag.split('}')[1]

    def getCheckSum(self, checksumType, file):
        """Get the md5 or sha checksum from a file object 
           The file param can be a regular filename, URI, a StringIO 
           object, or any other object which simulates a file."""

        blksize = 1024

        if type(file) in [str, unicode]:
            #f = open(file, 'rb', blksize)
            f = StringIO.StringIO(tools.getFile(file))
        else:
            f = file
        
        if checksumType == 'md5':
            sum = md5.new()
        else:
            sum = sha.new()
        
        block = True
        while block:
            block = f.read(blksize)
            sum.update(block)

        return sum.hexdigest()



