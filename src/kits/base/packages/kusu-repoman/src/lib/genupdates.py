#!/usr/bin/env python
# $Id$
#
# Copyright (C) 2007 Platform Computing Inc
#

import os
import subprocess
import sys
import tempfile
import shutil
import atexit
import string

from primitive.system.software.probe import OS
from primitive.support.util import runCommand
from primitive.core.errors import ModuleException
from kusu.genupdates.downloader import Downloader

class CmdExecutionError(Exception): pass
class MissingPackagesError(Exception): pass
class UnsupportedOSError(Exception): pass 

class GenUpdatesFactory(object):
    def __init__(self):
        pass

    def getUpdatesClass(self, target_os=OS()):
        if target_os[0].lower() in ['rhel', 'redhat', 'centos', 'fedora', 'sl']:
            return YumGenUpdates(target_os)
        elif target_os[0].lower() in ['sles', 'suse', 'opensuse']:
            return YastGenUpdates(target_os)
        else:
            raise UnsupportedOSError, 'Target os: %s-%s-%s is not supported' % target_os

class BaseGenUpdates(object):
    def __init__(self, target_os=OS()):
        self.target = (target_os[0].lower(),) + target_os[1:]
        self.rpms = []

    def runCmd(self, cmd):
        try:
            return runCommand(cmd)
        except ModuleException, msg:
            raise CmdExecutionError, msg

    def getSrcDir(self):
        dir = os.getenv('KUSU_ROOT', '/opt/kusu')
        return os.path.join(dir, 'lib/nodeinstaller')

    def cleanup(self, tdir):
        """Housekeeping routines"""
        if os.path.exists(tdir):
            shutil.rmtree(tdir)

    def downloadRPMS(self, rpms, dldir):
        """ Download the list of packages required to create Kusu Runtime.
            The packages will be downloaded into dldir directory.
        """
        dldir = os.path.abspath(dldir)

        do = Downloader(dldir, target_os=self.target)
        return do.downloadPackages(rpms)

    def visitor_binary_rpms(self, (pkgs, rpms), dirname, names):
        """Returns the binary RPM"""
        li = []
        if '.svn' in names:
            names.remove('.svn')
        for pkg in pkgs:
            li.extend([name for name in names if name.startswith(pkg) and name.endswith('.rpm')])

        if li:
            for l in li:
                rpms.append(os.path.abspath(os.path.join(dirname,l)))

    def getAndVerifyRPMS(self, getrpms, destdir):
        downloaded = self.downloadRPMS(getrpms[:], destdir)

        rpms = []
        # get the RPMS directory
        os.path.walk(destdir, self.visitor_binary_rpms, (getrpms, rpms))

        # take out kusu-nodeinstaller-patchfiles
        nipkg = [p for p in rpms if os.path.basename(p).startswith('kusu-nodeinstaller-patchfiles')]
        
        for p in nipkg:
            rpms.remove(p)
       
        missing = [pkg for pkg in getrpms if pkg not in downloaded] 
        return rpms, missing

    def unpackRPMS(self, rpm_paths, destdir):
        err = open('/dev/null','w')
        for rpm in rpm_paths:
            rpm2cpioP = subprocess.Popen('rpm2cpio %s' % rpm, shell=True, cwd=destdir,
                                         stdout=subprocess.PIPE, stderr=err)
            cpioP = subprocess.Popen('cpio -id', shell=True, cwd=destdir, stdin=rpm2cpioP.stdout,
                                     stdout=subprocess.PIPE, stderr=err)
            cpioP.wait()
        err.close()

    def generateUpdatesImg(self, updatesdir, updatesimgdir):
        pass

    def doGenUpdates(self, nidir):
        # create a scratchdir to hold the downloaded RPMS.
        rpmsdir = tempfile.mkdtemp(prefix='rpmsdir-')
        atexit.register(self.cleanup, rpmsdir)
        rpmlist, missing = self.getAndVerifyRPMS(self.rpms, rpmsdir)

        if missing:
            msg = 'Packages missing from repositories:\n\t%s' % '\n\t'.join(missing)
            raise MissingPackagesError, msg

        # create a temp holding directory and unpack RPMS there.
        unpacked_dir = tempfile.mkdtemp(prefix='unpackdir-')
        atexit.register(self.cleanup, unpacked_dir)
        self.unpackRPMS(rpmlist, unpacked_dir)

        # create patchfiles subdirectories for SLES.
        updates_dir = tempfile.mkdtemp(prefix='updatesdir-')
        atexit.register(self.cleanup, updates_dir)
        niPatchfilesDir = updates_dir
        OSNameVerArchPatchfilesDir = os.path.join(niPatchfilesDir, 
                                                  'nodeinstaller/%s/%s/%s' % self.target)
        os.makedirs(OSNameVerArchPatchfilesDir)

        # generate the updates.img and place in the os directories.
        self.generateUpdatesImg(unpacked_dir, OSNameVerArchPatchfilesDir)

        # remove existing nidir if any
        if os.path.exists(nidir):
            shutil.rmtree(nidir)
        os.mkdir(nidir)

        # copy from the temporary updates directory to specified directory
        err = open('/dev/null','w')
        cmd = 'find . | cpio -mpdu %s' % nidir
        cpioP = subprocess.Popen(cmd,shell=True,cwd=updates_dir,stdout=subprocess.PIPE,stderr=err)
        cpioP.wait()
        err.close()

class YastGenUpdates(BaseGenUpdates):
    def __init__(self, target_os=OS()):
        BaseGenUpdates.__init__(self, target_os)
        self.rpms = [
                     'coreutils',
                     'grub',
                     'kusu-autoinstall',
                     'kusu-boot',
                     'kusu-core',
                     'kusu-hardware',
                     'kusu-installer',
                     'kusu-networktool',
                     'kusu-nodeinstaller',
                     'kusu-path',
                     'kusu-ui',
                     'kusu-util',
                     'libnewt0_52',
                     'libreiserfs',
                     'newt',
                     'parted',
                     'pyparted',
                     'python',
                     'python-bcrypt',
                     'python-cheetah',
                     'python-elementtree',
                     'python-IPy',
                     'python-newt',
                     'python-sqlalchemy',
                     'python-xml',
                     'primitive',
                     'rpm',
                     'rpm-python',
                     'slang',
                    ]

    def __getYastScript(self, distro, version):
        """Returns the 'faux' yast script"""
        trunk = self.getSrcDir()
        distspath = 'src/dists/%s/%s/nodeinstaller' % (distro, version)
        yastScript = os.path.abspath(os.path.join(trunk, os.path.join(distspath, 'updates.img/yast')))
        return yastScript

    def generateUpdatesImg(self, unpacked_dir, outputdir):
        # Create a 'sbin' directory where the RPMS are unpacked and copy the fake yast there.
        unpacked_dir_sbin = os.path.join(unpacked_dir, 'sbin')
        if not os.path.exists(unpacked_dir_sbin):
            os.mkdir(unpacked_dir_sbin)
        yastScript = self.__getYastScript(self.target[0], self.target[1])
        shutil.copy(yastScript, unpacked_dir_sbin)
        os.chmod(os.path.join(unpacked_dir_sbin, 'yast'), 0755)

        # Remove the parted and partprobe binaries or autoyast will fail at its partitioning stage.
        os.unlink(os.path.join(unpacked_dir, 'usr', 'sbin', 'parted'))
        os.unlink(os.path.join(unpacked_dir, 'usr', 'sbin', 'partprobe'))

        # generate the updates.img
        self.runCmd('/sbin/mkfs.cramfs %s %s' % (unpacked_dir, os.path.join(outputdir, 'updates.img')))

class YumGenUpdates(BaseGenUpdates):
    def __init__(self, target_os=OS()):
        BaseGenUpdates.__init__(self, target_os)
        self.rpms = ['kusu-autoinstall',
                     'kusu-boot',
                     'kusu-buildkit',
                     'python-cheetah',
                     'kusu-core',
                     'kusu-createrepo',
                     'kusu-driverpatch',
                     'kusu-hardware',
                     'kusu-installer',
                     'python-IPy',
                     'kusu-kitops',
                     'kusu-md5crypt',
                     'kusu-networktool',
                     'kusu-nodeinstaller',
                     'kusu-path',
                     'python-sqlite2',
                     'kusu-repoman',
                     'python-sqlalchemy',
                     'kusu-ui',
                     'kusu-util',
                     'python-bcrypt',
                     'primitive']

    def __getAnacondaScript(self, (distro, version)):
        """Returns the 'faux' anaconda script"""
        trunk = self.getSrcDir()
        distspath = 'src/dists/%s/%s/nodeinstaller' % (distro, version)
        anacondaScript = os.path.abspath(os.path.join(trunk, os.path.join(distspath, 'updates.img/anaconda')))
        return anacondaScript

    def __getKSTemplate(self, (distro, version)):
        """Returns the ks.cfg.tmpl"""
        trunk = self.getSrcDir()
        distspath = 'src/dists/%s/%s/nodeinstaller' % (distro, version)
        kscfgtmpl = os.path.abspath(os.path.join(trunk, os.path.join(distspath, 'ks.cfg.tmpl')))
        return kscfgtmpl
        
    def __getYumScalabilityPatch(self, (distro,version)):
        """Returns the yuminstall.py.patch"""
        trunk = self.getSrcDir()
        distspath = 'src/dists/%s/%s/nodeinstaller' % (distro, version)
        patchPath = os.path.join(trunk, os.path.join(distspath, 'updates.img/yuminstall.py.patch'))
        return os.path.abspath(patchPath)
    
    def __checkFreeLoopDev(self):
        """Check for any available loopback devices"""
        loopdev  = self.runCmd('losetup -a')[0]
        used_list = [line.split(':', 1)[0] for line in loopdev.splitlines()]
        devs_list = self.runCmd('ls /dev/loop*')[0].splitlines()
        unused_set = set(devs_list) - set(used_list)
        if len(unused_set) > 0:
            return True
        return False

    def __packExt2FS(self, dirname, rootimgpath, size=5000):
        """Packs the directory dir into an ext2fs rootimgpath. The size of the image can be passed as well.
        """

        if not os.path.exists(dirname):
            raise OSError

        # nuke existing rootimgpath if existing
        if os.path.exists(rootimgpath):
            os.remove(rootimgpath)
        rootimgpath = os.path.abspath(rootimgpath)

        # create scratchdir
        scratchdir = tempfile.mkdtemp(prefix='ext2fs-')
        atexit.register(self.cleanup, scratchdir)
        tmprootdir = tempfile.mkdtemp(dir=scratchdir)

        # create a block device, format it, mount it
        cwd = os.getcwd()
        os.chdir(scratchdir)
        self.runCmd('dd of=%s if=/dev/zero bs=1024 count=%s' % (rootimgpath, size))
        self.runCmd('mke2fs -F %s' % rootimgpath)

        if not self.__checkFreeLoopDev():
            # create a loopback device
            self.runCmd('mknod /dev/loop0 b 7 0')
            self.runCmd('mount -o loop=/dev/loop0 %s %s' % (rootimgpath, tmprootdir))
        else:
            self.runCmd('mount -o loop %s %s' % (rootimgpath, tmprootdir))

        # copy the contents over to the newly made ext2fs filesystem
        os.chdir(dirname)
        self.runCmd('find . | cpio -mpdu %s' % tmprootdir)
        
        # housecleaning
        os.chdir(scratchdir)
        self.runCmd('umount %s' % tmprootdir)
        os.chdir(cwd)

    def generateUpdatesImg(self, unpacked_dir, outputdir, size=0):
        dist_ver = (self.target[0], self.target[1])
        anacondaScript = self.__getAnacondaScript(dist_ver)
        kscfgTemplate = self.__getKSTemplate(dist_ver)

        shutil.copy(kscfgTemplate, outputdir)

        # fix the missing __init__.py
        initpy = os.path.join(unpacked_dir, 'opt/kusu/lib/python/kusu/__init__.py')
        f = open(initpy,'w')
        f.close()
            
        # copy the 'faux' anaconda script
        shutil.copy(anacondaScript, unpacked_dir)
        os.chmod(os.path.join(unpacked_dir, 'anaconda'), 0755)

        # Bring in Scalability patch
        if dist_ver == ('rhel', '5'):
            # Rhel 5 specific patch for now.
            yumScalabilityPatch =  self.__getYumScalabilityPatch(dist_ver)
            shutil.copy(yumScalabilityPatch, unpacked_dir)

        self.__packExt2FS(unpacked_dir, os.path.join(outputdir, 'updates.img'), 20000)

