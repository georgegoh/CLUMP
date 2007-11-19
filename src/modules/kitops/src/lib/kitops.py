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
import sqlalchemy as sa

from kusu.boot.tool import BootMediaTool
from kusu.boot.distro import *
from kusu.kitops.package import PackageFactory
from kusu.util.tools import cpio_copytree
from kusu.util import rpmtool
from kusu.buildkit import processKitInfo
from kusu.util.errors import *
from kusu.util.rpmtool import RPM
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
        self.i_mounted = False
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
            raise KitAlreadyInstalledError, \
                    "Kit '%s-%s-%s' already installed" % \
                    (kit['name'], kit['version'], kit['arch'])

        # copy the RPMS
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

        # populate the kit DB table with info
        newkit = self.__db.Kits(rname=kit['name'], rdesc=kit['description'],
                                version=kit['version'], arch=kit['arch'],
                                removable=kit['removable'])
        newkit.save()
        
        # Add kit to packages table for installer nodegroup
        installngs = self.__db.NodeGroups.select_by(type='installer')
        for installng in installngs:
            installng.packages.append(
                                self.__db.Packages(packagename=kit['pkgname']))

        self.__db.flush()
        kl.debug('Addkit kid: %s', newkit.kid)

        # check/populate component table
        try:
            updated_ngtypes = self.updateComponents(newkit.kid, kitinfo[2])
        except ComponentAlreadyInstalledError, msg:
            # updateComponents encountered an error, remove kit from DB
            newkit.removable = True
            newkit.flush()
            self.deleteKit(kit['name'], kit['version'], kit['arch'])
            raise ComponentAlreadyInstalledError, msg
            
        # install the kit RPM
        if not self.installer:
            rpmP = subprocess.Popen('rpm --quiet --force --nodeps -i %s' %
                                    (kitpath / kitrpm),
                                    shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            o, e = rpmP.communicate()
            kl.debug('Installing kit RPM stdout: %s, stderr: %s', o, e)

            if rpmP.returncode != 0:
                # failed installing RPM, remove kit from DB
                newkit.removable = True
                newkit.update()
                newkit.flush()
                self.deleteKit(kit['name'], kit['version'], kit['arch'])
                raise InstallKitRPMError, 'Kit RPM installation ' + \
                    'failed, return code: %d' % rpmP.returncode
        else:
            rpm = kitinfo[3]

            # execute pre section
            cfmsync = self.addRPMPreScript(kit['name'],
                                           kit['version'],
                                           kit['arch'],
                                           rpm.getPre())

            # execute post section
            cfmsync = self.addRPMPostScript(kit['name'],
                                            kit['version'],
                                            kit['arch'],
                                            rpm.getPost()) or cfmsync

            if cfmsync: self.add_cfmsync_script()

        # RPM install successful, add kit to DB

        # handling driverpacks

        # get the handle on components
        components = kitinfo[2]
        # FIXME: Put a proper try/except here!

        for comp in components:
            if 'driverpacks' in comp:
                # there should be one and only one component with the pkgname we want
                _comp = self.__db.Components.select_by(cname=comp['pkgname'])[0]
                for _dpack in comp['driverpacks']:
                    dpname = _dpack['name']
                    dpdesc = _dpack['description']
                    dpack = self.__db.DriverPacks()
                    dpack.dpname = dpname
                    dpack.dpdesc = dpdesc
                    _comp.driverpacks.append(dpack)

                    self.__db.flush()

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

                if self.installer:
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
        for kitrpm in self.mountpoint.walkfiles('kit-*.rpm'):
            # TODO: should keep track of these locations and make sure we don't
            # have multiple kit RPMs in the same directory tree
            location = kitrpm.abspath().dirname()

            # extract the kitrpm contents into a temporary directory
            tmpdir = path(tempfile.mkdtemp(prefix='kitops', dir=self.tmpprefix))
            rpm = RPM(str(kitrpm))
            rpm.extract(tmpdir)

            kitinfos = []
            for kitinfo in tmpdir.walkfiles('kitinfo'):
                kitinfos.append(kitinfo)

            # only one kitinfo file permitted
            if len(kitinfos) > 1:
                tmpdir.rmtree()
                raise InvalidKitInfoError, \
                    'Found %d kitinfo files, only 1 expected' % len(kitinfos)

            if len(kitinfos) == 0: # no kitinfo file, revert to legacy discovery
                kl.info('No kitinfo found in %s, determining metadata ' +
                        'from RPMs directly', kitrpm)
                kit, components = self.inspectRPMs(kitrpm)
                if kit:
                    availableKits.append((location, kit, components, rpm))

            for kitinfo in kitinfos:
                kit, components = processKitInfo(kitinfo)
                availableKits.append((location, kit, components, rpm))

            tmpdir.rmtree()

        if not availableKits:
            self.unmountMedia()

        kl.debug("Kits available: %s", availableKits)
        return availableKits

    def inspectRPMs(self, kitrpm):
        """
        Determine kit and component info by inspecting RPMs.
        """

        kit = {'version': '', 'release': '', 'pkgname': '', 'name': '',
               'arch': '', 'description': '', 'dependencies': [],
               'license': '', 'scripts': [], 'removable': True}
        components = []

        #extract some RPMTAG info
        kitinst = PackageFactory(str(kitrpm))
        kit['version'] = kitinst.getVersion()
        kit['release'] = kitinst.getRelease()
        kit['pkgname'] = kitinst.getName()
        kit['name'] = kitinst.getName()
        kit['arch'] = kitinst.getArch()
        kit['description'] = kitinst.getSummary()

        if kit['name'].startswith('kit-'):
            kit['name'] = kit['name'][len('kit-'):]

        complist = kitrpm.abspath().dirname().glob('component-*.rpm')
        for comploc in complist:
            comp = {'compversion': '', 'comprelease': '', 'pkgname': '',
                    'name': '', 'arch': '', 'description': '', 'ngtypes': [],
                    'ostype': '', 'osversion': '', 
                    'driverpacks':False}


            compinst = PackageFactory(str(comploc))
            comp['compversion'] = compinst.getVersion()
            comp['comprelease'] = compinst.getRelease()
            comp['pkgname'] = compinst.getName()
            comp['name'] = compinst.getName()
            comp['arch'] = compinst.getArch()
            comp['description'] = compinst.getSummary()

            if comp['name'].startswith('component-'):
                comp['name'] = comp['name'][len('component-'):]

            components.append(comp)

        return kit, components

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
        self.i_mounted = True

    def unmountMedia(self):
        """
        self.mountpoint is unmounted, removed and set to None.
        """

        if self.i_mounted and self.mountpoint and self.mountpoint.ismount():
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
            bmt.copyInitrd(self.mountpoint, self.pxeboot_dir / kit['initrd'],
                           overwrite=True)
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
                                removable=True, arch=kit['arch'])
        newkit.save()
        newkit.flush()
        
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
        newkit.components.append(comp)
 
        # setup driverpacks entry and associate it with the mock component
        for kpkg in kpkgs:
            dpack = self.__db.DriverPacks()
            dpack.dpname = kpkg.getFilename().basename() 
            desc = ' %s for %s' % (kpkg.summary,kpkg.arch)
            dpack.dpdesc = desc        
            comp.driverpacks.append(dpack)

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

        if not kits:
            msg = "Kit '%s" % del_name
            if del_version:
                msg += '-%s' % del_version
            if del_arch:
                msg += '-%s' % del_arch
            msg += "' is not in the database"
            raise KitNotInstalledError, msg

        del_path = ''
        if del_arch and del_version:
            kl.info("Removing kit '%s', version %s, arch %s" %
                    (del_name, del_version, del_arch))
            del_path = self.kits_dir / del_name / del_version / del_arch
            del_version = '-' + del_version
            del_arch = '-' + del_arch
            del_depth = 2
        elif del_version:
            kl.info("Removing kit '%s', version %s, all architectures" %
                    (del_name, del_version))
            del_path = self.kits_dir / del_name / del_version
            del_version = '-' + del_version
            del_depth = 1
        else:
            kl.info("Removing kit '%s', all versions and architectures" %
                    del_name)
            del_path = self.kits_dir / del_name
            del_depth = 0

        error_kits = []
        for kit in kits:
            if not self.installer and not kit.removable:
                error_kits.append("Kit '%s-%s-%s' is not removable" % 
                                   (kit.rname, kit.version, kit.arch))
                continue

            repos = self.__db.ReposHaveKits.select_by(kid=kit.kid)
            if repos:
                error_kits.append("Cannot delete kit " +
                                  "'%s-%s-%s', it is used by a repo" %
                                  (kit.rname, kit.version, kit.arch))
                continue
                
            try:
                # remove component info from DB
                for component in kit.components:
                    for dpack in component.driverpacks:
                        dpack.delete()
                    component.delete()

                # remove packages
                pkgs = self.__db.Packages.select_by(packagename='kit-%s' %
                                                    kit.rname)
                for pkg in pkgs:
                    pkg.delete()

                # remove kit DB info
                kit.delete()
            except sa.exceptions.SQLError, e:
                raise DeleteKitsError, [e]
 
            # uninstall kit RPM
            if not kit.isOS and not self.installer:
                cmds = ['/bin/rpm', '--quiet', '-e', '--nodeps',
                        'kit-%s-%s' % (kit.rname, kit.version)]
                rpmP = subprocess.Popen(cmds,# shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                o, e = rpmP.communicate()
                kl.debug('Removing kit RPM stdout: %s, stderr: %s', o, e)
            elif self.installer:
                # remove any scripts
                self.removeRPMScripts(kit.rname, kit.version, kit.arch)

            # remove tftpboot contents
            if kit.isOS:
                p = self.pxeboot_dir / ('initrd-%s.img' % kit.longname)
                if p.exists(): p.remove()
                p = self.pxeboot_dir / ('kernel-%s' % kit.longname)
                if p.exists(): p.remove()
                if not self.pxeboot_dir.listdir():  # directory is empty
                    self.pxeboot_dir.rmdir()

            # remove the RPMS kit contents
            if del_path.exists(): del_path.rmtree()

            deeper_del_path = del_path
            for dd in xrange(del_depth):
                deeper_del_path = deeper_del_path.dirname()
                if not deeper_del_path.listdir():
                    deeper_del_path.rmdir()

        self.__db.flush()

        if error_kits:
            raise DeleteKitsError, error_kits

    def addRPMPreScript(self, kitname, kitver, kitarch, cmd):
        """
        Places commands in cmd into a kusurc pre section script.
        """

        return self.addRPMScript(kitname, kitver, kitarch, cmd, 0)

    def addRPMPostScript(self, kitname, kitver, kitarch, cmd):
        """
        Places commands in cmd into a kusurc post section script.
        """

        return self.addRPMScript(kitname, kitver, kitarch, cmd, 1)

    def addRPMScript(self, kitname, kitver, kitarch, cmd, order):
        """
        Places commands in cmd into a kusurc script.

        Returns True if the script is written to disk, False otherwise.
        """

        script = self.getRPMScriptName(kitname, kitver, kitarch, order)

        if script.exists():
            kl.debug("Script '%s' already exists, doing nothing" % script)
            return False

        # ignore if only comments/empty lines in script
        skipScript = True
        for command in cmd.split('\n'):
            if command.strip() != '' and not command.strip().startswith('#'):
                skipScript = False
                break

        if skipScript:
            kl.debug("Script '%s' contains no commands, doing nothing" % script)
            return False

        kl.debug("Writing to '%s' the following:\n%s", script, cmd)

        if not script.parent.exists():
            script.parent.makedirs()

        f = open(script, 'w')
        f.write(cmd + '\nrm -r $0\n') # also delete myself when I'm finished
        f.flush()
        f.close()

        script.chmod(0766)

        return True

    def removeRPMScripts(self, kitname, kitver, kitarch):
        """
        Removes kusurc script for this kit RPM.
        """

        for order in [0, 1]:
            script = self.getRPMScriptName(kitname, kitver, kitarch, order)

            if script.exists():
                kl.debug("Removing '%s'", script)
                script.remove()

            kl.debug("Script '%s' does not exist, doing nothing", script)

    def getRPMScriptName(self, kitname, kitver, kitarch, order):
        """
        Generates a kusurc script name for this kit.
        """

        script = path('S01RPMScript-%s-%s-%s-%s.rc' % (kitname, kitver,
                                                       kitarch, order))
        return self.prefix / 'etc/rc.kusu.d' / script

    def add_cfmsync_script(self):
        """
        Generate an rc script which runs cfmsync -p, if said script doesn't
        already exist.
        """

        script = self.prefix / 'etc/rc.kusu.d/S99RunCFMSync.rc'

        if not script.exists(): # only do this once
            if not script.parent.exists():
                script.parent.makedirs()

            f = open(script, 'w')
            f.write('\n'.join(('#!/bin/bash', 'cfmsync -p', 'rm -r $0\n')))
            f.flush()
            f.close()

            script.chmod(0766)

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
