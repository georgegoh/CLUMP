#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright (C) 2010 Platform Computing Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 2 of the GNU General Public License as published by the
# Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

import os
import sys

sys.path.append('/opt/kusu/bootstrap/lib/python')
sys.path.append('/opt/kusu/bootstrap/lib/python/pysrc')
sys.path.append('/opt/kusu/bootstrap/primitive/lib/python2.4/site-packages/')

from kusu.kitops.kitops import KitOps
from path import path
from kusu.util.errors import *
from primitive.support import osfamily
from primitive.support.osfamily_dict import osfamily_dict
import kusu.core.database as db
import md5
import message
from primitive.system.software import probe as softprobe

try:
    import subprocess
except:
    from popen5 import subprocess

class InstallOSKitReceiver:
    """
    This class prompts for, and installs the OS kit
    """
    def __init__(self, kusu_db ):

        self._db = kusu_db
        self.os_kit = None
        self.kitops = KitOps(installer=False)
        self.kitops.setDB(self._db)
        self.kitops.setPrefix(path('/'))
        self.kitops.setTmpPrefix(os.environ.get('KUSU_TMP', ''))

        name, ver, arch = softprobe.OS()
        ver = ver.split(".")[0] #keep only major number of version

        self.bootstrap_os_version = ver
        self.bootstrap_os_arch =  arch
        self.bootstrap_os_type = name.lower() #prevents stuff like "CentOS == centos"

    def updateNodeGroupImages(self, initrd, kernel, longname):
        """
            Update the node group initrd and kernel images
        """
        ngs = self._db.NodeGroups.select()
        ngids = [row.ngid for row in self._db.NGHasComp.select()]

        for ng in ngs:
            if ng.ngid in ngids:
                ng.ngname = ng.ngname + '-' +  longname

                if ng.installtype == 'package':
                    ng.initrd = initrd
                    ng.kernel = kernel
                ng.save()
                ng.flush()

    def install_os_kit(self, kit_media):
        try:
            self.kits, cd = self.get_kits_from_media(kit_media)
        except Exception, msg:
            return False, "\nFailed to mount kit media:  %s" % msg

        st, msg = self._check_for_duplicate_os_kit(self.kits)
        if st:
            self.kitops.unmountMedia()
            return False, msg

        message.display('\nVerifying that OS is the right distro, arch, version')
        verified, err_list = self.verifyDistroVersionAndArch(self.kits)
        if not verified:
            self.kitops.unmountMedia()
            return False, 'Cannot add OS kit ' + \
                          'because the media does not match the ' + \
                          'following criteria:\n\t' + '\n\t'.join(err_list)

        #try:
        self._addOSKit(kit_media, cd)
        #except Exception, msg:
            #self.kitops.unmountMedia()
            #return False, "\nFailed to add OS Kit:  %s" % msg

        return True, ''

    def eject(self, path):
        """Eject a CD/DVD drive. Give me a path string."""
        p = subprocess.Popen('eject %s' % path,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        return p.communicate()


    def verifyDistroVersionAndArch(self, distro):
        """
        Verify that a distro matches the version and architecture
        """
        verified = False
        err_list = []
        try:
            ostype = distro.ostype
        except AttributeError:
            return False, ["The media does not contain the OS kit"]

        osTypeMatch = False
        versionMatch = False
        archMatch = False

        if ostype == self.bootstrap_os_type:
            osTypeMatch = True
        else:
             err_list.append('Expected OS:%s Provided OS:%s' % (self.bootstrap_os_type.ljust(10),
                                                   ostype or 'Unknown'))

        distro_ver = distro.getVersion() or 'Unknown'
        if distro_ver != 'Unknown':
            distro_ver = distro_ver.split('.')[0]

        if self.bootstrap_os_version == distro_ver:
            versionMatch = True
        else:
            err_list.append('Expected Major Version:%s Provided Major Version:%s' % (self.bootstrap_os_version.ljust(5),
                                                             distro_ver))

        if self.bootstrap_os_arch == distro.getArch():
            archMatch = True
        else:
            if distro.getArch() != 'noarch':
                err_list.append('Expected Arch:%s\tProvided Arch:%s' % (self.bootstrap_os_arch,
                                                           distro.getArch() or 'Unknown'))

        return osTypeMatch and versionMatch and archMatch, err_list

    def computeChecksum(self, mountpoint):
        """ Do a recursive directory listing of the cdrom. use this concatenated
            listing to perform an md5 checksum as fingerprint for CD
        """
        rpms = []
        for root, dirs, files in os.walk(mountpoint):
            rpms.extend(files)

        sortedRPMs = sorted(rpms)
        m = md5.new()
        m.update(str(sortedRPMs)) #alternatively the list can be flattened into a string: "".join(sortedRPMS)

        return m.hexdigest()

    def closeTray(self, path):
        """Close a CD/DVD drive. Give me a path string."""
        p = subprocess.Popen('eject -t %s' % path,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        return p.communicate()

    def _check_kit_distro_and_arch(self, distro_name, distro_arch, distro_ver):
        distro_family = distro_name # Assume that the family name is passed
        if not distro_ver:
            distro_ver = self.bootstrap_os_version # For base kit don't need to check version

        for key, values in osfamily_dict.items():
            if self.bootstrap_os_type in values:
                self.bootstrap_family = key

            if distro_name in values:
                distro_family = key

        if self.bootstrap_family == distro_family:
            distro_name = self.bootstrap_os_type

        if distro_name != self.bootstrap_os_type or \
            distro_ver != self.bootstrap_os_version or \
            distro_arch != self.bootstrap_os_arch:
            message.failure('Wrong OS disk. Inserted OS disk does ' \
                                 'not match selected operating system: %s. ' \
                                 'Please insert the correct disc.\n\n' \
                                 'Expected name: %s ver: %s arch: %s\n' \
                                 'Given name: %s ver: %s arch: %s' % \
                                  (self.bootstrap_os_type,
                                   self.bootstrap_os_type,
                                   self.bootstrap_os_version,
                                   self.bootstrap_os_arch,
                                   distro_name, distro_ver, distro_arch), 0)

            return False

        return True

    def _addOSKit(self, kit_media, cdrom):
        try:
            kit = self.kitops.prepareOSKit(self.kits)
        except (IOError,FileAlreadyExists,CopyError), e :
            self.kitops.unmountMedia()
            message.display('Error reading OS disk. Please ensure that the ' + \
                                     'OS disk is not corrupted or that' + \
                                     'the CD/DVD drive is not faulty.')
            return

        except UnrecognizedKitMediaError, e:
            self.kitops.unmountMedia()
            message.failure('Media Error : %s' % e.args[0], 0)
            return

        disks_cksum = []

        # Compute the checksum of the very first Kit CD
        message.display('\nStarting checksum... this might take a while...')

        #Checksum first disk
        cur_disk_cksum  = self.computeChecksum(self.kitops.mountpoint)

        #store checksum
        disks_cksum.append(cur_disk_cksum)


        message.display('\nCopying OS kit (%s). This might take a while...' % kit['name'])
        self.os_kit = kit
        kitdir = self.kitops.copyOSKitMedia(kit)

        if sum([f.size for f in kitdir.walkfiles()]) <= 900000000: # cd provided
            while 1:
                answer = message.input('\nAny more disks for this OS kit? (Y/[N]):').strip()
                # unmount and eject.
                self.kitops.unmountMedia()
                if cdrom:
                    out, err = self.eject(cdrom)
                    if err:
                        message.failure('CD/DVD Drive Eject Error: %s' % err, 0)

                if answer.lower() in ['no', 'n', '']:
                    break

                if answer.lower() in ['yes', 'y']:
                    answer = message.input("\nURI for next ISO | Blank if physical media | 'N' to finish").strip()
                    if not answer:
                        kits, cd = self.get_kits_from_media('cdrom')
                    elif answer.lower() in ['no', 'n']:
                        break
                    else:
                        kits, cd = self.get_kits_from_media('iso')

                message.display('Copying OS kit (%s). This might take a while...' % kit['name'])
                # compute the next checksum
                cur_disk_cksum = self.computeChecksum(self.kitops.mountpoint)

                # If the checksum has already existed (duplicate CD), then prompt user to insert the next CD
                # for the current OS kit
                if cur_disk_cksum in disks_cksum:
                    message.display('\nDuplicate Media Inserted. This media has already been copied.')
                    continue

                disks_cksum.append(cur_disk_cksum)

                dist = self.kitops.getOSDist()

                if not self._check_kit_distro_and_arch(dist.ostype, dist.getArch(),  dist.getVersion()):
                    self.kitops.unmountMedia()
                    continue

                self.kitops.copyOSKitMedia(kit)

        self.updateNodeGroupImages(kit['initrd'], kit['kernel'], kit['longname'])
        self.kitops.finalizeOSKit(kit)

    def _check_for_duplicate_os_kit(self, kit):
        #LOGME: print ('Getting OS distribution')
        ostype = None
        try:
            ostype = kit.ostype
        except AttributeError:
            return False, ''

        if ostype is not None:
            if self.os_kit:
                return True, '\nCannot add more than one OS kit ' + \
                               'during installation. ' + \
                               '\nYou can add additional OS kit using kusu-kitops later.'

        return False, ''

    def _check_for_duplicate_base_kit(self, kit):
        try:
            kit.ostype # os kit
            return False, ''
        except AttributeError:
            pass

        if kit[1]['name'] != 'base':
            return False, ''

        base = [kit.rname for kit in self.kitops.listKit() if kit.rname == 'base']
        if base:
            return True, '\nCannot add more than one base kit' +\
                          'during installation.' +\
                          '\nYou can add additional base kits using kusu-kitops later.'
        return False, ''

    def install_extra_kits(self, kits):
        retVal = False
        msg = ''
        for kit in kits:
            st, msg = self._check_for_duplicate_os_kit(kit)
            if st:
                message.warning("\n%s" % msg)
                continue

            st, msg = self._check_for_duplicate_base_kit(kit)
            if st:
                 message.warning("\n%s" %msg)
                 continue

            kitname = kit[1]['name']
            try:
                message.display( "\nAdding Kit: '%s'..." % kitname)
                self.kitops.addKit(kit, api=str(kit[4]))
                retVal = True
            except (KitAlreadyInstalledError, InstallKitRPMError,
                        ComponentAlreadyInstalledError,UnsupportedKitAPIError), e:
                msg += "\nInstallation of the kit '%s' + failed: %s" % (kitname, e)
                message.failure(msg, 0)
            except AssertionError:
                msg += "\nThe inserted disk could not be identified."
                message.failure(msg,0)

        self.kitops.unmountMedia()
        return retVal, msg

    def get_kits_from_media(self, kit_media, base=''):
        """Install the other kits from cd."""

        kits = []
        if kit_media == 'cdrom':
            import primitive.system.hardware.probe
            cdrom_dict = primitive.system.hardware.probe.getCDROM()
            cdrom_list = ['/dev/' + cd for cd in sorted(cdrom_dict.keys())]

            for cd in cdrom_list:
                self.kitops.setKitMedia(cd)
                try:
                    kits = self.kitops.addKitPrepare()
                except Exception:
                    continue
                if base == 'base':
                    if not self._has_base_kit(kits):
                        continue
                if kits:
                    return kits, cd
        elif kit_media == 'iso':
            kit_iso = self.prompt_for_kit()
            self.kitops.setKitMedia(kit_iso)
            try:
                kits = self.kitops.addKitPrepare()
                if base == 'base':
                    if not self._has_base_kit(kits):
                        self.kitops.unmountMedia()
                        msg = "\nCould not find the correct base kit in the media." +\
                               "\nPlease make sure that the base kit is for the same distro and arch"
                        return [], msg
            except Exception, e:
                msg = "\nPlease provide a valid iso file: %s" % e
                return [], msg

        return kits, ''

    def add_kits(self, kit_media):
        kits = []
        try:
            kits, cd = self.get_kits_from_media(kit_media)
        except Exception, msg:
            return False, "\nFailed to mount kit media:  %s" % msg

        kits = self.selectKits(kits)
        if kits:
            # we cannot identify the distro -- treat as ordinary kit
            status, msg = self.install_extra_kits(kits)
        if not status:
            return False, msg

        return True, msg

    def delete_kits(self, kits=[]):
        # We cannot delete the base and the os kits.
        if not kits:
            kits = self._get_allowed_kits()
            kits = self.selectKits(kits, 'delete')

        for kit in kits:
            try:
                message.display("\nDeleting kit %s" %kit.rname)
                self.kitops.deleteKit(del_name=kit.rname, del_version=kit.version, del_arch=kit.arch)
            except DeleteKitsError, msg:
                return False, msg
            message.display("\nKit %s deleted successfully" %kit.rname)

        return True, ''

    def find_incompatible_kits(self):
        """ Finds and returns the kits that are not compatible with the OS kit."""

        incompatible = []
        kit_lits = self.kitops.listKit()
        os = [kit for kit in kit_lits if kit.isOS]
        if os:
           self.os_kit = os[0]
        for kit in self.kitops.listKit():
            components = self.kitops.getKitComponents(kit.kid, self.os_kit.os)
            if not components:
                incompatible.append(kit)
        return incompatible

    def _get_allowed_kits(self):
        kits = []
        for kit in self.kitops.listKit():
            if kit.isOS:
                continue
            if kit.rname == 'base':
                continue
            else:
                kits.append(kit)

        return kits

    def prompt_for_kit(self):
        kit_iso = ""
        while not os.path.exists(kit_iso):
            kit_iso = message.input("Please provide path to ISO image or mount point: ")
            if not os.path.exists(kit_iso):
                message.failure("The specified path or file does not exist.",0)

        return kit_iso

    def installKitsOnBootMedia(self, kit_media):
        """Install the kits on boot media (most likely base kit only)."""
        kits = []
        kits, msg = self.get_kits_from_media(kit_media, 'base')
        if not kits:
            return False, msg

        retVal, msg = self.install_extra_kits(kits)
        if retVal:
            msg = "\nBase kit Installation Succeded."

        self.installedBootMediaKits = retVal
        return retVal, msg

    def _has_base_kit(self, kits):
        base_kit = False
        for kit in kits:
            if kit[1]['name'] == 'base':
                rpmtool =  kit[-2]
                kit_os = kit[2][0]['os'][0]['name']
                kit_arch = rpmtool.getArch()
                if self._check_kit_distro_and_arch(kit_os, kit_arch, ''):
                    base_kit = True
                    break
                else:
                    base_kit = False
                    break

        return base_kit

    def selectKits(self, kits, policy='add'):
        """
        From a list of kits select kits to add/delete.
        """
        if len(kits) <= 1:
            return kits

        selected_kits = []
        while 1:
            for num_kits in enumerate(kits):
                if policy == 'add':
                    message.display('\n[%d]: %s-%s-%s' % (num_kits[0], num_kits[1][1]['name'],
                                      num_kits[1][1]['version'],
                                      num_kits[1][1]['arch']))
                else:
                    message.display('\n[%d]: %s-%s-%s' % (num_kits[0], num_kits[1].rname,
                                       num_kits[1].version, num_kits[1].arch))

            res = message.input("\nProvide a comma separated list of kits " +
                   "to %s, 'all' to %s all the kits " % (policy, policy) +
                   "or ENTER to %s none:" % policy).strip()
            res = [x.strip() for x in res.split(',')]
            if res == ['']:
                message.warning('No kits selected', 0)
                return selected_kits

            if res == ['all']:
                return kits

            for x in res:
                try:
                    kit = kits[int(x)]
                except ValueError, IndexError:
                    message.warning("Wrong input '%s' provided. Ignoring..." % x, 0)
                    continue
                selected_kits.append(kit)
            return selected_kits
        return selected_kits

if __name__ == "__main__":
    osk = InstallOSKitReceiver()
    osk.installKitsOnBootMedia()
