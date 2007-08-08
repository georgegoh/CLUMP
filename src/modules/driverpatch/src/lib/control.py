#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module contains Controller-specific operations for driverpatch. """

from kusu.boot.tool import BootMediaTool
from kusu.util.errors import InvalidPathError, FileDoesNotExistError, InvalidArguments
from path import path
import subprocess

# constants
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
        self.populateInitial()
        
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
        
    def unpack(self,dirpath):
        """ Unpacks the collection into the dirpath. """
        dirpath = path(dirpath).abspath()
        if not dirpath.exists(): dirpath.mkdir()
            
        cmd1 = 'zcat %s' % self.collectionpath
        p1 = subprocess.Popen(cmd1,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        cmd2 = 'cpio -id'
        p2 = subprocess.Popen(cmd2,shell=True,cwd=dirpath,stdin=p1.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p2.communicate()
                
    def pack(self, dirpath, collectionpath):
        """ Packs the dirpath contents back into a collectionpath.
        """
        dirpath = path(dirpath).abspath()
        collectionpath = path(collectionpath).abspath()
        
        cmd1 = 'find . -type f'
        p1 = subprocess.Popen(cmd1,shell=True,cwd=dirpath,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        cmd2 = 'cpio --quiet -H crc -o'
        p2 = subprocess.Popen(cmd2,shell=True,cwd=dirpath,stdin=p1.stdout,stdout=subprocess.PIPE)
        cmd3 = 'gzip -9 > %s' % collectionpath
        p3 = subprocess.Popen(cmd3,shell=True,cwd=dirpath,stdin=p2.stdout,stdout=subprocess.PIPE)
        p3.communicate()

        
    def populateInitial(self):
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
        self._kmodpath = path(kmodpath)
        self.kmodname = self._kmodpath.basename()
        self.kernelversion = ''
        self.kernelarch = ''

    def setup(self):
        cmd =  'strings %s' % self._kmodpath
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

class DataModel(object):
    """ Convenience class for the data operations.
    """
    
    def __init__(self, dbinst):
        """ Initialize this class. dbinst is an instance of the kusu.core.database.DB class.
        """
        self.dbinst = dbinst
        
    def getDriverPacks(self, **kwargs):
        """ Get the driverpacks entries based on ngid or ngname.
        """

        if not 'id' in kwargs and not 'name' in kwargs:
            raise InvalidArguments, 'id or name not specified!'
        
        _ngid = kwargs.get('id','')
        if _ngid:
            try:
                ngid = long(_ngid)
            except ValueError:
                raise ValueError, 'id should be a number!'

        ngname = kwargs.get('name','')
            
        # get the list of nodegroups
        ngs = self.dbinst.NodeGroups.select()
        
        if 'id' in kwargs:
            # get the components based on ngid
            comps = [ng.components for ng in ngs if ng.ngid == ngid]
            
        elif 'name' in kwargs:
            # get the components based on ngname
            comps = [ng.components for ng in ngs if ng.ngname.find(ngname) > -1]
            
        if not comps: return None

        # get the list of driverpacks
        # the first list contains the list of components associated with nodegroup
        dpacks = []
        for comp in comps:
            # and the second list contains the driverpacks associated with each component list
            li = [c.driverpacks for c in comp if c.driverpacks]
            for l in li:
                dpacks.extend(l)

        return dpacks


class DriverPatchController(object):
    """ This composition class will be the one typically used by users. """
    
    def __init__(self):
        self.bmt = BootMediaTool()  # the unpack/repack routines come from bmt
        
    def unpackInitrdImage(self, initrdimg, dirpath):
        """ Unpacks the specified initrdimg into dirpath. """
        return self.bmt.unpackRootImg(self, initrdimg, dirpath)
        
    def packInitrdImage(self, initrdimg, dirpath):
        """ Packs the specified dirpath into initrdimg. """
        return self.bmt.packRootImg(dirpath, initrdimg)
        
    def getKernelModulesCgz(self, dirpath):
        """ Locate the modules.cgz in the dirpath. """
        dirpath = path(dirpath).abspath()
        li = [f for f in dirpath.walkfiles('modules.cgz')]
        if not li: raise FileDoesNotExistError
        return li[0]
        
    def getKernelModulesAssets(self, dirpath):
        """ Locate modules assets: module-info, modules.alias, modules.dep,
            pci.ids. Returns a dict containing the asset as the key and 
            path of that asset as the value.
        """
        dirpath = path(dirpath).abspath()
        assets = ['module-info', 'modules.alias', 'modules.dep', 'pci.ids']
        d = {}
        for asset in assets:
            li = [f for f in dirpath.walkfiles(asset)]
            if not li:
                v = ''
            else:
                v = li[0]
            d[asset] = v
            
        return d
        

        
