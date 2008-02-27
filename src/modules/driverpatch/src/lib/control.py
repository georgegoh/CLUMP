#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module contains Controller-specific operations for driverpatch. """

from kusu.boot.tool import BootMediaTool
from kusu.util.errors import InvalidPathError, FileDoesNotExistError, InvalidArguments, \
                            UnknownKernelModuleAsset, DirDoesNotExistError, UnknownFileTypeError
from kusu.driverpatch import dkms, kernel
from kusu.util.tools import mkdtemp
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
        
def getKernelVersionfromKo(kofile):
    """ Returns the kernel version from a kofile. 
    """
    cmd1 = 'strings %s' % kofile
    stringP = subprocess.Popen(cmd1,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    cmd2 = 'grep verm'
    grepP = subprocess.Popen(cmd2,shell=True,stdin=stringP.stdout,stdout=subprocess.PIPE)
    out,err = grepP.communicate()
    if out:
        s = out.split('vermagic=')[-1]
        return s.split(' ')[0]
        
def getKernelArchfromKo(kofile):
    """ Returns the kernel arch from a kofile. 
    """
    cmd1 = 'strings %s' % kofile
    stringP = subprocess.Popen(cmd1,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    cmd2 = 'grep verm'
    grepP = subprocess.Popen(cmd2,shell=True,stdin=stringP.stdout,stdout=subprocess.PIPE)
    out,err = grepP.communicate()
    if out:
        s = out.split('vermagic=')[-1]
        # FIXME: change this to regex-foo
        arch = s.split(' ')[3]
        if arch == '586' or arch == '686':
            return 'i' + arch
        else:
            return arch


class KernelModulesCollection(list):
    """ A collection of kernel modules, typically stored in an archive or a directory.
    """
    
    def __init__(self, collectionpath, arch):
        """ The collectionpath can be a directory containing a /lib/modules/`uname-r` 
            subdirectory structure or an archive such as modules.cgz.
        """
        list.__init__(self)
        self.collectionpath = path(collectionpath)
        self.arch = arch
        if not self.validate(): raise InvalidPathError
        #self.populateInitial()
        
    def getCollectionType(self):
        """ Returns the type of collectionpath.
            For modules.cgz, it returns 'modulecgz'
            For module directory, it returns 'moduledir'
            For everything else, it returns ''
        """
        if self.collectionpath.isfile() and self.collectionpath.endswith('.cgz'):
            return 'modulecgz'
        elif self.collectionpath.isdir() and path(self.collectionpath / 'lib/modules').exists():
            return 'moduledir'
        else:
            return ''
        
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
        
    def getModulesFileList(self):
        """ Get the filelist from a kernel module directory.
        """
        
        li = [KernelModule(ko) for ko in self.collectionpath.walkfiles('*.ko')]
        
        return li

    def setupKernelModuleDir(self, dirpath):
        """ Creates a proper directory structure in dirpath for the kernel modules.
        """
            
        dirpath = path(dirpath)
        versionarch = '%s/%s' % (self.getKernelVersion(),self.arch)
        kmoddir = dirpath / versionarch
        if not kmoddir.exists(): kmoddir.makedirs()
        
        return kmoddir
        
    def getKernelVersion(self):
        """ Returns the kernel version.
        """
        if self.getCollectionType() == 'modulecgz':
            tmpdir = path(mkdtemp())
            self.unpack(tmpdir)
            verdir = tmpdir.dirs()[0]
            tmpdir.rmtree()
            return verdir.basename()
        elif self.getCollectionType() == 'moduledir':
            # get the modules directory
            moddir = self.collectionpath / 'lib/modules'
            kverdirs = moddir.dirs()
            if not kverdirs:
                raise UnknownKernelModuleAsset
                
            # FIXME: Only handling single subdirectory under /lib/modules
            return kverdirs[0].basename()
                
                
            

    def getKernelArch(self):
        """ Returns the kernel arch.
        """
        return self.arch
        
    def unpack(self,dirpath):
        """ Unpacks the collection into the dirpath.
        """
        if self.getCollectionType() == 'modulecgz':
            dirpath = path(dirpath).abspath()
            if not dirpath.exists(): dirpath.mkdir()
            
            cmd1 = 'zcat %s' % self.collectionpath
            p1 = subprocess.Popen(cmd1,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
            cmd2 = 'cpio -id'
            p2 = subprocess.Popen(cmd2,shell=True,cwd=dirpath,stdin=p1.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            p2.communicate()
        elif self.getCollectionType() == 'moduledir':
            kmoddir = self.setupKernelModuleDir(dirpath)
            kofiles = [ko for ko in self.collectionpath.walkfiles('*.ko*')]
            for ko in kofiles:
                if not ko.basename() in kmoddir.files():
                    ko.copy(kmoddir)
                
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
        if self.getCollectionType() == 'modulecgz':
            self.extend(self.getModulesCgzFileList())
        elif self.getCollectionType() == 'moduledir':
            self.extend(self.getModulesFileList())
            
        
    def validate(self):
        if not self.collectionpath.exists(): return False
        if self.getCollectionType() != 'modulecgz' and \
            self.getCollectionType() != 'moduledir': 
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
        """ Get the driverpacks entries based on ngid or ngname and installtype.
            installtype defaults to 'package'.
        """

        if not 'id' in kwargs and not 'name' in kwargs:
            raise InvalidArguments, 'id or name not specified!'
            
        installtype = kwargs.get('installtype','package')
        
        _ngid = kwargs.get('id','')
        ngid = None
        if _ngid:
            try:
                ngid = long(_ngid)
            except ValueError:
                raise ValueError, 'id should be a number!'

        ngname = kwargs.get('name','')
            
        # get the list of nodegroups
        ngs = self.dbinst.NodeGroups.select()
        if 'id' in kwargs and ngid:
            # get the components based on ngid
            comps = [ng.components for ng in ngs if ng.ngid == ngid and \
                ng.installtype == installtype]
            
        elif 'name' in kwargs and ngname:
            # get the components based on ngname
            comps = [ng.components for ng in ngs if ng.ngname.find(ngname) > -1 and \
                ng.installtype == installtype]
            
        if not comps: return None

        # get the list of driverpacks

        dpacks = []
        for comp in comps:
            li = [c.driverpacks for c in comp if c.driverpacks]
            for l in li:
                dpacks.extend(l)

        return dpacks


class DriverPatchController(object):
    """ This composition class will be the one typically used by users. """
    
    def __init__(self, dbinst):
        """ Initialize this class. dbinst is an instance of the kusu.core.database.DB class.
        """
        self.bmt = BootMediaTool()  # the unpack/repack routines come from bmt
        self.dm = DataModel(dbinst)
        
        
    def unpackInitrdImage(self, initrdimg, dirpath):
        """ Unpacks the specified initrdimg into dirpath. """
        return self.bmt.unpackRootImg(initrdimg, dirpath)
        
    def packInitrdImage(self, initrdimg, dirpath):
        """ Packs the specified dirpath into initrdimg. """
        return self.bmt.packRootImg(dirpath, initrdimg)
        
    def isKernelPackage(self, packagerpm):
        """ Check if the packagerpm is a kernel package. """
        _krpm = path(packagerpm)
        krpm = kernel.RPMPackage(_krpm)
        
        return krpm.isKernel()
        
    def isKernelModulePackage(self, packagerpm):
        """ Check if the packagerpm is a kernel package. """
        _krpm = path(packagerpm)
        krpm = kernel.RPMPackage(_krpm)

        return krpm.isKernelModule()
            
    def hasPciUpdates(self, packagerpm):
        """ Check if the packagerpm is a kernel package. """
        _krpm = path(packagerpm)
        krpm = kernel.RPMPackage(_krpm)

        return krpm.hasPciUpdates()
                
    def hasPcitable(self, packagerpm):
        """ Check if the packagerpm is a kernel package. """
        _krpm = path(packagerpm)
        krpm = kernel.RPMPackage(_krpm)

        return krpm.hasPcitable()
        
    def extractPciUpdates(self, packagerpm, destdir):
        """ Check if the packagerpm is a kernel package. """
        _krpm = path(packagerpm)
        krpm = kernel.RPMPackage(_krpm)

        return krpm.extractPciUpdates(destdir)
            
    def extractPcitable(self, packagerpm, destdir):
        """ Check if the packagerpm is a kernel package. """
        _krpm = path(packagerpm)
        krpm = kernel.RPMPackage(_krpm)

        return krpm.extractPcitable(destdir)        


    def patchPciIds(self, packagerpm, original, pciupdates):
        """ Check if the packagerpm is a kernel package. """
        _krpm = path(packagerpm)
        krpm = kernel.RPMPackage(_krpm)

        return krpm.patchPciIds(original, pciupdates)        
        
    def copyKernel(self, kernelrpm, destdir, kernelname=''):
        """ Copy the kernel image found in kernelrpm to destdir.
            If kernelname is specified, copy the image as the kernelname
        """
        kernelrpm = path(kernelrpm)
        krpm = kernel.RPMPackage(kernelrpm)
        return krpm.extractKernel(destdir,kernelname)
        
    def extractKernelModulesDir(self, kernelrpm, destdir):
        """ Extracts the kernel modules directory found in kernelrpm to destdir.
        """
        kernelrpm = path(kernelrpm)
        krpm = kernel.RPMPackage(kernelrpm)
        krpm.extractKernelModulesDir(destdir)
        
    def convertKmodDirToModulesArchive(self, kmoddir, modulearchive, arch):
        """ Converts kernel module directory into a modulearchive file 
            (e.g modules.cgz).
        """
        col = KernelModulesCollection(kmoddir,arch)
        tmpdir = path(mkdtemp())
        col.unpack(tmpdir)
        col.pack(tmpdir,modulearchive)
        
    def getKernelVersion(self, kmoddir, arch):
        """ Returns the kernel version.
        """
        col = KernelModulesCollection(kmoddir, arch)
        return col.getKernelVersion()
        
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
        
    def updateKernelModulesAssets(self, assetsdict, dirpath):
        """ Updates the initrd dirpath with the assetsdict.
            The structure of the assetsdict are as follows:
            
            {   'module-info': 'filepath of the module-info',
                'modules.alias': 'filepath of the modules.alias',
                'modules.dep': 'filepath of the modules.dep',
                'pci.ids': 'filepath of the pci.ids'
            }
        """
        dirpath = path(dirpath).abspath()
        if not dirpath.exists(): raise DirDoesNotExistError, dirpath
        modulespath = dirpath / 'modules'
        if not modulespath.exists(): raise DirDoesNotExistError, modulespath
        
        assets = ['module-info', 'modules.alias', 'modules.dep', 
                'modules.cgz','pci.ids']

        li = [k for k in assetsdict.keys() if k in assets]
        if not li: raise UnknownKernelModuleAsset, assetsdict
        for l in li:
            if not assetsdict[l]:
                continue
            f = path(assetsdict[l])
            
            if not f.exists(): FileDoesNotExistError, f
            if f.basename() <> l: raise UnknownFileTypeError, f
            f.copy(modulespath)


    def getDriverPacks(self, **kwargs):
        return self.dm.getDriverPacks(**kwargs)
        

        

        
