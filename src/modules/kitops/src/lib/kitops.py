#!/usr/bin/python
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
import string
import urllib
import urlparse
import tempfile
import glob
import re
import path
from kusu.core.db import KusuDB
from kusu.boot.tool import BootMediaTool
from kusu.boot.distro import *
from kusu.kitops.package import PackageFactory

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
        self.__tmpfname = None
        self.__tmpmntdir = None
        self.__db = KusuDB()

        self.depot_prefix = path(kw.get('prefix', '/'))
        self.kits = self.depot_prefix / path('depot/kits/')

        try:
            self.__db.connect('kusudb','apache')
            #self.__db.connect('test')
        except Exception,msg:
            sys.stderr.write('kitops: Connection to the database failed with error message %s' %msg)
            sys.exit(EDB_FAIL)

    def setPrefix(self, prefix):
        """
        Provide a new depot_prefix.
        """

        self.depot_prefix = path(prefix)
        self.kits = self.depot_prefix / path('depot/kits/')

    def addKitPrepare(self):
        '''PreCondition:  add operation requested
           PostCondition: the kit media is mounted to self.mountpoint'''
        # 1. kit media was not specified - auto-detect
        if not self.kitmedia:
            lst = self.findMediaDevices()
            print "DEBUG: media device list = ",lst
            try:
                assert(lst)
            except AssertionError:
                sys.stderr.write('kitops: kit media neither specified nor found\n')
                return EKITLOC_FAIL

            for dev in lst:
                try:
                    self.mountMedia('/dev/%s' %dev)
                except EMOUNTFAIL,inst:
                    sys.stderr.write('kitops: failed mounting device /dev/%s\n' %dev)
                    self.__handleMountError(int(inst))
                else:
                    #mountpoint is defined - mount was successful
                    self.MediaDevice = '/dev/%s' %dev
                    return 0
            return EKITLOC_FAIL

        # 2. kit media was specified - determine what to do with it
        rv = urlparse.urlparse(self.kitmedia)

        if rv[0]:
            print "kitops: Network kit specified - retrieving..."
            (self.__tmpfname, headers) = urllib.urlretrieve(self.kitmedia)
            self.medialoc = os.path.abspath(self.__tmpfname)
        else :
            self.medialoc = os.path.abspath(self.kitmedia)

        #at this point, media can be either an iso file or a mountpoint dir
        if os.path.isfile(self.medialoc) and os.path.splitext(self.medialoc)[1].lower()=='.iso':
            print 'kitops: media iso file was provided: %s' %self.medialoc
            isISO = True
            try:
                self.mountMedia(self.medialoc, isISO)
            except EMOUNTFAIL,inst:
                self.__handleMountError(int(inst))
                return EKITLOC_FAIL
            #mountpoint is defined - we're done
            return 0
                
        elif os.path.isdir(self.medialoc) and os.path.ismount(self.medialoc):
            print 'kitops: media mountpoint was provided: %s' %self.medialoc
            self.mountpoint = self.medialoc

        else:
            #if neither of the above - error
            self.errorMessage('kitops: improper kit media location specification\n')
            return EKITLOC_FAIL

        #at this point we have the kit mounted to self.mountpoint
        return 0

    def addKit(self):
        '''perform the add operation on the kit specified 
           Precondition: kit is mounted to self.mountpoint'''

        #at this point we have the kit mounted to self.mountpoint
        try:
            assert(self.mountpoint and os.path.isdir(self.mountpoint) and os.path.ismount(self.mountpoint))
        except AssertionError,msg:
            sys.stderr.write('kitops: mountpoint sanity assertion failed:\n%s' %msg)
            return EKITLOC_FAIL

        #check if it's an OS kit
        if os.path.isdir('%s/isolinux' %self.mountpoint):
            rv = self.addOsKit()
            return rv

        #handle most common scenario
        if self.kitname == '':  #kit to install was NOT specified
            #create list of candidate kits to install
            dirlst = self.__getDirList(self.mountpoint)
            for i in range(0,len(dirlst)):
                if not glob.glob('%s/%s/kit-*.rpm' % (self.mountpoint, dirlst[i])):
                    del dirlst[i]
            if not dirlst:
                print 'kitops: bad media provided - no kits found'
                return EKIT_BAD

            if len(dirlst) == 1:
                self.kitname = dirlst[0]
            elif len(dirlst) > 1:
                #handleMetaKit - return the kit to work with (self.kitname must be set)
                rv = self.selectKit(self.mountpoint, dirlst)
                if not rv:
                    print 'kitops: bad media provided - no kits found'
                    return EKIT_BAD
                self.kitname = rv

        # at this point self.kitname must be defined
        try:
            assert(bool(self.kitname))
        except AssertionError, msg:
            sys.stderr.write("kitops: kitname still not defined - shouldn't happen\n%s" %msg)
            return EKITADD_FAIL

        kitRPMlst = glob.glob('%s/%s/kit-%s*.rpm' %(self.mountpoint,self.kitname,self.kitname))
        try:
            assert(len(kitRPMlst)==1)
        except AssertionError,msg:
            sys.stderr.write('kitops: number of kit RPMs under %s/%s must be exactly one\n%s' \
                %(self.mountpoint,self.kitname,msg))
            return EKITADD_FAIL

        kit = {} #the struct for kit info
        kit['rpmloc'] = path(kitRPMlst[0])    #absolute path to kit RPM

        #extract some RPMTAG info
        kit['inst'] = PackageFactory(str(kit['rpmloc']))
        kit['ver'] = kit['inst'].getVersion()
        kit['name'] = kit['inst'].getName()
        if kit['name'].startswith('kit-'):
            kit['name'] = kit['name'][len('kit-'):]
        kit['sum'] = kit['inst'].getSummary()
        print 'DEBUG: kitops: ', kit['name'],kit['ver'],kit['sum']

        #check if this kit is already installed - by name and version
        try:
            if self.checkKitInstalled(kit['name'], kit['ver']):
                print "kitops: Kit '%s' version '%s' is already installed." %(kit['name'],kit['ver'])
                return EKITADD_FAIL
        except Exception,msg:
            sys.stderr.write('kitops: DB check on the kit %s failed with msg=%s\n' % (kit['name'],msg))
            return EKITADD_FAIL

        # 1. copy the RPMS
        repodir = self.kits / kit['name'] / kit['ver']
        if not repodir.exists():
            repodir.makedirs()
        cmd = 'cd %s/%s; tar cf - --exclude %s *.rpm | (cd %s; tar xf -)' % \
              (self.mountpoint, self.kitname, kit['rpmloc'].basename(), repodir)
        print 'DEBUG: kitops: cmd = %s' %cmd
        os.system(cmd)

        # 2. populate the kit DB table with info
        query = "insert into kits (rname,rdesc,version) values \
            ('%s','%s','%s')" % (kit['name'], kit['sum'], kit['ver'])

        try:
            rv = self.__db.execute(query)
            print "kitops: DEBUG: kit table update, rv=",rv
        except Exception,msg:
            print 'kitops: Database query=%s failed with msg=%s' %(query,msg)
            return EKITADD_FAIL

        #extract the kit id to associate with components
        query = "select kid from kits where rname='%s' and version='%s'" %(kit['name'],kit['ver'])
        self.__db.execute(query)
        kit['kid'], = self.__db.fetchone()
        print 'addKIT: DEBUG - kid = ',kit['kid']

        # 3. install the kit RPM
        try:
            os.system('rpm -ihv %s' %kit['rpmloc'])
        except Exception, msg:
            sys.stderr.write('kitops: kit RPM installation failed with message %s' %msg)
            #possible to reverse the DB transaction at this point and gracefully exit
            return EKITADD_FAIL

        #at this point kit RPM must've populated the components table - check
        # 4. check/populate component table
        complst = glob.glob('%s/%s/component-*.rpm' %(self.mountpoint,kit['name']))
        for comploc in complst:
            comp = {}
            comp['inst'] = PackageFactory(comploc)
            comp['name'] = comp['inst'].getName()
            if comp['name'].startswith('component-'):
                comp['name'] = comp['name'][len('component-'):]

            try:
                assert(bool(comp['name']))
            except:
                sys.stderr.write('kitops: encountered corrupt name for component from %s' \
                        %os.path.basename(comploc))
                #handleAddFailure - reverse DB Transaction, remove RPMS?
                return EKITADD_FAIL

            comp['ver'] = comp['inst'].getVersion()
            comp['sum'] = comp['inst'].getSummary()
            query = "select cid,kid from components where cname = '%s'" % comp['name']
            self.__db.execute(query)
            comp['dbcidlst'] = self.__db.fetchall() #len>1 only if multi-distro explicit support

            if not comp['dbcidlst']: #this component was not inserted in kit RPM's %post
                #generate an entry for this component
                query = "insert into components (kid,cname,cdesc) values (%s,'%s','%s')"\
                            %(kit['kid'], comp['name'], comp['sum'])
                self.__db.execute(query)
            else:
                for dbcid,dbkid in comp['dbcidlst']:
                    if dbkid>0 and dbkid != kit['kid']:
                        print "kitops: Warning, updating kit ID for component '%s', cid=%s" \
                                %(comp['name'], dbcid)
                    query = "UPDATE components SET kid=%s where cid=%s" %(kit['kid'],dbcid)
                    self.__db.execute(query)
        # 5. done

        return 0

    def findMediaDevices(self):
        '''Check for IDE/ATAPI, SCSI CD-ROM/DVD/CDRW devices, including USB storage
         devices.  Return the list of media devices to try'''
        MediaDevLst = []
        devdirlst = []

        devdirlst = os.listdir("/sys/block")
        devdirlst.sort()

        for dev in devdirlst:
            if re.match("^hd?", dev):
                devinfo = open("/sys/block/%s/removable" % dev, 'r')
                removable = devinfo.readline().strip()
                devinfo.close()
                if int(removable) == 1:
                    MediaDevLst.append(dev)

            elif re.match("^sr?", dev):
                devinfo = open("/sys/block/%s/removable" % dev, 'r')
                removable = devinfo.readline().strip()
                devinfo.close()
                if int(removable) == 1:
                    scsidev = "scd%s" % dev[2:]
                    MediaDevLst.append(scsidev)
        return MediaDevLst

    def checkKitInstalled(self,kitname,kitver):
        '''Returns true if specified kit is already in the DB, false otherwise'''
        query = "select * from kits where rname='%s' and version='%s'" %(kitname,kitver)
        print 'checkKitInstalled: query=',query
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
            dirlst = self.__getDirList(mountpoint)
            for i in range(0, len(dirlst)):
                if not glob.glob('%s/%s/kit-*.rpm' % (mountpoint, dirlst[i])):
                    del dirlst[i]
            if not dirlst:
                print 'kitops: bad media provided - no kits found'
                return EKIT_BAD
        #TO BE CONTINUED
        
    def mountMedia(self, media, isISO=False):
        ''' mount the specified media to a temporary dir
            PostCondition: self.__tmpmntdir & self.mountpoint are set & equal if successful'''
        self.__tmpmntdir = tempfile.mkdtemp()

        if isISO:
            cmd = "mount -o loop %s %s 2> /dev/null" % (media, self.__tmpmntdir)
        else:
            cmd = "mount %s %s 2> /dev/null" % (media, self.__tmpmntdir)
        rv = os.system(cmd)
        if rv != 0:
            os.rmdir(self.__tmpmntdir)
            self.__tmpmntdir = None
            raise EMOUNTFAIL(rv)

        self.mountpoint = self.__tmpmntdir

    def unmountMedia(self):
        '''PostCondition: self.mountpoint is unmounted, self.__tmpmntdir is removed,
            and both are set to None ''' 
        if self.mountpoint:
            os.system('umount -l %s 2> /dev/null' %self.mountpoint)
            self.mountpoint = None
        if self.__tmpmntdir:
            os.system('rm -rf %s 2> /dev/null' %self.__tmpmntdir)
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
                print "kitops: mount failed with this error: %s" % errdict[key]

    def addOsKit(self):
        '''handle the special case when the kit is an OS
           Precondition: self.mountpoint is defined, media successfully mounted'''
        print 'kitops: adding OS KIT'

        kit = {} #a struct to hold the kit info for the distro
        #instantiate a distro via the factory
        osdistro = DistroFactory(self.mountpoint)           #distro instance
        kit['ver']    = osdistro.getVersion()               #os kit version in the db
        kit['arch']   = osdistro.getArch()                  #os kit arch in the db
        kit['name'] = '%s-%s-%s' %(osdistro.ostype, kit['ver'], kit['arch'])
        kit['sum'] = 'OS kit for %s %s %s' %(osdistro.ostype, kit['name'], kit['ver'], kit['arch'])

        query = "SELECT * from kits where rname = '%s'" %kit['name']
        print "DEBUG: addOsKit: query = ", query
        try:
            self.__db.execute(query)
            rv = self.__db.fetchone()
        except Exception,msg:
            print 'kitops: Database query=%s failed with msg=%s' %(query,msg)
            return EKITADD_FAIL

        if rv != None:
            print 'kitops: The OS kit %s is already installed' % kit['name']
            return EKITADD_FAIL

        #copy kernel & initrd to pxedir
        pxedir = '/tftpboot/pxelinux/'
        if not os.path.isdir(pxedir):
            os.makedirs(pxedir)

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
        bmt.packRootImg(tmprootfs, pxedir+'/initrd-%s.img'  %kit['name'])
        #copy kernel to tftpboot & rename
        bmt.copyKernel(self.mountpoint, pxedir+'/kernel-%s' %kit['name'],True)

        #copy the RPMS to repo dir
        print "kitops: copying the RPMs - this may take a LOOONG time..."
        repodir = '/depot/kits/%s/%s/' %(kit['name'],kit['ver'])
        if not os.path.exists(repodir):
            os.makedirs(repodir)


        disk = 0
        while 1:    #loop to go through all the media disks...
            disk += 1
            print "kitops: Copying packages from Disk %d ..." %disk

            cmd = 'cd %s/%s; tar -cf - --exclude TRANS.TBL . | (cd %s; tar xf -)' \
                % (self.mountpoint, osdistro.pathLayoutAttributes['packagesdir'], repodir)
            print "DEBUG: rpm copy cmd = ", cmd
            try:
                os.system(cmd)
            except Exception,msg:
                print "kitops: OS system command failed executing '%s' with message = %s" % (cmd,msg)
                return EKITADD_FAIL
            res = ''
            while not (res == 'y' or res == 'N'):
                res = raw_input('Any more disks for this OS kit? [y/N] ')
            if res == 'N':
                break
            print "Please insert next disk if installing from phys. media NOW"
            res = raw_input('(URI for next ISO | blank if phys. media | N to finish): ')
            res = string.strip(res)
            if res == 'N':
                break

            #unmount current, prepare for next
            self.unmountMedia()
            self.kitmedia = res
            print "DEBUG: kitmedia specified by user=%s=" %self.kitmedia
            self.addKitPrepare()
        # end while
                

        #populate the database with info
        query = "insert into kits (rname,rdesc,version,upgradeable,removable,arch) values \
            ('%s','%s','%s',0,0,'%s')" % (kit['name'], kit['sum'], kit['ver'], kit['arch'])
        print "DEBUG: addOsKit: query = ", query

        try:
            self.__db.execute(query)
        except Exception,msg:
            print 'kitops: Database query=%s failed with msg=%s' %(query,msg)
            return EKITADD_FAIL

        
        return 0

    def __getDirList(self, topdir):
        '''returns a list of directories under a specified topdir, excluding . & ..'''
        return [d for d in os.listdir(topdir) if os.path.isdir(os.path.join(topdir, d))]

    def __getFileList(self, topdir):
        return [f for f in os.listdir(topdir) if os.path.isfile(os.path.join(topdir, d))]

    def deleteKit(self):
        '''perform the delete operation on the kit specified '''

        try:
            assert(bool(self.kitname))
        except AssertionError,msg:
            sys.stderr.write('kitops: name for kit to delete not specified\n')
            return EKITDEL_FAIL

        kit = {} #data struct to hold delkit's properties
        kit['name'] = self.kitname

        query = "select kid,removable,version from kits  where rname='%s' " %kit['name']
        self.__db.execute(query)
        rv = self.__db.fetchone()
        print 'DEBUG: del kit DB record: ', rv
        if not rv:
            print "kitops: kit '%s' is not in the database" %kit['name']
            return EKITDEL_FAIL
        (kit['kid'], kit['removable'], kit['ver']) = rv

        if not kit['removable']:
            print "kitops: kit '%s' is not removable" %kit['name']
            return EKITDEL_FAIL

        # at this point kit is removable and in the DB
        query = "SELECT kits.kid from kits, repos_have_kits where kits.kid = \
                repos_have_kits.kid and kits.rname='%s'" %kit['name']
        self.__db.execute(query)
        rv = self.__db.fetchall()
        if rv:  #the kit is in use by some repo
            print "kitops: kit '%s' is in use by a repo - can't delete" %kit['name']
            return EKITDEL_FAIL

        #the kit is NOT in use
        #1. remove the RPMS from /depot/kits/<kitname>/<kitver>
        cmd = "/bin/rm -rf /depot/kits/%s/%s/ " % (kit['name'],kit['ver'])
        os.system(cmd)

        #2. remove kit RPM
        os.system('/bin/rpm -e --nodeps kit-%s' %kit['name'])

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
                print "kitops: specified kit '%s' is not in the DB" %self.kitname
                return EKITLST_FAIL
            kid = rv[0] #extract the kid of the specified kit
            query = '''select k.rname Kit, c.cname Component, c.cdesc Description, c.OS 
                    from kits k, components c where c.kid=k.kid and k.kid=%s''' %kid
        else:
#            query = '''select rname Kit,rdesc Description,Version, arch Architecture,
#                    Upgradeable,Removeable from kits'''
            query = 'SELECT rname Kit, rdesc Description, version Version, ' +\
                    'arch Architecture, removable Removable FROM kits'

        #print "DEBUG: listKit, query = %s" %query
        os.system("mysql -e '%s' %s" %(query,self.__db.dbname))

        return 0    #success

    def setKitname(self, kitname):
        self.kitname = kitname

    def setKitmedia(self, kitmedia):
        self.kitmedia = kitmedia

