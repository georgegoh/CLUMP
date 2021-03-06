#!/usr/bin/env python
# $Id$
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE for details.
""" This module contains several classes and functions for dealing with boot media and boot environments. """

from path import path
import subprocess
import os
from kusu.boot.distro import DistroFactory, SUPPORTED_DISTROS, USES_ANACONDA
from kusu.boot.image import *
from kusu.util.errors import *
from kusu.util.tools import cpio_copytree
import tempfile

SUPPORTED_KUSU_ENVARS = ['KUSU_BUILD_DIST', 'KUSU_INSTALL_PREFIX', 
                        'KUSU_BUILD_DISTVER', 'KUSU_BUILD_ARCH',
                        'KUSU_ROOT', 'KUSU_DEVEL_ROOT',
                        'KUSU_BUILD_ISOBIN', 'KUSU_DISTRO_SRC',
                        'KUSU_CACHE_DIR', 'KUSU_DIST',
                        'KUSU_DISTVER', 'KUSU_TMP',
                        'KUSU_LOGLEVEL', 'KUSU_LOGFILE', 'KUSU_DIST_ARCH']

def getPartitionMap(src='/proc/partitions'):
    """ This function returns a list of dicts containing the entries of /proc/partitions. """
    partition_map = {}
    lines = open(src).readlines()
    for line in lines[2:]:
        tokens = line.split()
        details = {}
        details['major'] = tokens[0]
        details['minor'] = tokens[1]
        details['blocks'] = tokens[2]
        partition_map[tokens[3]] = details
    return partition_map
    
def makeDev(devtype,major,minor,devpath):
    """ This function creates /dev/* entries. Mainly used for creating block devices. """
    
    dp = '/dev/' + devpath
    # do not create if devpath already exists
    if path(dp).exists(): return
    
    os.system('mknod %s %s %s %s' % (dp,devtype,major,minor))

def cleanupTransient(rootpath):
    """ Clean up any transient artefacts not needed in the rootpath"""

    # remove *.pyc and *.pyo
    cmd = "find %s -name '*py?' | xargs rm -f" % rootpath
    cleanupP = subprocess.Popen(cmd,shell=True)
    cleanupP.communicate()

    # remove the kusudevenv.sh script
    cmd = "find %s -name 'kusudevenv.sh' | xargs rm -f" % rootpath
    cleanupP = subprocess.Popen(cmd,shell=True)
    cleanupP.communicate()

def copyKitContents(kit,dst):
    """ Copy kit contents into dst. Raises KitCopyError except if fails. """
    
    kit = path(kit).abspath()
    dst = path(dst).abspath()
    
    if not kit.exists(): raise KitCopyError, 'Kit not found!'
    if not dst.exists(): raise KitCopyError, 'Destination directory does not exist!'
    
    # handle the kit iso
    if kit.exists():
        cmd = 'losetup -f'
        loopP = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        v = loopP.communicate()[0]
        if not v.startswith('/dev/loop'):
            raise KitCopyError, 'No available loop devices!'
            
        # create mntpnt to hold kit
        mountpt = path(tempfile.mkdtemp(dir='/tmp'))
        cmd = 'mount -o loop %s %s' % (kit,mountpt)
        mountP = subprocess.Popen(cmd,shell=True)
        mountP.communicate()
        
        # copy the contents
        cpio_copytree(mountpt,dst)
        
        cmd = 'umount %s' % mountpt
        umountP = subprocess.Popen(cmd,shell=True)
        umountP.communicate()
        
        # remove TRANS.TBL
        for f in dst.walkfiles('TRANS.TBL'):
            f.remove()
        
        if mountpt.exists(): mountpt.rmtree()

    

class KusuSVNSource:
    """ This class contains data and operations that work with the Kusu SVN source. """
    
    def __init__(self, source, env=None):
        """ source refers to the Kusu SVN trunk source. env refers to a dict containing KUSU_* environment variables
            that can be used to control the build.
        """
        self.srcpath = path(source)
        self.isRemote = False
        self.develroot = None
        self.kusuroot = None
        self.scratchdir = None
        self.env = env

        # These should describe the key directories/files that identify a Kusu SVN source layout.
        self.srcpathLayoutAttributes = {
            'bin' : 'bin',
            'build' : 'build',
            'CMakeLists' : 'CMakeLists.txt',
            'docs' : 'docs',
            'etc' : 'etc',
            'src' : 'src',
            'dists' : 'src/dists'
        }

    def verifySrcPath(self):
        """Call the correct verify*SrcPath method."""

        if self.isRemote:
            return self.verifyRemoteSrcPath()
        else:
            return self.verifyLocalSrcPath()

    def verifyLocalSrcPath(self):
        """Verify the path for attributes that describes a valid Kusu SVN source"""

        try:
            if not self.srcpath.exists(): return False
        except AttributeError:
            # we could be testing on a NoneType object instead of a Path object
            return False

        # Check the path for each attribute listed, return if invalid path
        for k,v in self.srcpathLayoutAttributes.items():
            p = self.srcpath / v
            if not p.exists(): return False

        return True
        
    def setup(self,develroot=None,kusuroot=None):
        """ General setup for Kusu develroot"""
        
        if not develroot:
            self.scratchdir = path(tempfile.mkdtemp(dir='/tmp'))
            self.develroot = path(tempfile.mkdtemp(dir=self.scratchdir))
        else:
            if path(develroot).exists():
                self.develroot = path(develroot)
            else:
                raise FilePathError, "Please ensure that the develroot %s exists!" \
                    % develroot
            
        if not kusuroot:
            self.kusuroot = self.develroot / 'kusuroot'
        else:
            if path(kusuroot).exists():
                self.kusuroot = path(kusuroot)
            else:
                raise FilePathError, "Please ensure that the kusuroot %s exists!" \
                    % kusuroot
            
                
    def runCMake(self):
        """ Run CMake within the Kusu develroot. This is a blocking call. """
        env = os.environ
        env['KUSU_ROOT'] = self.kusuroot
        cmakeP = subprocess.Popen('cmake %s > /dev/null 2>&1' % self.srcpath.abspath(),shell=True,
                    cwd=self.develroot,env=env)
        result = cmakeP.communicate()
        
        return cmakeP.returncode

        
    def runMake(self):
        """ Run make within the Kusu develroot. This is a blocking call. """

        makeP = subprocess.Popen('make > /dev/null 2>&1',shell=True,
                    cwd=self.develroot)
        result = makeP.communicate()

        return makeP.returncode
        
    def cleanup(self):
        """ Housecleaning for Kusu develroot. """
        
        # remove the scratchtree when done
        if self.kusuroot.exists(): self.kusuroot.rmtree()
        if self.develroot.exists(): self.develroot.rmtree()
        if self.scratchdir.exists(): self.scratchdir.rmtree()
        
    def run(self):
        """ Main launcher. """
        
        retcode = self.runCMake()
        if retcode <> 0:
            self.cleanup()
            raise FailedBuildCMake, "Failed CMake build for Kusu"

        retcode = self.runMake()
        if retcode <> 0:
            self.cleanup()
            raise FailedBuildMake, "Failed Make build for Kusu"
        
    def copyKusuroot(self, dest, overwrite=False):
        """Copy the kusuroot file to a destination"""

        if path(dest).parent.access(os.W_OK):
            # make sure that the existing destpath is accessible and writable
            if path(dest).exists() and overwrite:
                path(dest).rmtree()
                cpio_copytree(self.kusuroot,dest)
            elif not path(dest).exists():
                cpio_copytree(self.kusuroot,dest)
            else:
                raise FileAlreadyExists
        else:
            raise CopyError        

class BootMediaTool:
    """ The management class for boot-media-tool operations. This convenience class combines 
        the functions and methods from the kusu.boot.image and kusu.boot.distro modules. 
    """
        
    def _initSrc(self,srcpath):
        """ Initializes the installsrc instance with DistroFactory. 
        """
        self.installsrc = DistroFactory(srcpath)
        
    def validSrcPath(self, srcpath):
        """ Verify if the srcpath is valid. """
        self._initSrc(srcpath)
        return self.installsrc.verifySrcPath()
        
    def getDistro(self, srcpath):
        """ Returns the OS type. """
        self._initSrc(srcpath)
        return self.installsrc.ostype
        
    def getVersion(self, srcpath):
        """ Returns the OS type. """
        self._initSrc(srcpath)
        return self.installsrc.getVersion()
        
    def getKernelPath(self, srcpath):
        """ Query the srcpath and returns the path of the kernel. """
        self._initSrc(srcpath)
        return self.installsrc.getKernelPath()
        
    def getKernelPackages(self, srcpath):
        """ Returns the list of distro-specific kernel packages. """
        self._initSrc(srcpath)
        return self.installsrc.getKernelPackages()
        
    getKernelRpms = getKernelPackages
        
    def getIsolinuxbinPath(self, srcpath):
        """ Query the srcpath and returns the path of the isolinux.bin. """
        self._initSrc(srcpath)
        return self.installsrc.getIsolinuxbinPath()

    def getInitrdPath(self, srcpath):
        """ Query the srcpath and returns the path of the initrd. """
        self._initSrc(srcpath)
        return self.installsrc.getInitrdPath()
        
    def copyKernel(self, srcpath, dest, overwrite=False):
        """ Extract the kernel from the srcpath to the dest. A CopyError
            exception will be raised if there are errors when extraction.
        """
        try:
            self._initSrc(srcpath)
            self.installsrc.copyKernel(dest,overwrite)
            return True
        except (CopyError,FileAlreadyExists,IOError), e:
            raise e
            
    def copyInitrd(self, srcpath, dest, overwrite=False):
        """ Extract the initrd from the srcpath to the dest. A CopyError
            exception will be raised if there are errors when extraction. 
        """
        try:
            self._initSrc(srcpath)
            self.installsrc.copyInitrd(dest,overwrite)
            return True
        except (CopyError,FileAlreadyExists,IOError), e:
            raise e
            
    def packRootImg(self, dirname, rootimgpath, initscript=None):
        """ Converts the rootfs directory into a initramfs image. A
            FilePathError exception will be raised if the paths are
            invalid or unaccesible. This is also a root only operation.
        """
        try:
            packInitramFS(dirname, rootimgpath, initscript)
            return True
        except FilePathError, e:
            raise e
            
    def unpackRootImg(self, rootimgpath, dirname):
        """ Unpack a root image into a rootfs directory. A
            FilePathError exception will be raised if the paths are
            invalid or unaccesible. This is also a root only operation
            and a NotPriviledgedUser exception will be raised if non-root
            process or user is calling this method.
        """
        try:
            unpack(rootimgpath, dirname)
            return True
        except (FilePathError,NotPriviledgedUser), e:
            raise e
            
    def mkISOLinuxDir(self, isolinuxdir, kernelpath, initrdpath, ostype, isolinuxbin):
        """ Creates isolinux directory. A FilePathError exception will be 
            raised if the paths are invalid or unaccesible.
        """
        try:
            obj = OperatingEnvironment(kernelpath,initrdpath,ostype)
            makeISOLinuxDir(isolinuxdir, obj, isolinuxbin)
            return True
        except FilePathError, e:
            raise e
            
    def mkISOFromSource(self,srcpath,patchfile,kususrc,arch,kit=None):
        """ Creates Kusu Boot ISO based on installation source. If kit is available, add it into
            the iso, This method returns the isodir.
        """
        d = DistroFactory(srcpath)
        kususrc = KusuSVNSource(kususrc)
        if not kususrc.verifySrcPath(): raise InvalidKusuSource, "Invalid Kusu SVN Source!"
                
        try:
            p = 'src/dists/%s/%s/%s' % (d.ostype,d.getVersion(),arch)
            if not (kususrc.srcpath / p).exists(): raise UnsupportedDistro, "Distro-specific assets not in source tree!"
            
            if d.ostype in SUPPORTED_DISTROS and d.ostype in USES_ANACONDA:
                # create the isolinux directory
                tmpdir = path(tempfile.mkdtemp(dir='/tmp'))
                isolinuxdir = tmpdir / 'isolinux'
                isolinuxdir.mkdir()
                self.mkISOLinuxDir(isolinuxdir,d.getKernelPath(),
                    d.getInitrdPath(),d.ostype,d.getIsolinuxbinPath())
            
                # create the images directory and copy stage2/patchfile images
                imagesdir = tmpdir / 'images'
                imagesdir.mkdir()
                self.mkImagesDir(srcpath,imagesdir,patchfile)

                # put in the ks.cfg
                p = kususrc.srcpath / 'src/dists/%s/%s/%s/initrd/ks.cfg' % (d.ostype,d.getVersion(),arch)
                kscfg = path(p)
                if kscfg.exists(): 
                    kscfg.copy(tmpdir)
                
                # put in the isolinux.cfg
                p = kususrc.srcpath / 'src/dists/%s/%s/%s/initrd/isolinux.cfg' % (d.ostype,d.getVersion(),arch)
                isocfg = path(p)
                if isocfg.exists(): 
                    path(isolinuxdir / 'isolinux.cfg').remove()
                    isocfg.copy(isolinuxdir)
                    
                # put in the splash.lss
                p = kususrc.srcpath / 'src/dists/common/splash.lss'
                splashlss = path(p)
                if splashlss.exists(): 
                    splashlss.copy(isolinuxdir)
                    
                # put in the boot.msg
                p = kususrc.srcpath / 'src/dists/%s/%s/%s/boot.msg' % (d.ostype,d.getVersion(),arch)
                bootmsg = path(p)
                if bootmsg.exists(): 
                    bootmsg.copy(isolinuxdir)                    
                   
                # finally, add the .discinfo stub
                discinfo = path(tmpdir / '.discinfo')
                discinfo.touch()

                # copy the kit contents into tmpdir if kit is given
                if kit: copyKitContents(kit,tmpdir)

                return tmpdir

            else:
                raise InvalidInstallSource, "Installation source not supported!"
        except (FilePathError,InvalidInstallSource,InvalidKusuSource, UnsupportedDistro, KitCopyError), e:
            raise e
        
    def mkImagesDir(self, srcpath, destdir, patchfile=None,overwrite=False):
        """ Creates images directory based on installsrc. A FilePathError
            exception will be raised if the paths are invalid or unaccesible.
        """
        try:
            makeImagesDir(srcpath,destdir,patchfile,overwrite)
        except (FilePathError,InvalidInstallSource), e:
            raise e
            
    def mkBootISO(self, isodir, isoname, volname="BootKit"):
        """ Creates ISO based on the iso directory. A FilePathError 
            exception will be raised if the paths are invalid or unaccesible.
        """
        try:
            makeBootISO(isodir, isoname, volname="BootKit")
            return True
        except FilePathError, e:
            raise e
            
    def mkPatch(self,kususrc,osname,osver,osarch,patchfile,kusuroot=None):
        """ Creates a distro-specific Kusu Installer patchfile. """
        try:
            # prepares the env dict
            env = {}
            env['KUSU_BUILD_DIST'] = osname
            env['KUSU_BUILD_DISTVER'] = osver
            env['KUSU_BUILD_ARCH'] = osarch
            # check the current environment if any KUSU_* is set
            for k,v in os.environ.items():
                if k.startswith('KUSU_') and k in SUPPORTED_DISTROS:
                    env[k] = v
                
            svnsrc = KusuSVNSource(kususrc,env)
            
            # create a scratchdir to hold the patchfile contents
            parentdir = path(patchfile).parent
            tmpdir = path(tempfile.mkdtemp(dir=parentdir))
            destroot = tmpdir / 'opt/kusu'
            destroot.makedirs()
            
            if not svnsrc.verifySrcPath(): raise FilePathError, "Invalid Kusu SVN Source!"
            
            p = 'src/dists/%s/%s/%s' % (osname,osver,osarch)
            if not (svnsrc.srcpath / p).exists(): raise UnsupportedDistro, "Distro-specific assets not in source tree!"
            
            if svnsrc.verifySrcPath():
                if not kusuroot:
                    svnsrc.setup()
                    svnsrc.run()
                    svnsrc.copyKusuroot(destroot,overwrite=True)
                    svnsrc.cleanup()
                else:
                    # FIXME: verify kusuroot else there's going to be trouble!
                    cpio_copytree(kusuroot,destroot)
                # get the correct kusuenv.sh
                if osname in SUPPORTED_DISTROS and osname in USES_ANACONDA:
                    # put in the kusuenv.sh
                    p = svnsrc.srcpath / 'src/dists/%s/%s/%s/kusuenv.sh' % (osname,osver,osarch)
                    kusuenv = path(p)
                        
                    if kusuenv.exists(): 
                        kusuenv.copy(destroot / 'bin')
                        # make it executable
                        path(destroot / 'bin' / 'kusuenv.sh').chmod(0755)
                    
                    # remove the kusudevenv.sh
                    if path(destroot / 'bin' / 'kusudevenv.sh').exists():
                        path(destroot / 'bin' / 'kusudevenv.sh').remove()
                        
                    # put in the the faux anaconda launcher
                    p = svnsrc.srcpath / 'src/dists/%s/%s/%s/updates.img/anaconda' % (osname,osver,osarch)
                    fakeanaconda = path(p)
                    if fakeanaconda.exists(): 
                        fakeanaconda.copy(tmpdir)
                        # make it excutable
                        path(tmpdir / 'anaconda').chmod(0755)
                    
                    # clean out any unwanted stuff
                    cleanupTransient(destroot)
                    # pack the tmpdir into a patchfile with size of 10MB
                    packExt2FS(tmpdir,patchfile,size=10000)
                    
                else:
                    raise UnsupportedDistro, "Unsupported Distro!"

            path(tmpdir).rmtree()
        except (FilePathError,NotPriviledgedUser), e:
            # do some housecleaning if possible
            if svnsrc.verifySrcPath(): svnsrc.cleanup()
            if path(tmpdir).exists(): path(tmpdir).rmtree()
            raise e
        except UnsupportedDistro,e:
            if path(tmpdir).exists(): path(tmpdir).rmtree()
            raise e

    def mkNodeInstallerPatch(self,kususrc,osname,osver,osarch,patchfile,kusuroot=None):
        """ Creates a distro-specific Kusu NodeInstaller patchfile. """
        try:
            # prepares the env dict
            env = {}
            env['KUSU_BUILD_DIST'] = osname
            env['KUSU_BUILD_DISTVER'] = osver
            env['KUSU_BUILD_ARCH'] = osarch
            # check the current environment if any KUSU_* is set
            for k,v in os.environ.items():
                if k.startswith('KUSU_') and k in SUPPORTED_DISTROS:
                    env[k] = v

            svnsrc = KusuSVNSource(kususrc,env)

            # create a scratchdir to hold the nodeinstaller patchfile contents
            parentdir = path(patchfile).parent
            tmpdir = path(tempfile.mkdtemp(dir=parentdir))
            destroot = tmpdir / 'opt/kusu'
            destroot.makedirs()

            if not svnsrc.verifySrcPath(): raise FilePathError, "Invalid Kusu SVN Source!"

            p = 'src/dists/%s/%s/nodeinstaller' % (osname,osver)
            if not (svnsrc.srcpath / p).exists(): raise UnsupportedDistro, "Distro-specific assets not in source tree!"

            if svnsrc.verifySrcPath():
                if not kusuroot:
                    svnsrc.setup()
                    svnsrc.run()
                    svnsrc.copyKusuroot(destroot,overwrite=True)
                    svnsrc.cleanup()
                else:
                    # FIXME: verify kusuroot else there's going to be trouble!
                    cpio_copytree(kusuroot,destroot)
                # get the correct kusuenv.sh
                if osname in SUPPORTED_DISTROS and osname in USES_ANACONDA:
                    # put in the kusuenv.sh
                    p = svnsrc.srcpath / 'src/dists/%s/%s/%s/kusuenv.sh' % (osname,osver,osarch)
                    kusuenv = path(p)

                    if kusuenv.exists(): 
                        kusuenv.copy(destroot / 'bin')
                        # make it executable
                        path(destroot / 'bin' / 'kusuenv.sh').chmod(0755)

                    # remove the kusudevenv.sh
                    if path(destroot / 'bin' / 'kusudevenv.sh').exists():
                        path(destroot / 'bin' / 'kusudevenv.sh').remove()

                    # put in the the faux anaconda launcher
                    p = svnsrc.srcpath / 'src/dists/%s/%s/nodeinstaller/updates.img/anaconda' % (osname,osver)
                    fakeanaconda = path(p)
                    if fakeanaconda.exists(): 
                        fakeanaconda.copy(tmpdir)
                        # make it excutable
                        path(tmpdir / 'anaconda').chmod(0755)

                    # clean out any unwanted stuff
                    cleanupTransient(destroot)

                    # pack the tmpdir into a patchfile with size of 10MB
                    packExt2FS(tmpdir,patchfile,size=10000)

                else:
                    raise UnsupportedDistro, "Unsupported Distro!"

            path(tmpdir).rmtree()
        except (FilePathError,NotPriviledgedUser), e:
            # do some housecleaning if possible
            if svnsrc.verifySrcPath(): svnsrc.cleanup()
            if path(tmpdir).exists(): path(tmpdir).rmtree()
            raise e
        except UnsupportedDistro,e:
            if path(tmpdir).exists(): path(tmpdir).rmtree()
            raise e
        
    def mkBootArchive(self, isolinuxdir, archive):
        """ Creates a BootArchive based on the isolinux directory. A 
            FilePathError exception will be raised if the paths are 
            invalid or unaccesible.
        """
        try:
            makeBootArchive(isolinuxdir, archive)
            return True
        except FilePathError, e:
            raise e
