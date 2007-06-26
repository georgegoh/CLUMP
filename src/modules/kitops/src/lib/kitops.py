#!/usr/bin/env python
# $Id$
#
# Kusu kitops - kit operations tool
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
# Author: atumanov

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
from kusu.util.errors import *

try:
    import subprocess
except:
    from popen5 import subprocess

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

class KitOps:
    def __init__(self, **kw):
        self.installer = kw.get('installer', False)
        self.kitname = ''
        self.kitmedia = ''
        self.dlkitiso = None
        self.mountpoint = None
        self.medialoc = None
        self.__db = kw.get('db', None)

        self.prefix = path(kw.get('prefix', '/'))
        self.tmpprefix = path(kw.get('tmpprefix', '/tmp'))
        self.kits_dir = self.prefix / 'depot/kits/'
        self.pxeboot_dir = self.prefix / 'tftpboot/kusu/'

    def setKitName(self, kitname):
        self.kitname = kitname

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
        elif self.medialoc.isdir() and self.medialoc.ismount():
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
            assert(self.mountpoint
                   and self.mountpoint.isdir() and self.mountpoint.ismount())
        except AssertionError, msg:
            self.unmountMedia()
            raise AssertionError, \
                    'Mountpoint sanity assertion failed\n%s' % msg

    def addKit(self):
        '''perform the add operation on the kit specified 
           Precondition: kit is mounted to self.mountpoint'''

        if self.kitname == '':  #kit to install was NOT specified
            self.kitname = self.determineKitName()

        # at this point self.kitname must be defined
        try:
            assert(bool(self.kitname))
        except AssertionError, msg:
            self.unmountMedia()
            raise AssertionError, \
                    "Kitname still not defined, terminating\n%s" % msg

        kitRPMlst = path(self.mountpoint / self.kitname).glob('kit-%s*.rpm' %
                                                              self.kitname)
        try:
            assert(len(kitRPMlst)==1)
        except AssertionError, e:
            msg = 'Number of kit RPMs under %s must be exactly one\n%s' % \
                    (self.mountpoint / self.kitname, e)
            self.unmountMedia()
            raise AssertionError, msg
                    

        kit = self.parseRPMTag(kitRPMlst[0].abspath())

        #check if this kit is already installed - by name and version
        if self.checkKitInstalled(kit['name'], kit['ver'], kit['arch']):
            self.unmountMedia()
            raise KitAlreadyInstalledError, \
                    "Kit '%s-%s-%s' already installed" % \
                    (kit['name'], kit['ver'], kit['arch'])

        # 1. copy the RPMS
        repodir = self.kits_dir / kit['name'] / kit['ver'] / kit['arch']
        if not repodir.exists():
            repodir.makedirs()

        srcP = subprocess.Popen('tar cf - *.rpm',
                                cwd=self.mountpoint / self.kitname,
                                shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        dstP = subprocess.Popen('tar xf -',
                                cwd=repodir, shell=True, stdin=srcP.stdout,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dstP.communicate()

        # 2. populate the kit DB table with info
        newkit = self.__db.Kits(rname=kit['name'], rdesc=kit['sum'],
                                version=kit['ver'], arch=kit['arch'])
        newkit.save()
        
        # Add kit to packages table for master and installer nodegroups
        kitpkg = self.__db.Packages(packagename=kit['inst'].getName())
        masterng = self.__db.NodeGroups.selectfirst_by(ngname='master')
        masterng.packages.append(kitpkg)
        kitpkg = self.__db.Packages(packagename=kit['inst'].getName())
        installng = self.__db.NodeGroups.selectfirst_by(ngname='installer')
        installng.packages.append(kitpkg)

        # 3. install the kit RPM
        if not self.installer:
            try:
                rpmP = subprocess.Popen('rpm --quiet -i %s' % kit['rpmloc'],
                                        shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                rpmP.communicate()
            except Exception, e:
                self.unmountMedia()
                raise InstallKitRPMError, \
                        'Kit RPM installation failed\n%s' % e

        # RPM install successful, add kit to DB
        self.__db.flush()

        #extract the kit id to associate with components
        kit['kid'] = newkit.kid
        kl.debug('Addkit kid: %s', kit['kid'])

        # 4. check/populate component table
        try:
            self.updateComponents(newkit)
        except CorruptComponentNameError, msg:
            # updateComponents encountered an error, remove kit from DB
            newkit.removable = True
            newkit.flush()
            self.deleteKit()
            self.unmountMedia()
            raise CorruptComponentNameError, msg

    def updateComponents(self, kit):
        """
        Update components table with information from kit.
        """

        complst = path(self.mountpoint / kit.rname).glob('component-*.rpm')
        for comploc in complst:
            comp = {}
            comp['inst'] = PackageFactory(str(comploc))
            comp['name'] = comp['inst'].getName()

            try:
                assert(bool(comp['name']))
            except:
                self.unmountMedia()
                raise CorruptComponentNameError, \
                        'Encountered corrupt name for component from %s' % \
                        comploc.basename()

            comp['ver'] = comp['inst'].getVersion()
            comp['sum'] = comp['inst'].getSummary()

            components = self.__db.Components.select_by(cname=comp['name'])

            if not components:
                # this component was not inserted in kit RPM's %post
                # generate an entry for this component
                newcomp = self.__db.Components(kid=kit.kid, cname=comp['name'],
                                               cdesc=comp['sum'])
                # also store the OS/ARCH -- but how to determine?
                newcomp.save()

                ngs = self.__db.NodeGroups.select()

                for ng in ngs:
                    # if installing master node, add to that nodegroup
                    if self.installer and ng.ngname == 'master' \
                        and 0 <= newcomp.cname.find('installer'):
                        ng.components.append(newcomp)

                    # if installer component, add to installer nodegroup
                    if ng.ngname == 'installer' \
                        and 0 <= newcomp.cname.find('installer'):
                        ng.components.append(newcomp)
                        continue
                    # else if compute node component, add to compute nodegroup
                    elif ng.ngname == 'compute' \
                        and 0 <= newcomp.cname.find('node'):
                        ng.components.append(newcomp)
                        continue
                    # else if neither node nor installer component, add to all
                    elif 0 > newcomp.cname.find('node') \
                        and 0 > newcomp.cname.find('installer'):
                        ng.components.append(newcomp)
            else:
                for component in components:
                    if component.cid > 0 and component.kid != kit.kid:
                        kl.warning("Updating kit id for component '%s', cid=%s",
                                   comp['name'], component.cid)
                        component.kid = kit.kid

        # no longer need mounted media
        self.unmountMedia()

        self.__db.flush()

    def parseRPMTag(self, rpmloc):
        """
        Obtains some information from RPM tag and returns in a dictionary.
        """

        kit = {} #the struct for kit info
        kit['rpmloc'] = rpmloc   #absolute path to kit RPM

        #extract some RPMTAG info
        kit['inst'] = PackageFactory(str(kit['rpmloc']))
        kit['ver'] = kit['inst'].getVersion()
        kit['name'] = kit['inst'].getName()
        kit['arch'] = kit['inst'].getArch()

        if kit['name'].startswith('kit-'):
            kit['name'] = kit['name'][len('kit-'):]
        kit['sum'] = kit['inst'].getSummary()

        return kit

    def determineKitName(self):
        """
        Scan subdirectories for possible kits for installation.
        """

        #create list of candidate kits to install
        dirlst = []
        for dir in self.mountpoint.dirs():
            if dir.glob('kit-*.rpm'):
                dirlst.append(dir)

        if not dirlst:
            self.unmountMedia()
            raise NoKitsFoundError, 'Bad media provided, no kits found'

        if len(dirlst) == 1:
            return dirlst[0].basename()
        elif len(dirlst) > 1:
            # TODO: Implement metakit handling.
            #handleMetaKit - return the kit to work with (self.kitname must be set)
            try:
                self.kitname = self.selectKit(self.mountpoint, dirlst)
            except: # raise exceptions in self.selectKit and catch them here
                self.unmountMedia()
                raise NoKitsFoundError, 'Bad media provided, no kits found'

    def checkKitInstalled(self, kitname, kitver, kitarch):
        """
        Returns True if specified kit is already in the DB, False otherwise.
        """

        return [] != self.__db.Kits.select_by(rname=kitname, version=kitver,
                                              arch=kitarch)

    def selectKit(self, mountpoint, dirlst = None):
        '''selectKit method displays kits available on the media provided and prompts to choose
           returns None if it fails or the kit name/dir if it succeeds'''

        if dirlst == None:
            dirlst = mountpoint.dirs()
            for i in range(0, len(dirlst)):
                if not glob.glob('%s/%s/kit-*.rpm' % (mountpoint, dirlst[i])):
                    del dirlst[i]
            if not dirlst:
                raise NoKitsFoundError
        #TO BE CONTINUED
        
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
        mountP.communicate()

        if mountP.returncode != 0:
            tmpmntdir.rmdir()
            errors = self.__handleMountError(mountP.returncode)
            raise CannotMountKitMediaError, ''.join(errors)

        self.mountpoint = tmpmntdir

    def unmountMedia(self):
        """
        self.mountpoint is unmounted, removed and set to None.
        """

        if self.mountpoint:
            #umountP = subprocess.Popen('umount -l %s' %
            umountP = subprocess.Popen('umount %s' % self.mountpoint,
                                       shell=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            umountP.communicate()
            self.mountpoint.rmdir()
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
                        (osdistro.ostype, kit['ver'], kit['arch'])
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

        # add mock component to complete link from nodegroups to kits
        comp = self.__db.Components(cname=kit['longname'],
                                    cdesc='%s mock component' % kit['longname'])
        newkit.components.append(comp)

        if self.installer:
            ngs = self.__db.NodeGroups.select(
                    self.__db.NodeGroups.c.ngname.in_('master', 'compute',
                                                      'installer'))
        else:
            ngs = self.__db.NodeGroups.select(
                    self.__db.NodeGroups.c.ngname.in_('compute', 'installer'))

        for ng in ngs:
            if comp not in ng.components:
                ng.components.append(comp)

        self.__db.flush()

    def deleteKit(self, del_name='', del_version='', del_arch=''):
        '''perform the delete operation on the kit specified '''

        try:
            assert(bool(del_name))
        except AssertionError,msg:
            raise AssertionError, 'Name for kit to delete not specified'

        kits = []

        del_path = ''
        if del_arch and del_version:
            kits = self.__db.Kits.select_by(rname=del_name,
                                            version=del_version, arch=del_arch)
            kl.info("Removing kit '%s', version %s, arch %s" %
                    (del_name, del_version, del_arch))
            del_version = '-' + del_version
            del_arch = '-' + del_arch
            del_path = self.kits_dir / del_name / del_version / del_arch
        elif del_version:
            kits = self.__db.Kits.select_by(rname=del_name, version=del_version)
            kl.info("Removing kit '%s', version %s, all architectures" %
                    (del_name, del_version))
            del_version = '-' + del_version
            del_path = self.kits_dir / del_name / del_version
        else:
            kits = self.__db.Kits.select_by(rname=del_name)
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

    def listKit(self, ls_name=''):
        '''if the kit was specified, lists component summary for it, else prints
         kit table summary'''

        if ls_name:
            return self.__db.Kits.select_by(
                        self.__db.Kits.c.rname.like('%%%s%%' % ls_name))
        else:
            return self.__db.Kits.select()
