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
from kusu.core.db import KusuDB
from kusu.boot.tool import BootMediaTool
from kusu.boot.distro import *
from kusu.kitops.package import PackageFactory

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
        self.kitname = ''
        self.kitmedia = ''
        self.mountpoint = None
        self.medialoc = None
        self.MediaDevice = None
        self.__tmpmntdir = None
        self.__db = KusuDB()

        self.prefix = path(kw.get('prefix', os.environ.get('KUSU_ROOT', '/')))
        self.kits_dir = self.prefix / 'depot/kits/'
        self.pxeboot_dir = self.prefix / 'tftpboot/pxelinux/'

        try:
            #self.__db.connect('kusudb','apache')
            self.__db.connect('test')
        except Exception,msg:
            kl.error('Connection to DB failed: %s', msg)
            sys.exit(EDB_FAIL)

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
                return EKITLOC_FAIL
            #mountpoint is defined - we're done
            return 0
                
        elif self.medialoc.isdir() and self.medialoc.ismount():
            kl.debug('Media mountpoint: %s', self.medialoc)
            self.mountpoint = self.medialoc

        else:
            #if neither of the above - error
            self.errorMessage('kitops: improper kit media location specification\n')
            return EKITLOC_FAIL

        #at this point we have the kit mounted to self.mountpoint
        try:
            assert(self.mountpoint
                   and self.mountpoint.isdir() and self.mountpoint.ismount())
        except AssertionError,msg:
            sys.stderr.write('kitops: mountpoint sanity assertion failed:\n%s' %msg)
            return EKITLOC_FAIL

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
            sys.stderr.write('kitops: kit media neither specified nor found\n')
            return EKITLOC_FAIL

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
        return EKITLOC_FAIL

    def isOSKit(self):
        return path(self.mountpoint / 'isolinux').exists()

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
            sys.stderr.write("kitops: kitname still not defined - shouldn't happen\n%s" %msg)
            return EKITADD_FAIL

        kitRPMlst = path(self.mountpoint / self.kitname).glob('kit-%s*.rpm' %
                                                              self.kitname)
        try:
            assert(len(kitRPMlst)==1)
        except AssertionError,msg:
            sys.stderr.write('kitops: number of kit RPMs under %s' % 
                                 self.mountpoint / self.kitname + 
                             'must be exactly one\n%s' % msg)
            return EKITADD_FAIL

        kit = self.parseRPMTag(kitRPMlst[0].abspath())

        #check if this kit is already installed - by name and version
        try:
            if self.checkKitInstalled(kit['name'], kit['ver']):
                kl.debug("Kit '%s' version '%s' already installed",
                         kit['name'], kit['ver'])
                return EKITADD_FAIL
        except Exception,msg:
            kl.error('DB check on kit %s failed with: %s', kit['name'], msg)
            return EKITADD_FAIL

        # 1. copy the RPMS
        repodir = self.kits_dir / kit['name'] / kit['ver']
        if not repodir.exists():
            repodir.makedirs()

        srcP = subprocess.Popen('tar cf - --exclude %s *.rpm' %
                                kit['rpmloc'].basename(),
                                cwd=self.mountpoint / self.kitname,
                                shell=True, stdout=subprocess.PIPE)
        dstP = subprocess.Popen('tar xf -',
                                cwd=repodir, shell=True, stdin=srcP.stdout)
        dstP.communicate()

        # 2. populate the kit DB table with info
        query = "insert into kits (rname,rdesc,version) values \
            ('%s','%s','%s')" % (kit['name'], kit['sum'], kit['ver'])

        try:
            rv = self.__db.execute(query)
            kl.debug('Kit table udpate rv: %s', rv)
        except Exception,msg:
            kl.debug('FAIL query: %s, message: %s', query, msg)
            return EKITADD_FAIL

        #extract the kit id to associate with components
        query = "select kid from kits where rname='%s' and version='%s'" % \
                (kit['name'], kit['ver'])
        self.__db.execute(query)
        kit['kid'], = self.__db.fetchone()
        kl.debug('Addkit kid: %s', kit['kid'])

        # 3. install the kit RPM
        try:
            rpmP = subprocess.Popen('rpm --quiet -i %s' % kit['rpmloc'],
                                    shell=True)
            rpmP.wait()
        except Exception, msg:
            sys.stderr.write('kitops: kit RPM installation failed with message %s' %msg)
            #possible to reverse the DB transaction at this point and gracefully exit
            return EKITADD_FAIL

        # 4. check/populate component table
        self.updateComponents(kit)

        return 0

    def updateComponents(self, kit):
        """
        Update components table with information from kit.
        """

        complst = path(self.mountpoint / kit['name']).glob('component-*.rpm')
        for comploc in complst:
            comp = {}
            comp['inst'] = PackageFactory(str(comploc))
            comp['name'] = comp['inst'].getName()
            if comp['name'].startswith('component-'):
                comp['name'] = comp['name'][len('component-'):]

            try:
                assert(bool(comp['name']))
            except:
                sys.stderr.write('kitops: encountered corrupt name for ' +
                                 'component from %s' % comploc.basename())
                #handleAddFailure - reverse DB Transaction, remove RPMS?
                return EKITADD_FAIL

            comp['ver'] = comp['inst'].getVersion()
            comp['sum'] = comp['inst'].getSummary()
            query = "select cid,kid from components where cname = '%s'" % \
                    comp['name']
            self.__db.execute(query)
            #len>1 only if multi-distro explicit support
            comp['dbcidlst'] = self.__db.fetchall() 

            if not comp['dbcidlst']: 
                #this component was not inserted in kit RPM's %post
                #generate an entry for this component
                query = "insert into components (kid,cname,cdesc) " + \
                        "values (%s,'%s','%s')" % \
                        (kit['kid'], comp['name'], comp['sum'])
                self.__db.execute(query)
            else:
                for dbcid, dbkid in comp['dbcidlst']:
                    if dbkid > 0 and dbkid != kit['kid']:
                        kl.warning("Updating kit id for component '%s', cid=%s",
                                   comp['name'], dbcid)
                    query = "UPDATE components SET kid=%s where cid=%s" % \
                            (kit['kid'],dbcid)
                    self.__db.execute(query)

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
            kl.error('Bad media provided, no kits found')
            return EKIT_BAD

        if len(dirlst) == 1:
            self.kitname = dirlst[0].basename()
        elif len(dirlst) > 1:
            # TODO: Implement metakit handling.
            #handleMetaKit - return the kit to work with (self.kitname must be set)
            rv = self.selectKit(self.mountpoint, dirlst)
            if not rv:
                kl.error('Bad media provided, no kits found')
                return EKIT_BAD
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
        query = "select * from kits where rname='%s' and version='%s'" %(kitname,kitver)
        kl.debug('checkKitInstalled query: %s', query)
        try:
            self.__db.execute(query)
            rv = self.__db.fetchone()
        except Exception,msg:
            sys.stderr.write('kitops: Database query=%s failed with msg=%s' %(query,msg))
            raise

        if rv != None:
            return True
        return False

    def selectKit(self, mountpoint, dirlst = None):
        '''selectKit method displays kits available on the media provided and prompts to choose
           returns None if it fails or the kit name/dir if it succeeds'''

        if dirlst == None:
            dirlst = mountpoint.dirs()
            for i in range(0, len(dirlst)):
                if not glob.glob('%s/%s/kit-*.rpm' % (mountpoint, dirlst[i])):
                    del dirlst[i]
            if not dirlst:
                kl.error('Bad media provided, no kits found')
                return EKIT_BAD
        #TO BE CONTINUED
        
    def mountMedia(self, media, isISO=False):
        ''' mount the specified media to a temporary dir
            PostCondition: self.__tmpmntdir & self.mountpoint are set & equal if successful'''
        self.__tmpmntdir = path(tempfile.mkdtemp())

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

    def prepareOSKit(self):
        kit = {} #a struct to hold the kit info for the distro
        #instantiate a distro via the factory
        osdistro = DistroFactory(str(self.mountpoint)) #distro instance
        kit['ver']    = osdistro.getVersion()          #os kit version in the db
        kit['arch']   = osdistro.getArch()             #os kit arch in the db
        kit['name'] = '%s-%s-%s' %(osdistro.ostype, kit['ver'], kit['arch'])
        kit['sum'] = 'OS kit for %s %s %s' % \
                        (osdistro.ostype, kit['ver'], kit['arch'])

        query = "SELECT * from kits where rname = '%s'" %kit['name']
        kl.debug('addOSkit query: %s', query)
        try:
            self.__db.execute(query)
            rv = self.__db.fetchone()
        except Exception,msg:
            kl.error('FAIL query: %s, message: %s', query, msg)
            return EKITADD_FAIL, None, None

        if rv != None:
            kl.info("OS kit '%s' already installed", kit['name'])
            return EKITADD_FAIL, None, None

        #copy kernel & initrd to pxedir
        if not self.pxeboot_dir.exists():
            self.pxeboot_dir.makedirs()

        bmt = BootMediaTool()
        fd,tmprd1 = tempfile.mkstemp()
        os.close(fd)
        if os.path.exists(tmprd1):
            os.remove(tmprd1)
        tmprootfs = tempfile.mkdtemp()

        bmt.copyInitrd(self.mountpoint, tmprd1, True)
        bmt.unpackRootImg(tmprd1, tmprootfs)
        #patch tmprootfs with necessary pieces HERE
        #pack up the patched rootfs & put it under tftpboot
        bmt.packRootImg(tmprootfs,
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
            srcP = subprocess.Popen('tar -cf - --exclude TRANS.TBL .',
                        cwd=self.mountpoint /
                            osdistro.pathLayoutAttributes['packagesdir'],
                        shell=True, stdout=subprocess.PIPE)
            dstP = subprocess.Popen('tar xf -', cwd=repodir, shell=True,
                                    stdin=srcP.stdout)
            dstP.communicate()
        except Exception,msg:
            kl.error('Error during copy: %s', msg)
            return EKITADD_FAIL

        return 0
                
    def finalizeOSKit(self, kit):
        #populate the database with info
        query = "insert into kits (rname,rdesc,version,isOS,removeable,arch) values \
            ('%s','%s','%s',1,0,'%s')" % (kit['name'], kit['sum'], kit['ver'], kit['arch'])
        kl.debug('addOSKit query: %s', query)

        try:
            self.__db.execute(query)
        except Exception,msg:
            kl.debug('FAIL query: %s, message: %s', query, msg)
            return EKITADD_FAIL
        
        return 0

    def deleteKit(self):
        '''perform the delete operation on the kit specified '''

        try:
            assert(bool(self.kitname))
        except AssertionError,msg:
            sys.stderr.write('kitops: name for kit to delete not specified\n')
            return EKITDEL_FAIL

        kit = {} #data struct to hold delkit's properties
        kit['name'] = self.kitname

        query = "select kid,removeable,version from kits  where rname='%s' " %kit['name']
        self.__db.execute(query)
        rv = self.__db.fetchone()
        kl.debug('Delete kit DB record: %s', rv)
        if not rv:
            kl.error("Kit '%s' is not in the database", kit['name'])
            return EKITDEL_FAIL
        (kit['kid'], kit['removeable'], kit['ver']) = rv

        if not kit['removeable']:
            kl.error("Kit '%s' is not removable", kit['name'])
            return EKITDEL_FAIL

        # at this point kit is removable and in the DB
        query = "SELECT kits.kid from kits, repos_have_kits where kits.kid = \
                repos_have_kits.kid and kits.rname='%s'" %kit['name']
        self.__db.execute(query)
        rv = self.__db.fetchall()
        if rv:  #the kit is in use by some repo
            kl.error("Cannot delete kit '%s', it is used by a repo",
                     kit['name'])
            return EKITDEL_FAIL

        #the kit is NOT in use
        #1. remove the RPMS from /depot/kits/<kitname>/<kitver>
        rmP = subprocess.Popen('/bin/rm -rf %s' %
                               (self.kits_dir / kit['name'] / kit['ver']),
                               shell=True)

        #2. remove kit RPM
        rmP = subprocess.Popen('/bin/rpm --quiet -e --nodeps kit-%s' %
                               kit['name'], shell=True)
        rmP.wait()

        #3. remove component info from DB
        query = "DELETE from components where kid=%s" %kit['kid']
        try:
            self.__db.execute(query)
        except:
            self.stderr.write("kitops: delete operation failed to upgrade the DB for kit '%s'" %kit['name'])
            return EKITDEL_FAIL
        
        #4. remove kit DB info
        query = "DELETE from kits where kid=%s" %kit['kid']
        try:
            self.__db.execute(query)
        except:
            self.stderr.write("kitops: delete operation failed to upgrade the DB for kit '%s'" %kit['name'])
            return EKITDEL_FAIL
        
        #5. done
        return 0

    def listKit(self):
        '''if the kit was specified, lists component summary for it, else prints
         kit table summary'''

        if self.kitname:
            q = "select kid from kits where rname = '%s'" % self.kitname
            try:
                self.__db.execute(q)
                rv = self.__db.fetchone()
            except:
                sys.stderr.write("kitops: Error occurred accessing the DB during list operation")
                return EKITLST_FAIL

            if not rv:
                kl.error("Kit '%s' is not in DB", self.kitname)
                return EKITLST_FAIL
            kid = rv[0] #extract the kid of the specified kit
            #query = '''select k.rname Kit, c.cname Component, c.cdesc Description, c.OS 
            #        from kits k, components c where c.kid=k.kid and k.kid=%s''' %kid
            query = 'SELECT rname Kit, rdesc Description, version Version, ' + \
                    'arch Architecture, removeable Removable FROM kits ' + \
                    'WHERE kid=%s' % kid
        else:
            query = 'SELECT rname Kit, rdesc Description, version Version, ' + \
                    'arch Architecture, removeable Removable FROM kits'

        kl.debug('listKit query: %s', query)
        mysqlP = subprocess.Popen("mysql -u nobody -e '%s' %s" %
                                  (query, self.__db.dbname), shell=True)
        mysqlP.wait()

        return 0    #success

    def setKitname(self, kitname):
        self.kitname = kitname

    def setKitmedia(self, kitmedia):
        self.kitmedia = kitmedia

