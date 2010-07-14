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

        self.kitops = KitOps(installer=True)
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
        if kit_media == 'cdrom':
            import primitive.system.hardware.probe
            cdrom_dict = primitive.system.hardware.probe.getCDROM()
            cdrom_list = ['/dev/' + cd for cd in sorted(cdrom_dict.keys())]

            #print "Media device list: %s" % cdrom_list
            #print cdrom_dict
            boot_cd = ''
            for cd in cdrom_list:
                try:
                    self.kitops.setKitMedia(cd)
                    self.kits = self.kitops.addKitPrepare()

                    ostype = self.kits.ostype
                    if ostype is not None:
                        kit_list = self.kitops.listKit()
                        os = [kit.rname for kit in kit_list if kit.isOS]

                        if os:
                            return False, 'Cannot add more than one OS kit ' + \
                                          'during installation. ' + \
                                          'You can add additional OS kit using kusu-kitops later.'

                        message.display('\nVerifying that OS is the right distro, arch, version')
                        verified, err_list = self.verifyDistroVersionAndArch(self.kits)
                        if not verified:
                            return False, 'Cannot add OS kit ' + \
                                          'because the media does not match the ' + \
                                          'following criteria:\n\t' + '\n\t'.join(err_list)

                        try:
                            self.addOSKit(self.kitops, self.kits, cd)
                        except Exception, msg:
                            return False, "\nFailed to add OS Kit:  %s" % msg

                except Exception, msg:
                    return False,  "\nFailed to mount kit media: %s" % msg
                return True, ""
        elif kit_media == 'iso':
            kit_iso = self.prompt_for_kit()
            self.kitops.setKitMedia(kit_iso)
            kits = self.kitops.addKitPrepare()

            try:
                ostype = kits.ostype
                if ostype is not None:
                    kit_list = self.kitops.listKit()
                    os = [kit.rname for kit in kit_list if kit.isOS]

                    if os:
                        return False, 'Cannot add more than one OS kit ' + \
                                      'during installation. ' + \
                                      'You can add additional OS kit using kusu-kitops later.'

                    message.display('\nVerifying that OS is the right distro, arch, version')
                    verified, err_list = self.verifyDistroVersionAndArch(kits)
                    if not verified:
                        return False, 'Cannot add OS kit ' + \
                                      'because the .iso does not match the ' + \
                                      'following criteria:\n\t' + '\n\t'.join(err_list)


                kit = self.kitops.prepareOSKit(kits)
            except Exception, msg:
                return False, msg

            res = ''
            while 1:
                prepare_success = True
                if res:
                    self.kitops.setKitMedia(res)
                    try:
                        self.kitops.addKitPrepare()
                    except UnrecognizedKitMediaError, e:
                        msg = '\nFailed to add kit media: %s: %s' \
                                     % (res, e.args[0])
                        return False, msg

                if prepare_success:
                    try:
                        message.display('\nCopying OS kit (%s). This might take a while...' % kit['name'])

                        self.kitops.copyOSKitMedia(kit)
                    except CopyOSMediaError, e:
                        msg = '\nFailed to add OS kit: %s' % e.args[0]
                        return False, msg

                # We need to clear the kit media now that we're done with it
                self.kitops.setKitMedia('')

                answer = 'FAKE_ANSWER'
                while answer.strip().lower() not in ['no', 'yes', 'y', 'n', '']:
                    answer = message.input("Any more disks for this OS kit? (Y/[N]):")

                if answer.strip().lower() in ['no','n', '']:
                    break

                if answer.lower() in ['y', 'yes']:
                    message.display("\nPlease insert next disk if installing from phys. media NOW")
                    if not prepare_success:
                        message.display("\nCopying from the media you specified was not " + \
                              "successful. Try again...")
                    message.display('(\nURI for next ISO | blank if phys. media | N to finish):')
                    res = sys.stdin.readline().strip()
                    if res.lower() == 'n': break
                    elif not res: res = self.determineKitMedia()

            self.updateNodeGroupImages(kit['initrd'], kit['kernel'], kit['longname'])
            self.kitops.finalizeOSKit(kit)
            return True, ''

    def determineKitMedia(self):
        media_choices = self.autoDetectMedia()
        #found_kits = sorted(media_choices.keys())

        if len(media_choices) == 1:
            return media_choices.keys()[0]
        else:
            return self.selectKitMedia(media_choices)

    def autoDetectMedia(self):
        """
        Attemp to find kit media.
        """

        import primitive.system.hardware.probe
        cdrom_dict = primitive.system.hardware.probe.getCDROM()
        cdrom_list = ['/dev/' + cd for cd in sorted(cdrom_dict.keys())]

        available_kits = {}
        for cd in cdrom_list:
            try:
                self.kitops.mountMedia(cd)
                available_kits[cd] = self.kitops.getAvailableKits()
                self.kitops.unmountMedia()
            except CannotMountKitMediaError:
                pass

        if available_kits:
            return available_kits

    def selectKitMedia(self, choices):
        """
        Present a list of kits for the user to select from.
        """

        choice_list = []
        while 1:
            for num_media in enumerate(sorted(choices)):
                choice_list.append(num_media[1])
                message.display('[%d] (%s) Kits:' % (num_media[0], num_media[1]))

                for kit in choices[num_media[1]]:
                    message.display('\t%s-%s-%s' % (kit[1]['name'], kit[1]['version'],
                                             kit[1]['arch']))

            message.display('Select media to add from or ENTER to quit:')
            res = sys.stdin.readline().strip()
            if res == '':
                self.kitops.unmountMedia()
                sys.exit(0)

            try:
                return choices[choice_list[int(res)]]
            except ValueError, IndexError:
                pass

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
        ostype = distro.ostype

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


    def addOSKit(self, kitops, osdistro, cdrom):
        try:
            kit = kitops.prepareOSKit(osdistro)
        except (IOError,FileAlreadyExists,CopyError), e :
            message.display('Error reading OS disk. Please ensure that the ' + \
                                     'OS disk is not corrupted or that' + \
                                     'the CD/DVD drive is not faulty.')
            self.eject(cdrom)
            return

        except UnrecognizedKitMediaError, e:
            message.failure('Media Error : %s' % e.args[0], 0)
            self.eject(cdrom)
            return

        kit_name = kit['name']
        if kit_name in osfamily.getOSNames('rhelfamily') and \
                self.bootstrap_os_type in osfamily.getOSNames('rhelfamily'):
            kit_name = self.bootstrap_os_type

        if kit_name != self.bootstrap_os_type or \
            kit['ver'] != self.bootstrap_os_version or \
            kit['arch'] != self.bootstrap_os_arch:
            out, err = eject(cdrom)
            message.failure('Wrong OS disk. Inserted OS disk does ' \
                                     'not match selected operating system: %s. ' \
                                     'Please insert the correct disc.\n\n' \
                                     'Expected name: %s ver: %s arch: %s\n' \
                                     'Given name: %s ver: %s arch: %s' % \
                                       (self.bootstrap_os_type,
                                       self.bootstrap_os_type,
                                       self.bootstrap_os_version,
                                       self.bootstrap_os_arch,
                                       kit_name, kit['ver'], kit['arch']), 0)

            return

        disks_cksum = []

        # Compute the checksum of the very first Kit CD
        message.display('\nStarting checksum. This might take a while...')

        #Checksum first disk
        cur_disk_cksum  = self.computeChecksum(kitops.mountpoint)

        #store checksum
        disks_cksum.append(cur_disk_cksum)

        message.display('\nCopying OS kit (%s). This might take a while...' % kit['name'])
        kitdir = self.kitops.copyOSKitMedia(kit)

        if sum([f.size for f in kitdir.walkfiles()]) <= 700000000: # cd provided
            while message.display('Any more disks for this OS kit? (Y/[N]):'):
                # unmount and eject.
                out, err = self.eject(cdrom)
                if err:
                    message.failure('CD/DVD Drive Eject Error: %s' % err, 0)
                message.input('Please insert the next disk. Press enter when ready...')
                self.closeTray(cdrom)
                message.display('Copying OS kit (%s). This might take a while...' % kit['name'])

                self.kitops.setKitMedia(cdrom)
                self.kitops.addKitPrepare()

                # compute the next checksum
                cur_disk_cksum = self.computeChecksum(self.kitops.mountpoint)

                # If the checksum has already existed (duplicate CD), then prompt user to insert the next CD
                # for the current OS kit
                if cur_disk_cksum in disks_cksum:
                    message.input('Duplicate CD Inserted. This CD has already been copied. Please press ENTER to proceed with the installation for this OS kit')

                disks_cksum.append(cur_disk_cksum)

                dist = self.kitops.getOSDist()

                kit_name = dist.ostype
                if kit_name in osfamily.getOSNames('rhelfamily') and self.bootstrap_os_type in osfamily.getOSNames('rhelfamily'):
                    kit_name = self.bootstrap_os_type

                if not dist.ostype or not dist.getVersion() or not dist.getArch() or \
                    kit_name != self.bootstrap_os_type or \
                    dist.getVersion() != self.bootstrap_os_version or \
                    dist.getArch() != self.bootstrap_os_version:
                    print ('Wrong OS Disk. Disk does not match selected OS.')
                    continue

                self.kitops.copyOSKitMedia(kit)

        self.updateNodeGroupImages(kit['initrd'], kit['kernel'], kit['longname'])
        self.kitops.finalizeOSKit(kit)

    def addKitFromCDAction(self, kitops, cdrom):
        """ This method allows for the arbitrary installation of kits from CD media.
            Use this method to add 1) base kit, 2) all other kits (extra kits)
        """

        retVal = False
        msg = ""
        self.kitops.setDB(self._db)
        self.kitops.setKitMedia(cdrom)

        #LOGME: print ('Preparing to add a kit from media.')
        try:
            kits = self.kitops.addKitPrepare()
        except (AssertionError, CannotMountKitMediaError, UnrecognizedKitMediaError):
            msg = "Cannot Mount CD/DVD device. Couldn't mount the CD/DVD. Please wait and try again."
            return False, msg
        except Exception, ex:
            print ex

        #LOGME: print ('Getting OS distribution')

        ostype = None
        try:
            ostype = kits.ostype
        except AttributeError:
            pass

        if ostype is not None:
            kit_list = self.kitops.listKit()
            os = [kit.rname for kit in kit_list if kit.isOS]

            if os:

                return False, 'Cannot add more than one OS kit ' + \
                                             'during installation. ' + \
                                             'You can add additional OS kit using kusu-kitops later.'

        #LOGME: print 'Adding  Kit(s)'

        #if len(kits) > 0:
        #    print ("The following kits were found, and will be added:")
        #    for kit in kits:
        #        print kit[1]['name']
        #    print "\n"


        for kit in kits:
            kitname = kit[1]['name']
            try:
                print( "Adding Kit: '%s'..." % kitname)
                self.kitops.addKit(kit, api=str(kit[4]))
                retVal = True

            except KitAlreadyInstalledError:

                print ("The kit '%s' " % kitname + 'is already installed.')
                #LOGME ("The kit '%s' " % kitname + 'is already installed.')
            except AssertionError:
                print ('The inserted disk could not be identified.')
                #LOGME ('The inserted disk could not be identified.')

        # No kits found
        if not kits:
            retVal = False
            msg = 'Cannot Add Kit(s). No Kit(s) detected in media'

        self.kitops.unmountMedia()
        self.eject(cdrom)

        return retVal, msg

    def install_kits(self, kit_media):
        """Install the other kits from cd."""

        if kit_media == 'cdrom':
            import primitive.system.hardware.probe
            cdrom_dict = primitive.system.hardware.probe.getCDROM()
            cdrom_list = ['/dev/' + cd for cd in sorted(cdrom_dict.keys())]

            for cd in cdrom_list:
                self.addKitFromCDAction(self.kitops, cd)

            return True, ''
        elif kit_media == 'iso':
            kit_iso = self.prompt_for_kit()
            self.kitops.setKitMedia(kit_iso)
            kits = self.kitops.addKitPrepare()

            if kits:
                # we cannot identify the distro -- treat as ordinary kit
                kits = self.selectKits(kits)

                kitError = False
                for kit in kits:
                    try:
                        api = kit[4]
                        new_kid, updated_ngs = self.kitops.addKit(kit, api)
                        kit_str = "%s-%s-%s" % (kit[1]['name'],
                                                kit[1]['version'],
                                                kit[1]['arch'])
                    except (KitAlreadyInstalledError, InstallKitRPMError,
                            ComponentAlreadyInstalledError, AssertionError, UnsupportedKitAPIError), e:
                        msg = '%s(%s): %s' % (kit[0], kit[1]['name'], e.args[0])
                        return False, msg
                        kitError = True
                self.kitops.unmountMedia()
            else:
                msg = 'No kits found. Nothing to do.'
                print msg
                return False, msg

            if kitError:
                return False, kitError
            return True, 'Kit %s is added successfully.' % kit_str

    def prompt_for_kit(self):
        kit_iso = ""
        while not os.path.exists(kit_iso):
            kit_iso = message.input("Please provide path to ISO image or mount point: ")
            if not os.path.exists(kit_iso):
                print("The specified path or file does not exist.")

        return kit_iso

    def selectKits(self, kits):
        """
        From a list of kits found inside a metakit, select kits to install.
        """

        if len(kits) == 1:
            return kits

        if self.kit_name is not None:
            for kit in kits:
                if self.kit_name == kit[1]['name']:
                    if self.kit_ver is not None \
                        and self.kit_ver != kit[1]['version']:
                        continue
                    if self.kit_arch is not None \
                        and self.kit_arch != kit[1]['arch']:
                        continue
                    return [kit]
            return []

        choice_list = []
        # silent mode, assume all kits are added
        if self.suppress_questions:
            return kits
        while 1:
            for num_kits in enumerate(kits):
                print '[%d]: %s-%s-%s' % (num_kits[0], num_kits[1][1]['name'],
                                          num_kits[1][1]['version'],
                                          num_kits[1][1]['arch'])
            print ('Provide a comma separated list of kits ' +
                   "to install,\n'all' to install all kits " +
                   'or ENTER to quit: ')
            res = sys.stdin.readline().strip()
            res = [x.strip() for x in res.split(',')]
            if res == ['']:
                self.kitops.unmountMedia()
                sys.exit(0)

            if res == ['all']:
                return kits

            try:
                selected_kits = []
                for x in res:
                    selected_kits.append(kits[int(x)])
                return selected_kits
            except ValueError, IndexError:
                pass

    def installKitsOnBootMedia(self, kit_media):
        """Install the kits on boot media (most likely base kit only)."""

        retVal = False
        msg = ""
        if kit_media == 'cdrom':
            import primitive.system.hardware.probe
            cdrom_dict = primitive.system.hardware.probe.getCDROM()
            cdrom_list = ['/dev/' + cd for cd in sorted(cdrom_dict.keys())]

            #print 'Media device list: %s' % cdrom_list

            boot_cd = ''
            for cd in cdrom_list:
                try:
                    self.kitops.mountMedia(cd)
                    boot_kits = self.kitops.getAvailableKits()
                    self.kitops.unmountMedia()

                    for boot_kit in boot_kits:
                        if boot_kit[1]['name'] == 'base':
                            boot_cd = cd
                            break
                    if boot_cd:
                        break
                except CannotMountKitMediaError:
                    return False, "\nFailed to mount media."

            if boot_cd:
                print ('About to install base kit before showing kit screen')
                retVal, msg = self.addKitFromCDAction(self.kitops, boot_cd)

            self.installedBootMediaKits = retVal
            return retVal, msg
        elif kit_media == 'iso':
            kit_iso = self.prompt_for_kit()
            retVal, msg = self.addKitFromCDAction(self.kitops, kit_iso)
            self.installedBootMediaKits = retVal
            return retVal, msg


if __name__ == "__main__":
    osk = InstallOSKitReceiver()
    osk.installKitsOnBootMedia()

