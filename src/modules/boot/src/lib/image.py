#!/usr/bin/env python
# $Id: image.py 194 2007-03-29 07:36:10Z najib $
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE for details.

"""This module handles operations relating to booting up nodes."""

from path import path
import os
import sys
import commands
import re
import tempfile
import subprocess

ROOTIMG_PACKING_TYPE = ['cpio','ext2', 'gzip']

TOOLS_DEPS = ['cpio', 'mount', 'umount', 'file', 'strings', 'zcat']

class FilePathError(Exception): pass
class NotPriviledgedUser(Exception): pass
class UnsupportedPackingType(Exception): pass

def packInitramFS(dirname, rootimgpath, initscript=None):
    """Packs the directory dir into an initramfs rootimgpath. The initscript template file can be passed as well.
       Refer to Linux Kernel Documentation/filesystems/ramfs-rootfs-initramfs.txt for more information.
    """
    
    if not path(dirname).exists(): 
        raise FilePathError
    
    if os.environ['USER'] <> 'root': raise NotPriviledgedUser, "Operation requires root access!"
    
    # nuke existing rootimgpath if existing
    if path(rootimgpath).exists(): rootimgpath.remove()
    
    cwd = path(dirname)
    findP = subprocess.Popen("find .",cwd=cwd,shell=True,stdout=subprocess.PIPE)
    cpioP = subprocess.Popen("cpio -o -H newc --quiet",cwd=cwd,shell=True,stdin=findP.stdout,stdout=subprocess.PIPE)
    gzipP = subprocess.Popen("gzip > %s" % rootimgpath,shell=True,stdin=cpioP.stdout)
    gzipP.communicate()
    
    return gzipP.returncode
    
def unpack(rootimgpath, dirname):
    """Unpacks the file rootimgpath into the directory dir."""
    
    if not path(rootimgpath).exists(): raise FilePathError
    
    if os.environ['USER'] <> 'root': raise NotPriviledgedUser
    
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
            cmd = 'cd %s && cpio -I %s -id' % (tmprootdir,rootimg)
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
    
     
def makeBootISO(isolinuxdir, isoname, volname="BootKit"):
    """Create a bootable ISO isoname out of the directory isolinuxdir. The volname can be used to specify
       the ISO label name.
    """
    
    tdir = path(isolinuxdir)
    isopath = path(isoname)
    if not tdir.exists(): raise FilePathError
    
    # create a clean scratch directory for mkisofs operations
    scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
    bootdir = scratchdir / 'isolinux'
    cpio_copytree(tdir,bootdir)
    
    # nuke existing iso file if any
    if isopath.exists(): isopath.remove()
    
    options = '-c isolinux/boot.cat \
    -b isolinux/isolinux.bin \
    -V %s\
    -quiet \
    -no-emul-boot \
    -boot-load-size 4 \
    -R -r -T -f -l \
    -o %s %s' %  (volname,isopath,scratchdir)
    
    isoP = subprocess.Popen('mkisofs %s > /dev/null 2>&1' % options,shell=True)
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
    value = commands.getstatusoutput(cmdstr)
    
    return value
    
def cpio_copytree(src,dst):
    """A cpio-based copytree functionality. Only use this when shutil.copytree don't cut
       it. NOTE: This needs to move to the common util library.
    """

    # Taken from <unistd.h>, for file/dirs access modes
    # These can be OR'd together
    R_OK = 4   # Test for read permission.
    W_OK = 2   # Test for write permission.
    X_OK = 1   # Test for execute permission.

    # convert paths to be absolute
    src = path(src).abspath()
    dst = path(dst).abspath()
    cwd = path(src)

    if not cwd.exists(): raise IOError, "Source directory does not exist!"

    # create the dst directory if it doesn't exist initially
    if not path(dst).exists():
        if path(dst).parent.access(R_OK|W_OK):
            path(dst).mkdir()
        else:
            raise IOError, "No read/write permissions in parent directory!"
    else:
        if not path(dst).access(R_OK|W_OK): raise IOError, "No read/write permissions in destination directory!"


    findP = subprocess.Popen('find .',cwd=cwd,shell=True,stdout=subprocess.PIPE)
    cpioP = subprocess.Popen('cpio -mpdu --quiet %s' % dst,cwd=cwd,stdin=findP.stdout,shell=True)
    cpioP.communicate()
    return cpioP.returncode



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
        
        if not self.rootimgpath.exists(): raise FilePathError
        
        value = launchCmd('file', '-z -k', self.rootimgpath)
        li = []
        # check if any elements in the ROOTIMG_PACKING_TYPE exists
        for i in ROOTIMG_PACKING_TYPE:
            if value[1].find(i) > -1:
                li.append(i)
                
        if not li: return None
        
        return li
            
                
        
        
        
