#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.

"""This module handles operations relating to booting up nodes."""

from path import path
from kusu.boot.distro import DistroFactory
from kusu.util.tools import cpio_copytree
from kusu.util.errors import FilePathError, InvalidInstallSource, ToolNotFound, \
                            UnsupportedPackingType, NotPriviledgedUser
import os
import re
import tempfile
import subprocess

ROOTIMG_PACKING_TYPE = ['cpio','ext2', 'gzip']

TOOLS_DEPS = ['cpio', 'mount', 'umount', 'file', 'strings', 'zcat', 
    'mkisofs', 'tar', 'gzip']


def checkToolDeps(tool):
    """ Check if the tool is indeed available. A ToolNotFound exception 
        will be thrown if any of the tools are missing.
    """
    
    cmd = 'which %s > /dev/null 2>&1' % tool
    whichP = subprocess.Popen(cmd,shell=True)
    whichP.communicate()
    if whichP.returncode <> 0:
        raise ToolNotFound, tool
        
    return True
            
def checkAllToolsDeps():
    """ Check if the list of tools needed by BMT are indeed available. 
        A ToolNotFound exception will be thrown if any of the tools are
        missing.
    """

    for tool in TOOLS_DEPS:
        checkToolDeps(tool)
        
    return True


def packInitramFS(dirname, rootimgpath, initscript=None):
    """Packs the directory dir into an initramfs rootimgpath. The initscript template file can be passed as well.
       Refer to Linux Kernel Documentation/filesystems/ramfs-rootfs-initramfs.txt for more information.
    """
    
    if not path(dirname).exists(): 
        raise FilePathError
    
    if os.getuid() <> 0: raise NotPriviledgedUser, "Operation requires root access!"
    
    # check tools dependencies
    for tool in ['find', 'cpio', 'gzip']:
        checkToolDeps(tool)
    
    # nuke existing rootimgpath if existing
    if path(rootimgpath).exists(): path(rootimgpath).remove()
    
    cwd = path(dirname)
    findP = subprocess.Popen("find .",cwd=cwd,shell=True,stdout=subprocess.PIPE)
    cpioP = subprocess.Popen("cpio -o -H newc --quiet",cwd=cwd,shell=True,stdin=findP.stdout,stdout=subprocess.PIPE)
    gzipP = subprocess.Popen("gzip > %s" % rootimgpath,shell=True,stdin=cpioP.stdout)
    gzipP.communicate()
    
    return gzipP.returncode
    
def packExt2FS(dirname, rootimgpath, size=5000):
    """Packs the directory dir into an ext2fs rootimgpath. The size of the image can be passed as well.
    """

    if not path(dirname).exists(): 
        raise FilePathError

    if os.getuid() <> 0: raise NotPriviledgedUser, "Operation requires root access!"

    # check tools dependencies
    for tool in ['dd', 'mke2fs', 'mount', 'mount']:
        checkToolDeps(tool)

    # nuke existing rootimgpath if existing
    if path(rootimgpath).exists(): path(rootimgpath).remove()
    
    rootimgpath = path(rootimgpath).abspath()

    # create scratchdir
    scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
    tmprootdir = path(tempfile.mkdtemp(dir=scratchdir))

    # create a block device, format it, mount it
    cwd = path(scratchdir)
    ddP = subprocess.Popen("dd of=%s if=/dev/zero bs=1024 count=%s >/dev/null 2>&1" % (rootimgpath,size),shell=True,cwd=scratchdir)
    ddP.communicate()
    mke2fsP = subprocess.Popen("mke2fs -F %s >/dev/null 2>&1" % rootimgpath,shell=True,cwd=scratchdir)
    mke2fsP.communicate()
    mountP = subprocess.Popen("mount -o loop %s %s" % (rootimgpath,tmprootdir),shell=True,cwd=scratchdir)
    mountP.communicate()
    
    # copy the contents over to the newly made ext2fs filesystem
    cpio_copytree(dirname,tmprootdir)
    
    # housecleaning
    umountP = subprocess.Popen("umount %s" % tmprootdir,shell=True,cwd=scratchdir)
    umountP.communicate()
    if tmprootdir.exists(): tmprootdir.rmtree()
    if scratchdir.exists(): scratchdir.rmtree()
    
    
def unpack(rootimgpath, dirname):
    """Unpacks the file rootimgpath into the directory dir."""
    
    if not path(rootimgpath).exists(): raise FilePathError
    
    if os.getuid() <> 0: raise NotPriviledgedUser

    # check tools dependencies
    for tool in ['zcat', 'cpio', 'mount', 'mount']:
        checkToolDeps(tool)
    
    # nuke existing dirname
    if path(dirname).exists(): path(dirname).rmtree()
    
    # create scratchdir
    scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
    rootimg = scratchdir / path(rootimgpath).splitext()[0].basename()
    tmprootdir = path(tempfile.mkdtemp(dir=scratchdir))
        
    # create an OperatingEnvironment object with just the rootimgpath
    obj = OperatingEnvironment(rootimgpath=rootimgpath)
    
    packType1 = ['cpio', 'gzip']
    packType2 = ['ext2', 'gzip']
    
    packType1.sort()
    packType2.sort()
    
    format = obj.getRootImgFormat()
    format.sort()

    try:
        if format == packType1:
            cmd = 'zcat %s > %s' % (rootimgpath,rootimg)
            launchCmd(cmd)
            cmd = 'cd %s && cpio --quiet -I %s -id' % (tmprootdir,rootimg)
            launchCmd(cmd)
            cpio_copytree(tmprootdir,dirname)
            scratchdir.rmtree()
        elif format == packType2:
            cmd = 'zcat %s > %s' % (rootimgpath,rootimg)
            launchCmd(cmd)
            cmd = 'mount -o loop -t ext2 %s %s' % (rootimg,tmprootdir)
            launchCmd(cmd)
            cpio_copytree(tmprootdir,dirname)
            cmd = 'umount %s' % tmprootdir
            launchCmd(cmd)
            scratchdir.rmtree()
        else:
            scratchdir.rmtree()
            raise UnsupportedPackingType
    except (UnsupportedPackingType, IOError), e:
        scratchdir.rmtree()
        raise e
        
def makeImagesDir(srcpath, destdir, patchfile=None, overwrite=False):
    """ Create the images directory given the installation source. Also puts in the patchfile image if available. """
    
    srcpath = path(srcpath)
    destdir = path(destdir)
    if patchfile: patchfile = path(patchfile)
    
    obj = DistroFactory(srcpath)
    try:
        stage2img = obj.getStage2Path()
    except AttributeError:
        raise InvalidInstallSource, "Installation source not supported!"
        
    if not stage2img.exists(): raise FilePathError, "stage2.img not found within %s!" % srcpath
    
    if not destdir.exists(): destdir.mkdir()
    
    # copy the stage2.img into the destdir
    obj.copyStage2(destdir,overwrite)
        
    if patchfile and patchfile.exists(): patchfile.copy(destdir)
    
    
def makeISOLinuxDir(isolinuxdir, oenvobj=None, isolinuxbin=None):
    """Create, or update if already existing, isolinux directory. Also updates the isolinux.cfg file accordingly."""
    
    labels = {}
    tdir = path(isolinuxdir)
    isolinuxcfg = tdir / 'isolinux.cfg'
    
    if not path(isolinuxbin).exists(): raise FilePathError, "Requires isolinux.bin file!"
    
    if not tdir.exists(): 
        tdir.mkdir()
    elif isolinuxcfg.exists():
        # read in the existing isolinux.cfg file and create a dict based on the
        # label being the key and the following label subentries as the value.
        li = open(isolinuxcfg).read().split("label")[1:]
        li2 = []
        for l in li: li2.append(l.strip())
        li = li2
        for l in li:
            k = l.split('\n')
            li2 = []
            for i in k[1:]:
                li2.append(i.strip())
            labels[k[0]] = tuple(li2)
    
    kernelname = oenvobj.kernelpath.basename()
    rootimgname = oenvobj.rootimgpath.basename()
    ostype = oenvobj.ostype
    
    # create the label entry based on oenvobj
    labels[ostype] = ('kernel %s' % kernelname, 'append initrd=%s' % rootimgname)
    
    isolinuxcfgTmpl = []
    isolinuxcfgTmpl.append("prompt 1\n")
    isolinuxcfgTmpl.append("timeout 600\n")
    for k,v in labels.items():
        isolinuxcfgTmpl.append('label %s\n' % k)
        for i in v:
            isolinuxcfgTmpl.append('  %s\n' % i)
    isolinuxcfgTmpl.append('\n')
    
    # copy the kernel, initrd and the isolinux.bin to the isolinuxdir
    oenvobj.kernelpath.copy(tdir)
    oenvobj.rootimgpath.copy(tdir)
    path(isolinuxbin).copy(tdir)
    
    # nuke the original isolinux.cfg if existing
    if isolinuxcfg.exists(): isolinuxcfg.remove()
    
    # generate the new isolinux.cfg
    f = open(isolinuxcfg, 'w')
    f.writelines(isolinuxcfgTmpl)
    f.close()
    
     
def makeBootISO(isodir, isoname, volname="BootKit"):
    """Create a bootable ISO isoname out of the directory isodir. The volname can be used to specify
       the ISO label name.
    """
    
    tdir = path(isodir)
    isopath = path(isoname)
    if not tdir.exists(): raise FilePathError
    
    # check tools dependencies
    checkToolDeps('mkisofs')
    
    # create a clean scratch directory for mkisofs operations
    scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
    cpio_copytree(tdir,scratchdir)
    
    # nuke existing iso file if any
    if isopath.exists(): isopath.remove()
    
    options = '-c isolinux/boot.cat \
    -b isolinux/isolinux.bin \
    -V %s\
    -quiet \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    -R -r -T -f -l \
    -o %s %s' %  (volname,isopath,scratchdir)
    
    isoP = subprocess.Popen('mkisofs %s > /dev/null 2>&1' % options,shell=True,cwd=scratchdir)
    isoP.communicate()
    
    # cleanup
    scratchdir.rmtree()
    
    return isoP.returncode
    

def makeBootArchive(isolinuxdir, archivename):
    """Create a .tgz archive that contains the isolinuxdir. This bootarchive can be utilized by buildkit/kitscript for
       making bootable Kits. Note that the archive does not contain an initial isolinux-like subdirectory, only the 
       contents of the isolinuxdir will be archived.
    """
    
    tdir = path(isolinuxdir)
    
    if not tdir.exists(): raise FilePathError
    
    # check tools dependencies
    for tool in ['tar', 'gzip']:
        checkToolDeps(tool) 
    
    # nuke existing archivename if any
    if path(archivename).exists(): path(archivename).remove()
    
    tarP = subprocess.Popen('tar cf - .',cwd=tdir,shell=True,stdout=subprocess.PIPE)
    gzipP = subprocess.Popen("gzip > %s" % archivename,shell=True,stdin=tarP.stdout)
    gzipP.communicate()
    
    return gzipP.returncode
    
def launchCmd(cmd,*args):
    """External command launcher. args is a tuple of arguments to be passed to cmd.
       NOTE: This really should be moved to a common utility module.
    """
    
    cmdstr = "%s %s" % (cmd, ' '.join(args))
    cmdP = subprocess.Popen(cmdstr,shell=True,stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    value = cmdP.communicate()[0]
    
    return value
    
class OperatingEnvironment(object):
    """An OperatingEnvironment is a set of environement that contains the kernel and initial ramdisks. It also contains related
       methods and attributes. A RootImg refers to the initrd or initramfs image file.
    """
    def __init__(self, kernelpath=None, rootimgpath=None, ostype=None):
        """The following attributes should be defined:
        
           self.ostype - Refers to the type of OS or Distro. It should be in lowercase for consistency. 
                         It will be used for comparison cases.
           self.kernelpath - Path of the kernel file.
           self.rootimgpath - Path of the initrd/initramfs image file.
        """
        
        self.kernelpath = path(kernelpath)
        self.rootimgpath = path(rootimgpath)
        self.ostype = ostype
        
        
    def getUnameString(self):
        """Returns the uname string from the kernel file"""
        unameRE = re.compile (r'\w+.*\(\w+@.+\).+', flags=re.MULTILINE)
        value = launchCmd('strings', self.kernelpath)
        
        unamestr = None
        for i in value[1].split('\n'):
            k = unameRE.search(i)
            if k: unamestr = k.group()
            
        return unamestr
        
        
    def getKernelVersion(self):
        """Returns the version string of the kernel."""
        
        unamestr = self.getUnameString()
        if not unamestr: return None
        li = unamestr.split()
        
        return li[0]
        
    def getArch(self):
        """Returns the arch for this environment."""
        pass
        
    def getRootImgFormat(self):
        """Returns the packing format of the RootImg."""
        global ROOTIMG_PACKING_TYPE
        
        # check tools dependencies
        checkToolDeps('file')       
        
        if not self.rootimgpath.exists(): raise FilePathError
        
        value = launchCmd('file', '-z -k', self.rootimgpath)
        li = []
        # check if any elements in the ROOTIMG_PACKING_TYPE exists
        for i in ROOTIMG_PACKING_TYPE:
            if value.find(i) > -1:
                li.append(i)
                
        if not li: return None
        
        return li
            
                
        
        
        
