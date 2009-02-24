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
from sets import Set
import sqlalchemy as sa
from primitive.support.osfamily import getOSNames, matchTuple
from kusu.boot.tool import BootMediaTool
from kusu.boot.distro import *
from kusu.kitops.package import PackageFactory
from kusu.kitops.addkit_strategies import AddKitStrategy
from kusu.kitops.deletekit_strategies import DeleteKitStrategy
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


# We currently want to limit the extent of association
# to certain ngids and below. 
NG_ASSOC_THRESHOLD = 2
USE_NG_ASSOC_THRESHOLD = True


class KitOps:
    def __init__(self, **kw):
        self.installer = kw.get('installer', False) # installer environment?
        self.kitmedia = ''
        self.dlkitiso = None
        self.mountpoint = None
        self.i_mounted = False
        self.medialoc = None
        self.__db = kw.get('db', None)

        self.setPrefix(path(kw.get('prefix', '/')))
        self.setTmpPrefix(path(kw.get('tmpprefix', '/tmp')))

    def setKitMedia(self, kitmedia):
        self.kitmedia = kitmedia

    def setDB(self, db):
        self.__db = db

    def setPrefix(self, prefix):
        """
        Provide a new prefix.
        """
    
        kits_root = 'depot/kits/'
        pixie_root = 'tftpboot/kusu/'
        contrib_root = 'depot/contrib'
        kusu_root = 'opt/kusu'
        docs_root = 'depot/www'

        if self.__db:
            row = self.__db.AppGlobals.select_by(kname = 'DEPOT_KITS_ROOT')
            if row: kits_root =  row[0].kvalue

            row = self.__db.AppGlobals.select_by(kname = 'PIXIE_ROOT')
            if row: pixie_root =  row[0].kvalue

            row = self.__db.AppGlobals.select_by(kname = 'DEPOT_CONTRIB_ROOT')
            if row: contrib_root =  row[0].kvalue

            row = self.__db.AppGlobals.select_by(kname = 'DEPOT_DOCS_ROOT')
            if row: docs_root =  row[0].kvalue

        if kits_root[0] == '/': kits_root = kits_root[1:]
        if pixie_root[0] == '/': pixie_root = pixie_root[1:]
        if contrib_root[0] == '/': contrib_root = contrib_root[1:]
        if kusu_root[0] == '/': kusu_root = kusu_root[1:]
        if docs_root[0] == '/': docs_root = docs_root[1:]

        if prefix:
            self.prefix = path(prefix)
            self.kits_dir = self.prefix / kits_root
            self.pxeboot_dir = self.prefix / pixie_root
            self.contrib_dir = self.prefix / contrib_root
            self.kusu_root = self.prefix / kusu_root
            self.docs_dir = self.prefix / docs_root

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
            try:
                (self.dlkitiso, headers) = urllib.urlretrieve(self.kitmedia)
            except IOError, e:
                # The user likely passed in a bad URL.
                raise UnrecognizedKitMediaError, \
                    'Error accessing or opening kit media: %s' % e.args[0]
                
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
                                    'Kit media not found or unavailable'

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

        try:
            return self.getAvailableKits()
        except (InvalidRPMHeader, KitinfoSyntaxError):
            self.unmountMedia()
            raise

    def addKit(self, kitinfo, api='0.1'):
        '''perform the add operation on the kit specified 
           Precondition: kit is mounted to self.mountpoint'''
        if self.installer and api=='0.2':
            api = '0.2-installer'
        return AddKitStrategy[api](self, self.__db, kitinfo)

    def getKitComponents(self, kid, os):
        kitinfo = self.kits_dir / str(kid) / 'kitinfo'
        if not kitinfo.exists():
            return []
        kit, components = processKitInfo(kitinfo)
        if kit['api'] != '0.2':
            return []

        target_os = (os.name, os.major, os.minor, os.arch)
        components_list = []
        for comp in components:
            os_tuples = []
            try:
                for tup in comp['os']:
                    for os_name in getOSNames(tup['name'], default=[tup['name']]):
                        os_tuples.append((os_name, tup['major'], tup['minor'], tup['arch']))
            except KeyError:
                break
            try:
                if matchTuple(target_os, os_tuples):
                    db_comp = self.__db.Components.selectfirst_by(cname=comp['pkgname'], kid=kid)
                    components_list.append(db_comp)
            except KeyError:
                pass
        return components_list

    def updateComponents(self, kit, components):
        """
        Update components table with information from kit.
        """
        kid = kit.kid
        compnames = []
        for comp in components:
            compnames.append(comp['pkgname'])

        oldcomponents = self.__db.Components.select(
                self.__db.Components.c.cname.in_(*compnames))

        affected_ngs = Set()
        for comp in components:
            newcomponent = True
            for oldcomp in oldcomponents:
                if comp['pkgname'] == oldcomp.cname:
                    if comp.has_key('ostype') and comp['ostype'] == oldcomp.os:
                        newcomponent = False
                        kl.debug('Component %s already exists in database' % comp['pkgname'])

            if newcomponent:
                kl.debug('Component %s does not already exist in database' % comp['pkgname'])
                # This component does not yet exist in the DB, so add it now.
                # NOTE: storing pkgname as component name, since that's the
                # RPM package to be installed.
                if comp.has_key('os'):
                    comp_ngtypes = comp.get('ngtypes', [])
                    ngtypes = ';'.join(comp_ngtypes)
                    newcomp = self.__db.Components(kid=kid, cname=comp['pkgname'],
                                                   cdesc=comp['description'],
                                                   ngtypes=ngtypes)
                    newcomp.save()
                    newcomp.flush()
                else:
                    os = comp['ostype']
                    newcomp = self.__db.Components(kid=kid, cname=comp['pkgname'],
                                                   cdesc=comp['description'],
                                                   os=os)
                    # also store the OS/ARCH -- but how to determine?
                    newcomp.save()
                    newcomp.flush()

                ngs = self.__db.NodeGroups.select(
                    self.__db.NodeGroups.c.type.in_(*comp['ngtypes']))
                kl.debug('comp[ngtypes]: %s, ngs: %s' % (comp['ngtypes'], [ng.ngname for ng in ngs]))

                # associate components to nodegroups
                for ng in ngs:
                    kl.debug('Attempting to associate component %s.%s to nodegroup %s' % (newcomp.cid, newcomp.cname, ng.ngname))
                    kl.debug('installer mode: %s' % self.installer)
                    if not self.installer and ng.repo:
                        kl.debug('newcomp: %s, ng.repo.os: %s matches: %s matched: %s' % (newcomp, ng.repo.os, self.getKitComponents(kit.kid, ng.repo.os),
                                                                           newcomp in self.getKitComponents(kit.kid, ng.repo.os)))
                        kl.debug('USE_NG_ASSOC_THRESHOLD: %s NG_ASSOC_THRESHOLD: %s' % (USE_NG_ASSOC_THRESHOLD, NG_ASSOC_THRESHOLD))
                    if self.installer:
                        kl.debug('Associating component %s to nodegroup %s' % (newcomp.cname, ng.ngname))
                        ng.components.append(newcomp)
                        affected_ngs.add(ng.ngname)
                    elif USE_NG_ASSOC_THRESHOLD and ng.ngid > NG_ASSOC_THRESHOLD:
                        pass
                    elif ng.repo and newcomp in self.getKitComponents(kit.kid, ng.repo.os):
                        kl.debug('Associating component %s to nodegroup %s' % (newcomp.cname, ng.ngname))
                        ng.components.append(newcomp)
                        affected_ngs.add(ng.ngname)

                # associate driver packs to components
                if comp.has_key('driverpacks'):
                    for dp in comp['driverpacks']:
                        dpack = self.__db.DriverPacks()
                        dpack.dpname = dp['name']
                        dpack.dpdesc = dp['description']
                        newcomp.driverpacks.append(dpack)

                self.__db.flush()

            else:
                raise ComponentAlreadyInstalledError, \
                    'Component %s already installed' % comp['pkgname']

        self.__db.flush()
        return affected_ngs

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
            rpm = rpmtool.RPM(str(kitrpm))
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
                    # no kitinfo, so API = 0.1 by default.
                    availableKits.append((location, kit, components, rpm, '0.1'))

            for kitinfo in kitinfos:
                kit, components = processKitInfo(kitinfo)
                api = kit.get('api', '0.1')
                availableKits.append((location, kit, components, rpm, api))

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
        kit['filelist'] = kitinst.getFileList()

        if kit['name'].startswith('kit-'):
            kit['name'] = kit['name'][len('kit-'):]

        complist = kitrpm.abspath().dirname().glob('component-*.rpm')
        for comploc in complist:
            comp = {'compversion': '', 'comprelease': '', 'pkgname': '',
                    'name': '', 'arch': '', 'description': '', 'ngtypes': [],
                    'ostype': '', 'osversion': '', 
                    'driverpacks':[]}


            compinst = PackageFactory(str(comploc))
            comp['compversion'] = compinst.getVersion()
            comp['comprelease'] = compinst.getRelease()
            comp['pkgname'] = compinst.getName()
            comp['name'] = compinst.getName()
            comp['arch'] = compinst.getArch()
            comp['description'] = compinst.getSummary()
            comp['filelist'] = compinst.getFileList()

            if comp['name'].startswith('component-'):
                comp['name'] = comp['name'][len('component-'):]

            components.append(comp)

        return kit, components

    def getKitRPMInfo(self, kitrpm):
        """
        kitrpm = object of class kusu.util.rpmtool.RPM.
        """
        tmpdir = path(tempfile.mkdtemp(prefix='kitinfo-', dir=self.tmpprefix))
        kitrpm.extract(tmpdir)
        kitinfo = tmpdir / 'kitinfo'
        if not kitinfo.exists():
            return None
        kits, components = processKitInfo(kitinfo)
        # cleanup
        tmpdir.rmtree()
        return kits, components

    def getKitApi(self, kid):
        kitinfo = self.kits_dir / str(kid) / 'kitinfo'
        if not kitinfo.exists():
            return '0.1'
        kit, components = processKitInfo(kitinfo)
        return kit.get('api', '0.1')

    def mountMedia(self, media, isISO=False):
        """
        Mount the specified media to a temporary directory.
        """

        tmpmntdir = path(tempfile.mkdtemp(prefix='kitops',
                                          dir=self.tmpprefix))

        cmd = 'mount \"%s\" %s' % (media, tmpmntdir)
        if isISO:
            cmd = 'mount -o loop \"%s\" %s' % (media, tmpmntdir)

        mountP = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        out, err = mountP.communicate()

        if mountP.returncode != 0:
            kl.debug('Mount stdout: %s', out)
            kl.debug('Mount stderr: %s', err)
            tmpmntdir.rmdir()
            errors = self.__handleMountError(mountP.returncode)
            raise CannotMountKitMediaError, \
                'Mount error(s) %d: %s' % (mountP.returncode,
                                           ', '.join(errors)) + '\n%s' % err

        self.mountpoint = tmpmntdir
        self.i_mounted = True

    def unmountMedia(self):
        """
        self.mountpoint is unmounted, removed and set to None.
        """

        if self.i_mounted and self.mountpoint and self.mountpoint.ismount():
            #umountP = subprocess.Popen('umount -l %s' %
            umountP = subprocess.Popen('umount \"%s\"' % self.mountpoint,
                                       shell=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            out, err = umountP.communicate()

            if umountP.returncode == 0:
                self.mountpoint.rmdir()
            else:
                kl.error('Unable to umount %s' % self.mountpoint)

            self.mountpoint = None

        if self.dlkitiso and self.dlkitiso.exists():
            self.dlkitiso.remove()
            self.dlkitiso = None

    def __handleMountError(self, rv):
        '''handle the mount exit status when it's non-zero. Return nothing'''
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
            if rv & key:
                kl.error('Mount fail error: %s', errdict[key])
                errors.append(errdict[key])

        return errors

    def prepareOSKit(self, osdistro):
        kit = {} #a struct to hold the kit info for the distro
        kit['ver'] = osdistro.getVersion()          #os kit version in the db
        kit['major'] = osdistro.getMajorVersion()
        kit['minor'] = osdistro.getMinorVersion()
        kit['arch'] = osdistro.getArch()            #os kit arch in the db
        kit['name'] = osdistro.ostype.lower()
        kit['longname'] = '%s-%s.%s-%s' % (kit['name'], kit['major'], kit['minor'], kit['arch'])
        kit['sum'] = 'OS kit for %s %s.%s %s' % \
                        (kit['name'], kit['major'], kit['minor'], kit['arch'])

        kit['initrd'] = 'initrd-%s.img' % kit['longname']
        kit['kernel'] = 'kernel-%s' % kit['longname']
    
        kits = self.__db.OS.select_by(name=kit['name'], 
                                      major=kit['major'], minor=kit['minor'],
                                      arch=kit['arch'])

        if kits:
            self.unmountMedia()
            raise KitAlreadyInstalledError, \
                    "OS kit '%s' already installed" % kit['longname']

        oskit = self.__db.OS.select_by(name=kit['name'], major=kit['major'],
                                    minor=kit['minor'], arch=kit['arch'])
        if oskit:
            osid = oskit[0].osid
        else:
            newOS = self.__db.OS(name=kit['name'], major=kit['major'],
                                 minor=kit['minor'], arch=kit['arch'])
            newOS.save()
            newOS.flush()
            osid = newOS.osid
        kit['osid'] = osid
        #populate the database with info
        newkit = self.__db.Kits(rname=kit['name'], rdesc=kit['sum'],
                                version=kit['ver'],
                                isOS=True, osid=kit['osid'],
                                removable=True, arch=kit['arch'])
        newkit.save()
        newkit.flush()
        kit['kid'] = newkit.kid

        #copy kernel & initrd to pxedir
        if not self.pxeboot_dir.exists():
            self.pxeboot_dir.makedirs()

        bmt = BootMediaTool()


        fd, tmprd1 = tempfile.mkstemp(prefix='kitops', dir=self.tmpprefix)
        os.close(fd)
        tmprd1 = path(tmprd1)

        if tmprd1.exists():
            tmprd1.remove()

        tmprootfs = path(tempfile.mkdtemp(prefix='kitops',
                                          dir=self.tmpprefix))
        # Check whether this is disc 1.
        if bmt.getKernelPath(self.mountpoint) is None \
            or bmt.getInitrdPath(self.mountpoint) is None:
            self.unmountMedia()
            raise UnrecognizedKitMediaError, "Please supply disc 1 first!"

        try:
            bmt.copyInitrd(self.mountpoint, self.pxeboot_dir / kit['initrd'],
                           overwrite=True)

            #copy kernel to tftpboot & rename
            bmt.copyKernel(self.mountpoint, self.pxeboot_dir / kit['kernel'], True)

        except (CopyError,FileAlreadyExists,IOError), e:
            # cleanup tmp stuff
            if tmprd1.exists(): tmprd1.remove()
            if tmprootfs.exists(): tmprootfs.rmtree()

            # consider the kernel/initrd invalidated, remove them
            if path(self.pxeboot_dir / kit['kernel']).exists():
                path(self.pxeboot_dir / kit['kernel']).remove()
            if path(self.pxeboot_dir / kit['initrd']).exists():
                path(self.pxeboot_dir / kit['initrd']).remove()

            raise
            
        return kit

    def copyOSKitMedia(self, kit):
        #copy the RPMS to repo dir
        kl.info('Copying RPMs, this may take a while...')
        repodir = self.kits_dir / str(kit['kid'])

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
        return repodir

    def makeContribDir(self, kit):
        
        if kit['name'] in ['opensuse']:
            contribdir = self.contrib_dir / kit['name'] / kit['major'] / kit['minor'] / kit['arch']
        else:
            contribdir = self.contrib_dir / kit['name'] / kit['ver'] / kit['arch']

        kl.debug('contrib dir: %s' % contribdir) 
        if not contribdir.exists():
            contribdir.makedirs()

    def finalizeOSKit(self, kit):
        
        # get the kernel packages
        oskitdir = self.kits_dir / str(kit['kid'])
        bmt = BootMediaTool()
        _kpkgs = bmt.getKernelPackages(oskitdir)
        kpkgs = []
        if _kpkgs:
            # change the kernel packages paths into rpmtool objects
            kpkgs = [rpmtool.RPM(str(k)) for k in _kpkgs]

        newkit = self.__db.Kits.select_by(kid=kit['kid'])[0]

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

    def deleteKit(self, del_name, del_id=None, del_version=None, del_arch=None):
        '''perform the delete operation on the kit specified '''

        try:
            assert(bool(del_name) or bool(del_id))
        except AssertionError,msg:
            raise AssertionError, 'Name/ID for kit to delete not specified'

        kits = self.findKits(del_name, del_id, del_version, del_arch)

        if not kits:
            if del_id:
                msg = "Kit '%s" % del_id
            else:
                msg = "Kit '%s" % del_name
                if del_id:
                    msg += '-%s' % del_id
                if del_version:
                    msg += '-%s' % del_version
                if del_arch:
                    msg += '-%s' % del_arch
                
            msg += "' is not in the database"
            raise KitNotInstalledError, msg

        error_kits = []
        for kit in kits:
            if not self.installer and not kit.removable:
                error_kits.append("Kit '%s-%s-%s' is not removable" % 
                                   (kit.rname, kit.version, kit.arch))
                continue

            kl.info("Removing kit '%s' kitid '%s', version %s, arch %s" %
                    (kit.rname, kit.kid, kit.version, kit.arch))

            repos = self.__db.ReposHaveKits.select_by(kid=kit.kid)
            if repos:
                error_kits.append("Cannot delete kit " +
                                  "'%s-%s-%s', it is used by a repo" %
                                  (kit.rname, kit.version, kit.arch))
                continue

            api = '0.1'
            kitinfo = self.kits_dir / str(kit.kid) / 'kitinfo'
            if kitinfo.exists():
                kit_struct, components = processKitInfo(kitinfo)
                api = kit_struct.get('api', '0.1')

            DeleteKitStrategy[api](self, self.__db, kit)

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
            kl.debug("Script '%s' is empty, will not be generated" % script)
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
            f.write('\n'.join(('#!/bin/bash', '# Generated by kitops', 'cfmsync -p >>/var/log/kusu/kusurc.log 2>&1', 'rm -r $0\n')))
            f.flush()
            f.close()

            script.chmod(0766)

    def listKit(self, kitname=None, kitid=None, kitver=None, kitarch=None):
        if kitname or kitid or kitver or kitarch:
            return self.findKits(kitname, kitid, kitver, kitarch)
        else:
            return self.__db.Kits.select()

    def getNodeGroups(self, kitid):
        import kusu.core.database as db
        return db.findNodeGroupsFromKit(self.__db, kitargs={'kid': kitid})

    def findKits(self, name, id, version, arch):
        kits = []
        kwargs = {}
        if name is not None: kwargs['rname'] = name
        if id is not None: kwargs['kid'] = id
        if version is not None: kwargs['version'] = version
        if arch is not None: kwargs['arch'] = arch
        kits = self.__db.Kits.select_by(**kwargs)
 
        return kits
