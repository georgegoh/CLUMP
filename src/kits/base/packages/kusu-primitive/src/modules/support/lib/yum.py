#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# 
# $Id$ 
# 
# Copyright (C) 2010 Platform Computing Inc. 
# 

import sys
import md5
import sha
import gzip
import StringIO
import tempfile

from path import path

from primitive.support import rpmtool
from primitive.support.proxy import Proxy
from primitive.fetchtool.commands import FetchCommand

version_info = sys.version_info[:2]

if version_info < (2,5):
    try:
        import cElementTree
    except:
        import ElementTree
elif version_info >= (2,5):
    try:
        from xml.etree import cElementTree
    except:
        from xml.etree import ElementTree

class YumRepo:

    def __init__(self, uri, proxy=None):
        self.uri = uri
        self.repo = {}
        self.primary = {}
        self.proxy = proxy


    def getRepoMD(self):
        """Get the repodata index file"""

        repomd = self.uri + '/repodata/repomd.xml'

        tmpdir = path(tempfile.mkdtemp(prefix='yumrepo', dir='/tmp'))

        fc = FetchCommand(uri=repomd,
                          fetchdir=False,
                          proxy=self.proxy,
                          destdir=tmpdir,
                          overwrite=False)
        status , dest = fc.execute()

        f = open(tmpdir / 'repomd.xml')

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
                
        self.cleanup(tmpdir)
        return self.repo

    def getPrimary(self):
        """Get the primary list from repodata"""

        if not self.repo:
            self.getRepoMD()

        primaryFile = self.uri + '/' + self.repo['primary']['location']
        
        checksumType = self.repo['primary']['checksum'][0]
        checksum = self.repo['primary']['checksum'][1]

        tmpdir = path(tempfile.mkdtemp(prefix='yumrepo', dir='/tmp'))

        fc = FetchCommand(uri=primaryFile,
                          fetchdir=False,
                          proxy=self.proxy,
                          destdir=tmpdir,
                          overwrite=False)
        status , dest = fc.execute()

        primaryFile = open(tmpdir / path(self.repo['primary']['location']).basename())

        if self.getCheckSum(checksumType, primaryFile) == checksum:
            primaryFile.seek(0)
            blob = StringIO.StringIO(gzip.GzipFile(fileobj=primaryFile).read())

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

                self.cleanup(tmpdir)
                return self.primary

            else:
                self.cleanup(tmpdir)
                raise repodataChecksumException, primaryFile
        else:
            self.cleanup(tmpdir)
            raise repodataChecksumException, primaryFile
        
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


    def cleanup(self, tmpdir):
        if tmpdir.exists():
            tmpdir.rmtree()


