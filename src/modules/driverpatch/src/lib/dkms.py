#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module handles driverpatch operations dealing with DKMS
    (http://linux.dell.com/dkms/dkms.html). 
"""


from path import path
from kusu.util.errors import FileDoesNotExistError
from kusu.util import rpmtool, tools
import tarfile

FILE_EXTS = ['tgz','tbz2','tar.gz','tar.bz2','gz','bz2']

class RPMPackage(object):

        def __init__(self, filepath):
            """ Initializes this class with the filepath of the DKMS rpm package.
            """
            if not path(filepath).exists: raise FileDoesNotExistError
            self.filepath = path(filepath).abspath()
            self.rpmfile = rpmtool.RPM(str(self.filepath))
            
        def getKernelModuleName(self):
            """ Returns the module name contained in this package. 
            """
            # FIXME: this is totally relying on the name of the rpm
            # package is really the name of the module too. Which is
            # dangerous and silly

            return self.rpmfile.name
            
        def getKernelModuleVersion(self):
            """ Returns the module version string.
            """
            # FIXME: this is totally relying on the version of the rpm
            # package is really the version of the module too. Which is
            # dangerous and silly
            
            return self.rpmfile.version
            
        def verifyDKMSArchive(self, archive):
            """ Checks the tarball is a dkms archive. """
            archive = path(archive)
            tmpdir = path(tools.mkdtemp())
            pkg = tarfile.open(archive)
            for p in pkg:
                pkg.extract(p,tmpdir) 
                
            li = [f for f in tmpdir.dirs('dkms_main_tree')]
            tmpdir.rmtree()
            
            if not li:
                return False
            else:
                return True
            
        def getDKMSArchives(self):
            """ Returns the list of the dkms tarballs contained in the package.
            """
            tmpdir = path(tools.mkdtemp(prefix='driverpatch-dkms-'))
            self.unpack(tmpdir)
            li = []
            for f in tmpdir.walkfiles():
                if tarfile.is_tarfile(f) and self.verifyDKMSArchive(f):
                    li.append(f.basename())

            if tmpdir.exists(): tmpdir.rmtree()
            
            return li
            
        def unpack(self, destdir):
            """ Unpacks the package into destdir. 
            """
            self.rpmfile.extract(destdir)
            
        def unpackDKMSArchive(self, archive, destdir):
            """ Unpacks the dkms archive into destdir. 
            """
            destdir = path(destdir).abspath()
            if not destdir.exists(): destdir.mkdir()
            
            tmpdir = path(tools.mkdtemp())
            self.unpack(tmpdir)
            li = [f for f in tmpdir.walkfiles(archive)]
            if not li: 
                if tmpdir.exists(): tmpdir.rmtree()
                raise FileDoesNotExistError, archive
            
            # the first entry should be the path of the archive
            pkg = tarfile.open(li[0])
            for p in pkg:
                pkg.extract(p,destdir)
                
            if tmpdir.exists(): tmpdir.rmtree()

            
        def getKernelModuleFiles(self):
            """ Returns a list of containing tuples of the kofile, kernel version and arch.
            """
            # get the dkms archives
            li = self.getDKMSArchives()
            
            tmpdir = path(tools.mkdtemp())
            for l in li: self.unpackDKMSArchive(l,tmpdir)
            
            _kofiles = [(d.dirname().split('dkms_main_tree/')[-1],d.basename()) for d in tmpdir.walkfiles('*.ko')]

            kofiles = []
            for k in _kofiles:
                s,ko = k
                if s.endswith('/module'):
                    _s = s[0:-7] # we want everything until /module
                    kver,arch = _s.split('/')
                    kofiles.append((ko,kver,arch))

            if tmpdir.exists(): tmpdir.rmtree()
            
            return kofiles
            
        def extractKernelModuleFile(self, kofile, kver, arch, destdir):
            """ Extracts the kernel module kofile matching the kernel version and arch 
                to destdir. 
            """

            # get the dkms archives
            li = self.getDKMSArchives()

            tmpdir = path(tools.mkdtemp())
            for l in li: self.unpackDKMSArchive(l,tmpdir)
            
            _kofiles = [d for d in tmpdir.walkfiles(kofile)]
            if not _kofiles:
                if tmpdir.exists(): tmpdir.rmtree()
                raise FileDoesNotExistError, kofile
                
            kofiles = [k for k in _kofiles if k.find('%s/%s' % (kver,arch)) > -1]
            if not kofiles:
                if tmpdir.exists(): tmpdir.rmtree()
                raise FileDoesNotExistError, kofile
                
            for k in kofiles:
                destdir = path(destdir).abspath()
                if not destdir.exists(): destdir.makedirs()                
                k.copy(destdir)
            
        


