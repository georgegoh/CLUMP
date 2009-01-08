#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer New Partition Setup Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
from gettext import gettext as _
from kusu.util.errors import *
from kusu.ui.text.navigator import NAV_BACK
import kusu.util.log as kusulog
import os
import re

try:
    import subprocess
except:
    from popen5 import subprocess


kl = kusulog.getKusuLog('installer.kits')

def eject(path):
    """Eject a CD/DVD drive. Give me a path string."""
    p = subprocess.Popen('eject %s' % path,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    return p.communicate()
 
def closeTray(path):
    """Close a CD/DVD drive. Give me a path string."""
    p = subprocess.Popen('eject -t %s' % path,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    return p.communicate()
 
def addKitFromCDForm(baseScreen, kitops):
    """Add kit from CD. This displays the form."""
    import primitive.system.hardware.probe
    cdrom_dict = primitive.system.hardware.probe.getCDROM()
    cdrom_list = sorted(cdrom_dict.keys())
    cdrom_tulist = []

    if not cdrom_list:
        msg = _('No CD-ROM drives were found, cannot add any kits.')
        baseScreen.selector.popupMsg(_('No CD-ROM drives found'), msg)
        return NAV_BACK
    for key in cdrom_list:
        device_dict = cdrom_dict[key]
        vendor = device_dict['vendor']
        model = device_dict['model']
        if not vendor: vendor = ''
        else: vendor += ' '
        if not model: model = 'Unspecified Model'
        display_name = key + ' - ' + vendor + model
        cdrom_tulist.append((display_name , key))
    if len(cdrom_list) > 1:
        selected = baseScreen.selector.popupListBox('Select a CD/DVD Drive',
                        'Choose the drive which you wish to install kits from:',
                        cdrom_tulist)
        kl.debug('Selected CDROM: %s' % str(selected))
        choice = selected[1]
    else:
        choice = cdrom_list[0]
    cdrom = '/dev/' + choice

    out, err = eject(cdrom)
    if err:
        baseScreen.selector.popupMsg('CD/DVD Drive Eject Error', err)
        return NAV_BACK
    title = _('Insert CD or DVD')
    msg = _('Please insert a CD or DVD containing a kit, and press OK.')
    buttons = [_('OK'), _('Cancel')]
    result = baseScreen.selector.popupDialogBox(title, msg, buttons)
    if result == buttons[1].lower():
        return NAV_BACK
    closeTray(cdrom)
    addKitFromCDAction(baseScreen, kitops, cdrom)
    kl.debug('Kit added from CD')

def addKitFromCDAction(baseScreen, kitops, cdrom):
    """Add kit from CD. This is the action."""

    kitops.setDB(baseScreen.kiprofile.getDatabase())
    kitops.setKitMedia(cdrom)

    kl.debug('Add Kit Prepare')
    try:
        kits = kitops.addKitPrepare()
    except (AssertionError, CannotMountKitMediaError,
            UnrecognizedKitMediaError):
        baseScreen.selector.popupMsg('Cannot Mount CD/DVD device',
                                "Couldn't mount the CD/DVD. Please wait and try again.")
        return

    kl.debug('Get OS Dist')

    ostype = None
    try:
        ostype = kits.ostype
    except AttributeError:
        pass

    if ostype is not None:
        kit_list = kitops.listKit()
        os = [kit.rname for kit in kit_list if kit.isOS]

        if os:
            
            baseScreen.selector.popupMsg('Cannot Add Additional OS Kit', 'Cannot add more than one OS kit ' + \
                                         'during installation. ' + \
                                         'You can add additional OS kit using kitops later.')
            
            return

        kl.debug('Add OS Kit')
        kl.debug('Check that OS is the right distro, arch, version')
        verified, err_list = verifyDistroVersionAndArch(baseScreen.kiprofile, kits)
        if not verified:
            baseScreen.selector.popupMsg('Cannot Add OS Kit', 'Cannot add OS kit ' + \
                                         'because the media does not match the ' + \
                                         'following criteria:\n\t' + '\n\t'.join(err_list))
            return

        try:
            addOSKit(baseScreen, kitops, kits, cdrom)
            kl.debug('Added OS kit.')
        except KitAlreadyInstalledError, e:
            baseScreen.selector.popupMsg('Kit already installed', str(e))
    else:
        kl.debug('Add regular Kit(s)')
        for kit in kits:
            kitname = kit[1]['name']
            try:
                prog_dlg = baseScreen.selector.popupProgress('Adding kit', "Adding a Kit: '%s'..." % kitname)
                kitops.addKit(kit)
                prog_dlg.close()
            except KitAlreadyInstalledError:
                prog_dlg.close()
                baseScreen.selector.popupMsg('Kit Is Already Installed',
                                             "The kit '%s' " % kitname + \
                                             'is already installed.')
            except AssertionError:
                prog_dlg.close()
                baseScreen.selector.popupMsg('Cannot Identify Disk',
                                             'The inserted disk cannot be identified.')

        # No kits found
        if not kits:
            baseScreen.selector.popupMsg('Cannot Add Kit(s)', 'No Kit(s) detected in media')
    
        kitops.unmountMedia()


def verifyDistroVersionAndArch(kiprofile, distro):
    """
    Verify that a distro matches the version and architecture defined in
    the given kiprofile object.
    """
    verified = True
    err_list = []
    ostype = re.compile('[a-z]+').findall(distro.ostype)[0]    

    if kiprofile['OS'] in ['rhel', 'centos']:
        if ostype in ['rhel', 'centos']:
            pass
        else:
            err_list.append('OS:%s Media OS:%s' % (kiprofile['OS'].ljust(10),
                                                   ostype or 'Unknown'))
            verified = False

    elif kiprofile['OS'] != ostype: # ostype != os kit when os kit provided is not rhel/centos
        err_list.append('OS:%s Media OS:%s' % (kiprofile['OS'].ljust(10),
                                               ostype or 'Unknown'))
        verified = False
    
    distro_ver = distro.getVersion() or 'Unknown'
    if ostype in ['rhel', 'centos'] and distro_ver != 'Unknown':
        distro_ver = distro_ver.split('.')[0]
    if kiprofile['OS_VERSION'] != distro_ver:
        err_list.append('Version:%s Media Version:%s' % (kiprofile['OS_VERSION'].ljust(5),
                                                         distro_ver))
        verified = False

    if kiprofile['OS_ARCH'] != distro.getArch():
        # FIXME: not sure if this check belongs here. See FedoraInstallSrc
        # in distro.py:343.
        if distro.getArch() != 'noarch':
            err_list.append('Arch:%s\tMedia Arch:%s' % (kiprofile['OS_ARCH'],
                                                       distro.getArch() or 'Unknown'))
            verified = False
    return verified, err_list


def addOSKit(baseScreen, kitops, osdistro, cdrom):
    try:
        kit = kitops.prepareOSKit(osdistro)
    except (IOError,FileAlreadyExists,CopyError), e :
        baseScreen.selector.popupMsg('Error reading OS disk', 'Please ensure that the ' + \
                                     'OS disk is not corrupted or that' + \
                                     'the CD/DVD drive is not faulty.')
        eject(cdrom)
        return        
    except UnrecognizedKitMediaError, e:
        baseScreen.selector.popupMsg('Media Error', e.args[0])
        eject(cdrom)
        return
        
    kit_name = re.compile('[a-z]+').findall(kit['name'])[0]
    if kit_name in ['rhel', 'centos'] and baseScreen.kiprofile['OS'] in  ['rhel', 'centos']:
        kit_name = baseScreen.kiprofile['OS']

    if kit_name != baseScreen.kiprofile['OS'] or \
       kit['ver'] != baseScreen.kiprofile['OS_VERSION'] or \
       kit['arch'] != baseScreen.kiprofile['OS_ARCH']:
        out, err = eject(cdrom)
        baseScreen.selector.popupMsg('Wrong OS disk', 'Inserted OS disk does ' \
                                     'not match selected operating system: %s.' \
                                     ' Please insert the correct disc.' % \
                                     baseScreen.kiprofile['OS'])
        return

    baseScreen.kiprofile[baseScreen.profile]['initrd'] = kit['initrd']
    baseScreen.kiprofile[baseScreen.profile]['kernel'] = kit['kernel']
    baseScreen.kiprofile[baseScreen.profile]['longname'] = kit['longname']

    prog_dlg = baseScreen.selector.popupProgress('Copying Kit', 'Copying OS kit (%s)' % kit['name'])
    kitops.copyOSKitMedia(kit)
    prog_dlg.close()

    kitdir = kitops.kits_dir / kit['name'] / kit['ver'] / kit['arch']

    if sum([f.size for f in kitdir.walkfiles()]) <= 700000000: # cd provided
        while baseScreen.selector.popupYesNo('Any More Disks?',
                             'Any more disks for this OS kit?'):
            # unmount and eject.
            out, err = eject(cdrom)
            if err:
                baseScreen.selector.popupMsg('CD/DVD Drive Eject Error', err)
            baseScreen.selector.popupMsg('Insert Next Disk', 'Please insert the next disk.')
            closeTray(cdrom)
            prog_dlg = baseScreen.selector.popupProgress('Copying Kit', 'Copying OS kit (%s)' % kit['name'])

            kitops.setKitMedia(cdrom)
            kitops.addKitPrepare()
            d = kitops.getOSDist()

            kit_name = re.compile('[a-z]+').findall(d.ostype)[0]
            if kit_name in ['rhel', 'centos'] and baseScreen.kiprofile['OS'] in  ['rhel', 'centos']:
                kit_name = baseScreen.kiprofile['OS']

            if not d.ostype or not d.getVersion() or not d.getArch() or \
               kit_name != baseScreen.kiprofile['OS'] or \
               d.getVersion() != baseScreen.kiprofile['OS_VERSION'] or \
               d.getArch() != baseScreen.kiprofile['OS_ARCH']:
                prog_dlg.close()
                baseScreen.selector.popupMsg('Wrong OS Disk', 'Disk does not ' + \
                                             'match selected OS.')
                continue
            kitops.copyOSKitMedia(kit)
            prog_dlg.close()

    kitops.makeContribDir(kit)
    kitops.finalizeOSKit(kit)

def addKitFromURIForm(baseScreen):
    """Add kit from URI. This is the form."""
    pass
