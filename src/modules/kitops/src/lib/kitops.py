#!/usr/bin/env python
#
# Kusu kitops - kit operations tool
#
# $Id$
#
# Copyright (C) 2007 Platform Computing
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Author: atumanov

import sys
import os
import urllib
import urlparse
import tempfile
import glob
import re
import subprocess
from path import path

import kusu.core.database as db
from kusu.boot.tool import BootMediaTool
from kusu.boot.distro import *
from kusu.kitops.package import PackageFactory
from kusu.util.tools import cpio_copytree

import kusu.util.log as kusulog
kl = kusulog.getKusuLog('kitops')

EMOUNT_OK       =  0
EMOUNT_FAIL     = -1
EKITLOC_FAIL    = -2
EKITADD_FAIL    = -3
EKITDEL_FAIL    = -4
EKITUP_FAIL     = -5
EKITLST_FAIL    = -6
EDB_FAIL        = -7
EKIT_BAD        = -8

class EMOUNTFAIL(Exception):
    def __init__(self,rv):
        self.rv = rv

    def __str__(self):
        return '%s' % self.rv

    def __int__(self):
        return self.rv

class KitOps:
    def __init__(self, **kw):
        self.installer = False
        self.kitname = ''
        self.kitmedia = ''
        self.mountpoint = None
        self.medialoc = None
        self.MediaDevice = None
        self.__tmpmntdir = None
        self.__tmprd1 = None
        self.__tmprootfs = None
        self.__db = None

        if 'db' in kw:
            self.__db = kw['db']
        if 'installer' in kw:
            self.installer = kw['installer']

        self.prefix = path(kw.get('prefix', '/'))
        self.kits_dir = self.prefix / 'depot/kits/'
        self.pxeboot_dir = self.prefix / 'tftpboot/pxelinux/'

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

        self.prefix = path(prefix)
        self.kits_dir = self.prefix / 'depot/kits/'
        self.pxeboot_dir = self.prefix / 'tftpboot/pxelinux/'

    def addKitPrepare(self):
        '''PreCondition:  add operation requested
           PostCondition: the kit media is mounted to self.mountpoint'''
        # 1. kit media was not specified - auto-detect
        if not self.kitmedia:
            return self.autoDetectMedia()

        # 2. kit media was specified - determine what to do with it
        rv = urlparse.urlparse(self.kitmedia)

        if rv[0]:
            kl.debug('Network kit specified, retrieving')
            (tmpfname, headers) = urllib.urlretrieve(self.kitmedia)
            self.medialoc = path(tmpfname)
        else :
            self.medialoc = path(self.kitmedia)

        #at this point, media can be either an iso file or a mountpoint dir
        if self.medialoc.isfile() and self.medialoc.ext.lower() == '.iso':
            kl.debug('Media ISO file provided: %s', self.medialoc)
            isISO = True
            try:
                self.mountMedia(self.medialoc, isISO)
            except EMOUNTFAIL,inst:
                self.__handleMountError(int(inst))
                return self.terminate(EKITLOC_FAIL)
            #mountpoint is defined - we're done
            return 0
                
        elif self.medialoc.isdir() and self.medialoc.ismount():
            kl.debug('Media mountpoint: %s', self.medialoc)
            self.mountpoint = self.medialoc

        else:
            #if neither of the above - error
            return self.terminate(EKITLOC_FAIL,
                             'Improper kit media location specification')

        #at this point we have the kit mounted to self.mountpoint
        try:
            assert(self.mountpoint
                   and self.mountpoint.isdir() and self.mountpoint.ismount())
        except AssertionError,msg:
            return self.terminate(EKITLOC_FAIL,
                             'Mountpoint sanity assertion failed\n%s' % msg)

        return 0

    def autoDetectMedia(self):
        """
        Attemp to find kit media.
        """

        lst = self.findMediaDevices()
        kl.debug('Media device list: %s', lst)
        try:
            assert(lst)
        except AssertionError:
            return self.terminate(EKITLOC_FAIL,
                             'Kit media neither specified nor found')

        for dev in lst:
            try:
                self.mountMedia('/dev/%s' % dev)
            except EMOUNTFAIL,inst:
                sys.stderr.write('kitops: failed mounting device /dev/%s\n' %
                                 dev)
                self.__handleMountError(int(inst))
            else:
                #mountpoint is defined - mount was successful
                self.MediaDevice = '/dev/%s' % dev
                return 0
        return self.terminate(EKITLOC_FAIL)

    def getOSDist(self):
        return DistroFactory(str(self.mountpoint))

    def addKit(self):
        '''perform the add operation on the kit specified 
           Precondition: kit is mounted to self.mountpoint'''

        #handle most common scenario
        if self.kitname == '':  #kit to install was NOT specified
            self.determineKitName()

        # at this point self.kitname must be defined
        try:
            assert(bool(self.kitname))
        except AssertionError, msg:
            return self.terminate(EKITADD_FAIL,
                             "Kitname still not defined, terminating\n%s" % msg)

        kitRPMlst = path(self.mountpoint / self.kitname).glob('kit-%s*.rpm' %
                                                              self.kitname)
        try:
            assert(len(kitRPMlst)==1)
        except AssertionError,msg:
            return self.terminate(EKITADD_FAIL,
                             'Number of kit RPMs under %s' % 
                                 self.mountpoint / self.kitname + 
                             'must be exactly one\n%s' % msg)
            return EKITADD_FAIL

        kit = self.parseRPMTag(kitRPMlst[0].abspath())

        #check if this kit is already installed - by name and version
        try:
            if self.checkKitInstalled(kit['name'], kit['ver']):
                kl.debug("Kit '%s' version '%s' already installed",
                         kit['name'], kit['ver'])
                return self.terminate(EKITADD_FAIL)
        except Exception,msg:
            return self.terminate(EKITADD_FAIL,
                             'DB check on kit %s failed\n%s' %
                             (kit['name'], msg))

        # 1. copy the RPMS
        repodir = self.kits_dir / kit['name'] / kit['ver']
        if not repodir.exists():
            repodir.makedirs()

        #srcP = subprocess.Popen('tar cf - --exclude %s *.rpm' %
        #                        kit['rpmloc'].basename(),
        #                        cwd=self.mountpoint / self.kitname,
        #                        shell=True, stdout=subprocess.PIPE)
        #dstP = subprocess.Popen('tar xf -',
        #                        cwd=repodir, shell=True, stdin=srcP.stdout)
        srcP = subprocess.Popen('tar cf - *.rpm',
                                cwd=self.mountpoint / self.kitname,
                                shell=True, stdout=subprocess.PIPE)
        dstP = subprocess.Popen('tar xf -',
                                cwd=repodir, shell=True, stdin=srcP.stdout)
        dstP.communicate()

        # 2. populate the kit DB table with info
        session = self.__db.createSession()
        newkit = db.Kits(rname=kit['name'], rdesc=kit['sum'],
                         version=kit['ver'])
        session.save(newkit)
        
        # 3. install the kit RPM
        if not self.installer:
            try:
                rpmP = subprocess.Popen('rpm --quiet -i %s' % kit['rpmloc'],
                                        shell=True)
                rpmP.wait()
            except Exception, msg:
                return self.terminate(EKITADD_FAIL,
                                 'Kit RPM installation failed\n%s' % msg)

        # RPM install successful, add kit to DB
        session.flush()

        #extract the kit id to associate with components
        kit['kid'] = newkit.kid
        kl.debug('Addkit kid: %s', kit['kid'])

        # 4. check/populate component table
        rv = self.updateComponents(newkit)
        if 0 != rv:
            # updateComponents returned an error, remove kit from DB
            newkit.removable = True
            session.flush()
            session.close()
            self.deleteKit()
            return rv

        session.close()
        return 0

    def updateComponents(self, kit):
        """
        Update components table with information from kit.
        """

        session = self.__db.createSession()

        complst = path(self.mountpoint / kit.rname).glob('component-*.rpm')
        for comploc in complst:
            comp = {}
            comp['inst'] = PackageFactory(str(comploc))
            comp['name'] = comp['inst'].getName()
            if comp['name'].startswith('component-'):
                comp['name'] = comp['name'][len('component-'):]

            try:
                assert(bool(comp['name']))
            except:
                return self.terminate(EKITADD_FAIL,
                                 'Encountered corrupt name for ' +
                                 'component from %s' % comploc.basename())

            comp['ver'] = comp['inst'].getVersion()
            comp['sum'] = comp['inst'].getSummary()

            components = session.query(self.__db.components).select_by(
                                                            cname=comp['name'])

            if not components:
                # this component was not inserted in kit RPM's %post
                # generate an entry for this component
                newcomp = db.Components(kid=kit.kid, cname=comp['name'],
                                        cdesc=comp['sum'])
                session.save(newcomp)

                ngs = session.query(self.__db.nodegroups).select(
                    self.__db.nodegroups.c.ngname.in_('compute', 'installer'))

                for ng in ngs:
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

        session.flush()
        session.close()
        return 0

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
            return self.terminate(EKIT_BAD, 'Bad media provided, no kits found')

        if len(dirlst) == 1:
            self.kitname = dirlst[0].basename()
        elif len(dirlst) > 1:
            # TODO: Implement metakit handling.
            #handleMetaKit - return the kit to work with (self.kitname must be set)
            rv = self.selectKit(self.mountpoint, dirlst)
            if not rv:
                return self.terminate(EKIT_BAD,
                        'Bad media provided, no kits found')
            self.kitname = rv

    def findMediaDevices(self):
        '''Check for IDE/ATAPI, SCSI CD-ROM/DVD/CDRW devices, including USB storage
         devices.  Return the list of media devices to try'''
        MediaDevLst = []
        devdirlst = []

        devdirlst = path('/sys/block').listdir()
        devdirlst.sort()

        for dev in devdirlst:
            if re.match("^hd?", dev.basename()):
                #devinfo = open("/sys/block/%s/removable" % dev, 'r')
                devinfo = open(dev / 'removable', 'r')
                removable = devinfo.readline().strip()
                devinfo.close()
                if int(removable) == 1:
                    MediaDevLst.append(dev.basename())

            elif re.match("^sr?", dev):
                #devinfo = open("/sys/block/%s/removable" % dev, 'r')
                devinfo = open(dev / 'removable', 'r')
                removable = devinfo.readline().strip()
                devinfo.close()
                if int(removable) == 1:
                    scsidev = "scd%s" % dev.basename()[2:]
                    MediaDevLst.append(scsidev)
        return MediaDevLst

    def checkKitInstalled(self,kitname,kitver):
        '''Returns true if specified kit is already in the DB, false otherwise'''

        session = self.__db.createSession()

        kits = session.query(self.__db.kits).select_by(rname=kitname,
                                                       version=kitver)

        session.close()
        return [] != kits

    def selectKit(self, mountpoint, dirlst = None):
        '''selectKit method displays kits available on the media provided and prompts to choose
           returns None if it fails or the kit name/dir if it succeeds'''

        if dirlst == None:
            dirlst = mountpoint.dirs()
            for i in range(0, len(dirlst)):
                if not glob.glob('%s/%s/kit-*.rpm' % (mountpoint, dirlst[i])):
                    del dirlst[i]
            if not dirlst:
                return self.terminate(EKIT_BAD,
                        'Bad media provided, no kits found')
        #TO BE CONTINUED
        
    def mountMedia(self, media, isISO=False):
        ''' mount the specified media to a temporary dir
            PostCondition: self.__tmpmntdir & self.mountpoint are set & equal if successful'''
        self.__tmpmntdir = path(tempfile.mkdtemp(prefix='kitops'))

        if isISO:
            mountP = subprocess.Popen('mount -o loop %s %s 2> /dev/null' %
                                      (media, self.__tmpmntdir), shell=True)
        else:
            mountP = subprocess.Popen('mount %s %s 2> /dev/null' %
                                      (media, self.__tmpmntdir), shell=True)

        rv = mountP.wait()
        if rv != 0:
            self.__tmpmntdir.rmdir()
            self.__tmpmntdir = None
            raise EMOUNTFAIL(rv)

        self.mountpoint = self.__tmpmntdir

    def unmountMedia(self):
        '''PostCondition: self.mountpoint is unmounted, self.__tmpmntdir is removed,
            and both are set to None ''' 
        if self.mountpoint:
            #umountP = subprocess.Popen('umount -l %s 2> /dev/null' %
            umountP = subprocess.Popen('umount %s 2> /dev/null' %
                                       self.mountpoint, shell=True)
            self.mountpoint = None
        if self.__tmpmntdir:
            rmP = subprocess.Popen('rm -rf %s 2> /dev/null' % self.__tmpmntdir,
                                   shell=True)
            self.__tmpmntdir = None
        if self.__tmprd1:
            rmP = subprocess.Popen('rm -rf %s 2> /dev/null' % self.__tmprd1,
                                   shell=True)
            self.__tmprd1 = None
        if self.__tmprootfs:
            rmP = subprocess.Popen('rm -rf %s 2> /dev/null' % self.__tmprootfs,
                                   shell=True)
            self.__tmprootfs = None

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

        for key in errdict.keys():
            if status & key:
                kl.error('Mount fail error: %s', errdict[key])

    def prepareOSKit(self, osdistro):
        kit = {} #a struct to hold the kit info for the distro
        #instantiate a distro via the factory
        #osdistro = DistroFactory(str(self.mountpoint)) #distro instance
        kit['ver']    = osdistro.getVersion()          #os kit version in the db
        kit['arch']   = osdistro.getArch()             #os kit arch in the db
        kit['name'] = '%s-%s-%s' %(osdistro.ostype, kit['ver'], kit['arch'])
        kit['sum'] = 'OS kit for %s %s %s' % \
                        (osdistro.ostype, kit['ver'], kit['arch'])

        session = self.__db.createSession()
        kits = session.query(self.__db.kits).select_by(rname=kit['name'])
        session.close()

        if kits:
            return self.terminate((EKITADD_FAIL, None, None),
                             "OS kit '%s' already installed" % kit['name'])

        #copy kernel & initrd to pxedir
        if not self.pxeboot_dir.exists():
            self.pxeboot_dir.makedirs()

        bmt = BootMediaTool()
        fd, self.__tmprd1 = tempfile.mkstemp(prefix='kitops')
        os.close(fd)
        if os.path.exists(self.__tmprd1):
            os.remove(self.__tmprd1)
        self.__tmprootfs = tempfile.mkdtemp(prefix='kitops')

        bmt.copyInitrd(self.mountpoint, self.__tmprd1, True)
        bmt.unpackRootImg(self.__tmprd1, self.__tmprootfs)
        #patch self.__tmprootfs with necessary pieces HERE
        #pack up the patched rootfs & put it under tftpboot
        bmt.packRootImg(self.__tmprootfs,
                        self.pxeboot_dir / 'initrd-%s.img' % kit['name'])
        #copy kernel to tftpboot & rename
        bmt.copyKernel(self.mountpoint,
                       self.pxeboot_dir / 'kernel-%s' % kit['name'], True)

        return 0, kit, osdistro

    def copyOSKitMedia(self, kit, osdistro, media=''):
        if media:
            #unmount current, prepare for next
            self.unmountMedia()
            self.kitmedia = media
            kl.debug('Provided kit media: %s', self.kitmedia)
            self.addKitPrepare()

        #copy the RPMS to repo dir
        kl.info('Copying RPMs, this may take a while...')
        repodir = self.kits_dir / kit['name'] / kit['ver']
        if not repodir.exists():
            repodir.makedirs()

        try:
            cpio_copytree(self.mountpoint, repodir)
        except Exception,msg:
            return self.terminate(EKITADD_FAIL, 'Error during copy\n%s', msg)

        return 0
                
    def finalizeOSKit(self, kit):
        #populate the database with info
        session = self.__db.createSession()

        kit = db.Kits(rname=kit['name'], rdesc=kit['sum'], version=kit['ver'],
                      isOS=True, removable=False, arch=kit['arch'])
        session.save(kit)
        session.flush()

        # add mock component to complete link from nodegroups to kits
        comp = db.Components(cname=kit.rname, cdesc=kit.rname, os=kit.rname)
        kit.components.append(comp)

        ngs = session.query(self.__db.nodegroups).select(
                    self.__db.nodegroups.c.ngname.in_('compute', 'installer'))

        for ng in ngs:
            if comp not in ng.components:
                ng.components.append(comp)

        session.flush()
        session.close()

        return 0

    def deleteKit(self):
        '''perform the delete operation on the kit specified '''

        try:
            assert(bool(self.kitname))
        except AssertionError,msg:
            return self.terminate(EKITDEL_FAIL,
                             'Name for kit to delete not specified')

        session = self.__db.createSession()
        kit = session.query(self.__db.kits).selectfirst_by(rname=self.kitname)

        if not kit:
            return self.terminate(EKITDEL_FAIL,
                             "Kit '%s' is not in the database" % self.kitname)

        if not kit.removable:
            return self.terminate(EKITDEL_FAIL,
                             "Kit '%s' is not removable" % kit.rname)

        repos = session.query(self.__db.repos).select_by(kid=kit.kid)
        if repos:
            return self.terminate(EKITDEL_FAIL,
                             "Cannot delete kit '%s', it is used by a repo" %
                             kit.rname)
            
        #the kit is NOT in use
        #1. remove the RPMS from /depot/kits/<kitname>/<kitver>
        path(self.kits_dir / kit.rname / kit.version).rmtree()

        #2. remove kit RPM
        if not self.installer:
            rmP = subprocess.Popen('/bin/rpm --quiet -e --nodeps kit-%s' %
                                   kit.rname, shell=True)
            rmP.wait()

        #3. remove component info from DB
        for component in kit.components:
            session.delete(component)

        #4. remove kit DB info
        session.delete(kit)
        
        session.flush()
        session.close()

        #5. done
        return 0

    def listKit(self):
        '''if the kit was specified, lists component summary for it, else prints
         kit table summary'''

        session = self.__db.createSession()

        kits = []
        if self.kitname:
            kits = session.query(self.__db.kits).select_by(
                        self.__db.kits.c.rname.like('%%%s%%' % self.kitname))
        else:
            kits = session.query(self.__db.kits).select()

        session.close()
        return kits

    def terminate(self, rv, msg=''):
        """
        Perform some cleanup before returning rv and logging msg, if applicable.
        """

        self.unmountMedia()

        if msg:
            kl.error(msg)

        return rv
