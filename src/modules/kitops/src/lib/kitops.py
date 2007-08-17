#!/usr/bin/env python
# $Id$
#
# Kusu kitops - kit operations tool
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import sys
import os
import urllib
import urlparse
import tempfile
import glob
import re
from path import path

from kusu.boot.tool import BootMediaTool
from kusu.boot.distro import *
from kusu.kitops.package import PackageFactory
from kusu.util.tools import cpio_copytree
from kusu.util import rpmtool
from kusu.buildkit import processKitInfo
from kusu.util.errors import *
# TODO: uncomment this to call repoman's refresh
#from kusu.repoman.repofactory import RepoFactory

try:
    import subprocess
except:
    from popen5 import subprocess

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

class KitOps:
    def __init__(self, **kw):
        self.installer = kw.get('installer', False) # installer environment?
        self.kitmedia = ''
        self.dlkitiso = None
        self.mountpoint = None
        self.medialoc = None
        self.__db = kw.get('db', None)

        self.prefix = path(kw.get('prefix', '/'))
        self.tmpprefix = path(kw.get('tmpprefix', '/tmp'))
        self.kits_dir = self.prefix / 'depot/kits/'
        self.pxeboot_dir = self.prefix / 'tftpboot/kusu/'

    def setKitMedia(self, kitmedia):
        self.kitmedia = kitmedia

    def setDB(self, db):
        self.__db = db

    def setPrefix(self, prefix):
        """
        Provide a new prefix.
        """

        if prefix:
            self.prefix = path(prefix)
            self.kits_dir = self.prefix / 'depot/kits/'
            self.pxeboot_dir = self.prefix / 'tftpboot/kusu/'

    def setTmpPrefix(self, tmpprefix):
        """
        Provide a new tmpprefix.
        """

        if tmpprefix:
            self.tmpprefix = path(tmpprefix)

    def getOSDist(self):
        kl.debug("OSDIST mountpoint: %s", self.mountpoint)
        return DistroFactory(str(self.mountpoint))

    def addKitPrepare(self):
        '''PreCondition:  add operation requested
           PostCondition: the kit media is mounted to self.mountpoint'''

        # determine what to do with kit media
        rv = urlparse.urlparse(self.kitmedia)

        if rv[0]:
            kl.debug('Network kit specified, retrieving')
            (self.dlkitiso, headers) = urllib.urlretrieve(self.kitmedia)
            self.dlkitiso = path(self.dlkitiso)
            self.medialoc = self.dlkitiso
        else:
            self.medialoc = path(self.kitmedia)

        #at this point, media can be either an iso file or a mountpoint dir
        if self.medialoc.isfile() and self.medialoc.ext.lower() == '.iso':
            kl.debug('Media ISO file provided: %s', self.medialoc)
            self.mountMedia(self.medialoc, True)
        elif self.medialoc.isdir():
            kl.debug('Media mountpoint: %s', self.medialoc)
            self.mountpoint = self.medialoc
        else:
            try:
                kl.debug('Trying provided CDROM: %s', self.medialoc)
                self.mountMedia(self.medialoc)
            except CannotMountKitMediaError:
                #if neither of the above - error
                raise UnrecognizedKitMediaError, \
                                    'Improper kit media location specification'

        #at this point we have the kit mounted to self.mountpoint
        try:
            assert(self.mountpoint and self.mountpoint.isdir())
        except AssertionError, msg:
            self.unmountMedia()
            raise AssertionError, \
                    'Mountpoint sanity assertion failed\n%s' % msg

        oskit = self.getOSDist()
        if oskit.ostype is not None:
            return oskit

        return self.getAvailableKits()

    def addKit(self, kitinfo):
        '''perform the add operation on the kit specified 
           Precondition: kit is mounted to self.mountpoint'''

        kitpath = path(kitinfo[0])
        kit = kitinfo[1]
        kitrpm = '%s-%s-%s.%s.rpm' % (kit['pkgname'], kit['version'],
                                      kit['release'], kit['arch'])
        
        #check if this kit is already installed - by name and version
        if self.checkKitInstalled(kit['name'], kit['version'], kit['arch']):
            self.unmountMedia()
            raise KitAlreadyInstalledError, \
                    "Kit '%s-%s-%s' already installed" % \
                    (kit['name'], kit['version'], kit['arch'])

        # 1. copy the RPMS
        repodir = self.kits_dir / kit['name'] / kit['version'] / kit['arch']
        if not repodir.exists():
            repodir.makedirs()

        srcP = subprocess.Popen('tar cf - *.rpm', cwd=kitpath,
                                shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        dstP = subprocess.Popen('tar xf -',
                                cwd=repodir, shell=True, stdin=srcP.stdout,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dstP.communicate()
        
        # also copy the kitinfo file
        kifile = kitpath / 'kitinfo'
        if kifile.exists(): kifile.copy(repodir)

        # 2. populate the kit DB table with info
        newkit = self.__db.Kits(rname=kit['name'], rdesc=kit['description'],
                                version=kit['version'], arch=kit['arch'],
                                removable=kit['removable'])
        newkit.save()
        
        # Add kit to packages table for installer nodegroup
        installngs = self.__db.NodeGroups.select_by(type='installer')
        for installng in installngs:
            installng.packages.append(
                                self.__db.Packages(packagename=kit['pkgname']))

        # 3. install the kit RPM
        if not self.installer:
            try:
                rpmP = subprocess.Popen('rpm --quiet -i %s' %
                                        (kitpath / kitrpm),
                                        shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                o, e = rpmP.communicate()
            except Exception, e:
                self.unmountMedia()
                raise InstallKitRPMError, \
                        'Kit RPM installation failed\n%s' % e

        # RPM install successful, add kit to DB
        self.__db.flush()
        kl.debug('Addkit kid: %s', newkit.kid)

        # 4. check/populate component table
        try:
            updated_ngtypes = self.updateComponents(newkit.kid, kitinfo[2])
        except ComponentAlreadyInstalledError, msg:
            # updateComponents encountered an error, remove kit from DB
            newkit.removable = True
            newkit.flush()
            self.deleteKit()
            raise ComponentAlreadyInstalledError, msg
            
        # TODO: handle driverpacks entry here, get BMT to return driver/module RPM

        # TODO: uncomment this to call repoman's refresh
        #if updated_ngtypes:
        #    rfactory = RepoFactory(self.__db, self.prefix)
        #    rfactory.refresh(ngtype=updated_ngtypes)

    def updateComponents(self, kid, components):
        """
        Update components table with information from kit.
        """

        compnames = []
        for comp in components:
            compnames.append(comp['name'])

        oldcomponents = self.__db.Components.select(
                self.__db.Components.c.cname.in_(*compnames))

        updated_ngtypes = []
        for comp in components:
            newcomponent = True
            for oldcomp in oldcomponents:
                if comp['name'] == oldcomp.cname \
                    and comp['ostype'] == oldcomp.os:
                    newcomponent = False

            if newcomponent:
                # This component does not yet exist in the DB, so add it now.
                # NOTE: storing pkgname as component name, since that's the
                # RPM package to be installed.
                newcomp = self.__db.Components(kid=kid, cname=comp['pkgname'],
                                               cdesc=comp['description'],
                                               os=comp['ostype'])
                # also store the OS/ARCH -- but how to determine?
                newcomp.save()

                ngs = self.__db.NodeGroups.select(
                    self.__db.NodeGroups.c.type.in_(*comp['ngtypes']))

                for ng in ngs:
                    ng.components.append(newcomp)

                # keep track of updated nodegroup types
                for type in comp['ngtypes']:
                    if type not in updated_ngtypes:
                        updated_ngtypes.append(type)
            else:
                raise ComponentAlreadyInstalledError, \
                    'Component %s already installed' % comp['name']

        self.__db.flush()
        return updated_ngtypes

    def getAvailableKits(self):
        """
        Scan subdirectories for possible kits for installation.
        """

        availableKits = []
        for kitinfo in self.mountpoint.walkfiles('kitinfo'):
            location = kitinfo.abspath().dirname()
            kit, components = processKitInfo(kitinfo)
            availableKits.append((location, kit, components))

        if not availableKits:
            self.unmountMedia()

        return availableKits

    def checkKitInstalled(self, kitname, kitver, kitarch):
        """
        Returns True if specified kit is already in the DB, False otherwise.
        """

        return [] != self.__db.Kits.select_by(rname=kitname, version=kitver,
                                              arch=kitarch)

    def mountMedia(self, media, isISO=False):
        """
        Mount the specified media to a temporary directory.
        """

        tmpmntdir = path(tempfile.mkdtemp(prefix='kitops',
                                          dir=self.tmpprefix))

        cmd = 'mount %s %s' % (media, tmpmntdir)
        if isISO:
            cmd = 'mount -o loop %s %s' % (media, tmpmntdir)

        mountP = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        out, err = mountP.communicate()

        if mountP.returncode != 0:
            kl.debug('Mount stdout: %s', out)
            kl.debug('Mount stderr: %s', err)
            tmpmntdir.rmdir()
            errors = self.__handleMountError(mountP.returncode)
            raise CannotMountKitMediaError, ''.join(errors)

        self.mountpoint = tmpmntdir

    def unmountMedia(self):
        """
        self.mountpoint is unmounted, removed and set to None.
        """

        if self.mountpoint and self.mountpoint.ismount():
            #umountP = subprocess.Popen('umount -l %s' %
            umountP = subprocess.Popen('umount %s' % self.mountpoint,
                                       shell=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            umountP.communicate()

            if umountP.returncode == 0:
                self.mountpoint.rmdir()
            else:
                kl.error('Unable to umount %s' % self.mountpoint)

            self.mountpoint = None

        if self.dlkitiso and self.dlkitiso.exists():
            self.dlkitiso.remove()
            self.dlkitiso = None

    def __handleMountError(self,rv):
        '''handle the mount exit status when it's non-zero. Return nothing'''
        status = os.WEXITSTATUS(rv)

        errdict = { 1: 'incorrect invocation or permissions', 
                    2: 'system error (out of memory, cannot fork, no more loop devices)', 
                    4: 'internal mount bug or missing nfs support in mount',
                    8: 'user interrupt',
                   16: 'problems writing or locking /etc/mtab',
                   32: 'generic mount failure',
                   64: 'some mount succeeded'
                  }

        errors = []
        for key in errdict.keys():
            if status & key:
                kl.error('Mount fail error: %s', errdict[key])
                errors.append(errdict[key] + '\n')

        return errors

    def prepareOSKit(self, osdistro):
        kit = {} #a struct to hold the kit info for the distro
        kit['ver'] = osdistro.getVersion()          #os kit version in the db
        kit['arch'] = osdistro.getArch()            #os kit arch in the db
        kit['name'] = osdistro.ostype.lower()
        kit['longname'] = '%s-%s-%s' % (kit['name'], kit['ver'], kit['arch'])
        kit['sum'] = 'OS kit for %s %s %s' % \
                        (kit['name'], kit['ver'], kit['arch'])
        kit['initrd'] = 'initrd-%s.img' % kit['longname']
        kit['kernel'] = 'kernel-%s' % kit['longname']

        kits = self.__db.Kits.select_by(rname=kit['name'], version=kit['ver'],
                                        arch=kit['arch'])

        if kits:
            self.unmountMedia()
            raise KitAlreadyInstalledError, \
                    "OS kit '%s' already installed" % kit['longname']

        #copy kernel & initrd to pxedir
        if not self.pxeboot_dir.exists():
            self.pxeboot_dir.makedirs()

        bmt = BootMediaTool()

        if self.installer:
            bmt.copyInitrd(self.mountpoint, self.pxeboot_dir / kit['initrd'])
        else:
            fd, tmprd1 = tempfile.mkstemp(prefix='kitops', dir=self.tmpprefix)
            os.close(fd)
            tmprd1 = path(tmprd1)

            if tmprd1.exists():
                tmprd1.remove()

            tmprootfs = path(tempfile.mkdtemp(prefix='kitops',
                                              dir=self.tmpprefix))

            bmt.copyInitrd(self.mountpoint, tmprd1, True)
            bmt.unpackRootImg(tmprd1, tmprootfs)
            tmprd1.remove()
            #patch tmprootfs with necessary pieces HERE
            #pack up the patched rootfs & put it under tftpboot
            bmt.packRootImg(tmprootfs, self.pxeboot_dir / kit['initrd'])
            tmprootfs.rmtree()

        #copy kernel to tftpboot & rename
        bmt.copyKernel(self.mountpoint, self.pxeboot_dir / kit['kernel'], True)

        return kit

    def copyOSKitMedia(self, kit):
        #copy the RPMS to repo dir
        kl.info('Copying RPMs, this may take a while...')
        repodir = self.kits_dir / kit['name'] / kit['ver'] / kit['arch']

        if not repodir.exists():
            repodir.makedirs()

        try:
            rv = cpio_copytree(self.mountpoint, repodir)
            kl.debug('cpio_copytree return code: %d', rv)
        except Exception, msg:
            self.unmountMedia()
            raise CopyOSMediaError, \
                  'Error during copy\n%s\nmountpoint:%s, repodir:%s' % \
                  (msg, self.mountpoint, repodir)

        # copy successful, don't need mounted media anymore
        self.unmountMedia()
 
    def finalizeOSKit(self, kit):
        #populate the database with info
        newkit = self.__db.Kits(rname=kit['name'], rdesc=kit['sum'],
                                version=kit['ver'], isOS=True,
                                removable=False, arch=kit['arch'])
        newkit.save()
        self.__db.flush()
        
        # get the kernel packages
        oskitdir = self.kits_dir / kit['name'] / kit['ver'] / kit['arch']
        bmt = BootMediaTool()
        _kpkgs = bmt.getKernelPackages(oskitdir)
        kpkgs = []
        if _kpkgs:
            # change the kernel packages paths into rpmtool objects
            kpkgs = [rpmtool.RPM(str(k)) for k in _kpkgs]

        # add mock component to complete link from nodegroups to kits
        comp = self.__db.Components(cname=kit['longname'],
                                    cdesc='%s mock component' % kit['longname'])
        
        # setup driverpacks entry and associate it with the mock component
        for kpkg in kpkgs:
            dpack = self.__db.DriverPacks()
            dpack.dpname = kpkg.getFilename().basename() 
            desc = ' %s for %s' % (kpkg.summary,kpkg.arch)
            dpack.dpdesc = desc        
            comp.driverpacks.append(dpack)

        newkit.components.append(comp)

        if self.installer:
            ngs = self.__db.NodeGroups.select(
                    self.__db.NodeGroups.c.type.in_('compute', 'installer'))

        for ng in ngs:
            if comp not in ng.components:
                ng.components.append(comp)

        self.__db.flush()

    def deleteKit(self, del_name, del_version='', del_arch=''):
        '''perform the delete operation on the kit specified '''

        try:
            assert(bool(del_name))
        except AssertionError,msg:
            raise AssertionError, 'Name for kit to delete not specified'

        kits = self.findKits(del_name, del_version, del_arch)

        del_path = ''
        if del_arch and del_version:
            kl.info("Removing kit '%s', version %s, arch %s" %
                    (del_name, del_version, del_arch))
            del_path = self.kits_dir / del_name / del_version / del_arch
            del_version = '-' + del_version
            del_arch = '-' + del_arch
        elif del_version:
            kl.info("Removing kit '%s', version %s, all architectures" %
                    (del_name, del_version))
            del_path = self.kits_dir / del_name / del_version
            del_version = '-' + del_version
        else:
            kl.info("Removing kit '%s', all versions and architectures" %
                    del_name)
            del_path = self.kits_dir / del_name

        if not kits:
            raise KitNotInstalledError, \
                    "Kit '%s%s%s' is not in the database" % \
                    (del_name, del_version, del_arch)

        error_kits = []
        for kit in kits:
            if not self.installer and not kit.removable:
                error_kits.append("Kit '%s-%s-%s' is not removable" % 
                                   (kit.rname, kit.version, kit.arch))
                continue

            repos = self.__db.Repos.select_by(kid=kit.kid)
            if repos:
                error_kits.append("Cannot delete kit " +
                                  "'%s-%s-%s', it is used by a repo" %
                                  (kit.rname, kit.version, kit.arch))
                continue
                
            # remove the RPMS kit contents
            del_path.rmtree()

            # uninstall kit RPM
            if not kit.isOS and not self.installer:
                rmP = subprocess.Popen('/bin/rpm --quiet -e --nodeps kit-%s' %
                                       kit.rname, shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
                rmP.communicate()

            # remove component info from DB
            for component in kit.components:
                component.delete()

            if kit.isOS:
                # remove tftpboot contents
                path(self.pxeboot_dir / 'initrd-%s.img' % kit.longname).remove()
                path(self.pxeboot_dir / 'kernel-%s' % kit.longname).remove()
                if not self.pxeboot_dir.listdir():  # directory is empty
                    self.pxeboot_dir.rmdir()

            # remove packages
            pkgs = self.__db.Packages.select_by(packagename='kit-%s' %
                                                kit.rname)
            for pkg in pkgs:
                pkg.delete()

            # remove kit DB info
            kit.delete()
        
        self.__db.flush()

        if error_kits:
            raise DeleteKitsError, error_kits

    def listKit(self, kitname=None, kitver=None, kitarch=None):
        if kitname or kitver or kitarch:
            return self.findKits(kitname, kitver, kitarch)
        else:
            return self.__db.Kits.select()

    def getNodeGroups(self, kitname, kitver=None, kitarch=None):
        import kusu.core.database as db
        return db.findNodeGroupsFromKit(self.__db, kitargs={'rname': kitname,
                                                            'version': kitver,
                                                            'arch': kitarch})

    def findKits(self, name, version, arch):
        kits = []
        if arch and version:
            kits = self.__db.Kits.select_by(rname=name,
                                            version=version, arch=arch)
        elif version:
            kits = self.__db.Kits.select_by(rname=name, version=version)
        else:
            kits = self.__db.Kits.select_by(rname=name)
 
        return kits
