#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module contains Controller-specific operations for driverpatch. """

from kusu.boot.tool import BootMediaTool
from kusu.util.errors import InvalidPathError
from path import path
import subprocess

IMAGE_FORMAT_TYPES = ['cpio','gzip']

def checkFormat(filepath):
    """ Check if the image format is supported. Returns True if it is or False if not.
    """
    cmd = 'file -z -k %s' % filepath
    p = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    out, err = p.communicate()

    li = [fmt for fmt in IMAGE_FORMAT_TYPES if out.find(fmt) > -1]
    if not li: return False
    
    if li == IMAGE_FORMAT_TYPES: 
        return True
    else:
        return False

class KernelModulesCollection(list):
    """ A collection of kernel modules, typically stored in an archive or a directory.
    """
    
    def __init__(self, collectionpath):
        """ The collectionpath can be a directory such as /lib/modules/`uname-r` 
            or an archive such as modules.cgz.
        """
        list.__init__(self)
        self.collectionpath = path(collectionpath)
        if not self.validate(): raise InvalidPathError
        self.populate()
        
    def getModulesCgzFileList(self):
        """ Get the filelist of modules.cgz. This is only the list and not the actual files.
            Returns a list.
        """
        li = []
        cmd1 = 'zcat %s' % self.collectionpath
        p1 = subprocess.Popen(cmd1,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        cmd2 = 'cpio -t'
        p2 = subprocess.Popen(cmd2,shell=True,stdin=p1.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err = p2.communicate()
        if out:
            _li = out.split('\n')
            li = [KernelModule(l) for l in _li if l]
            
        return li
        
    def populate(self):
        """ Populates the kmods list. """
        if self.collectionpath.isfile():
            self.extend(self.getModulesCgzFileList())
        
    def validate(self):
        if not self.collectionpath.exists(): return False
        if self.collectionpath.isfile() and \
            not self.collectionpath.endswith('.cgz'): 
            return False
        
        if self.collectionpath.isfile() and \
            not checkFormat(self.collectionpath):
            return False

        return True

        

class KernelModule(object):

    def __init__(self, kmodpath):
        self.kmodpath = path(kmodpath).abspath()
        self.kmodname = self.kmodpath.basename()
        self.kernelversion = ''
        self.kernelarch = ''

    def setup(self):
        cmd =  'strings %s' % self.kmodpath
        p1 = subprocess.Popen(cmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        cmd = 'grep vermagic'
        p2 = subprocess.Popen(cmd,shell=True,stdin=p1.stdout,stdout=subprocess.PIPE)
        out, err = p2.communicate()
        line = out.split('=')[1]
        self.kernelversion = line[0]
        self.kernelarch = line[3]

    def getVersion(self):
        """ Returns the kernel version string. """
        if not self.kernelversion:
            self.setup()

        return self.kernelversion
        
    def getArch(self):
        """ Returns the kernel arch string. """
        if not self.kernelarch:
            self.setup()
            
        return self.kernelarch
        
    def __repr__(self):
        return "<KernelModule:'%s'>" % self.kmodname


class DriverPatchController(object):
    
    def __init__(self):
        self.bmt = BootMediaTool()  # the unpack/repack routines come from bmt
        
    def unpackInitrdImage(self, initrdimg, dirpath):
        """ Unpacks the specified initrdimg into dirpath. """
        return self.bmt.unpackRootImg(self, initrdimg, dirpath)
        
    def packInitrdImage(self, initrdimg, dirpath):
        """ Packs the specified dirpath into initrdimg. """
        return self.bmt.packRootImg(dirpath, initrdimg)
        
