#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer New Partition Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
from gettext import gettext as _
from kusu.util.errors import *
from kusu.ui.text.navigator import NAV_BACK
import kusu.util.log as kusulog
import os
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
 

def addKitFromCDForm(baseScreen, kitops):
    """Add kit from CD. This displays the form."""
    import kusu.hardware.probe
    cdrom_dict = kusu.hardware.probe.getCDROM()
    cdrom_list = sorted(cdrom_dict.keys())
    cdrom_tulist = []
    for key in cdrom_list:
        device_dict = cdrom_dict[key]
        vendor = device_dict['vendor']
        model = device_dict['model']
        if not vendor: vendor = ''
        else: vendor + ' '
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
    addKitFromCDAction(baseScreen, kitops, cdrom)


def addKitFromCDAction(baseScreen, kitops, cdrom):
    """Add kit from CD. This is the action."""
    # Mount cd
    kl.debug('CD PATH: %s' % cdrom)
    mountSuccess = False
    from kusu.kitops.kitops import EMOUNTFAIL
    while not mountSuccess:
        try:
            kitops.mountMedia(cdrom)
            mountSuccess = True
        except EMOUNTFAIL:
            baseScreen.selector.popupMsg('CD/DVD Mount Failure',
                                'Could not load the CD or DVD. Please ' + \
                                'check that you have inserted the disc ' + \
                                'correctly into the drive %s.' % cdrom)
    kitops.setKitMedia(kitops.mountpoint)
    kitops.setDB(baseScreen.kiprofile.getDatabase())

    kl.debug('Add Kit Prepare')
    try:
        kitops.addKitPrepare()
    except AssertionError:
        raise CannotAddKitError, 'Cannot mount the CDROM device.'

    kl.debug('Get OS Dist')
    media_distro = kitops.getOSDist()
    if media_distro.ostype:
        kl.debug('Add OS Kit')
        kit_add_failed = addOSKit(baseScreen, kitops, media_distro)
    else:
        kl.debug('Add regular Kit')
        try:
            prog_dlg = baseScreen.selector.popupProgress('Adding kit', 'Adding a Kit...')
            kit_add_failed = kitops.addKit()
            prog_dlg.close()
        except KitAlreadyInstalledError:
            prog_dlg.close()
            baseScreen.selector.popupMsg('Kit Is Already Installed',
                                        'The kit you have chosen is already installed')
            kit_add_failed = False

    if kit_add_failed: raise CannotAddKitError, 'Add kit Failed'
    # handle this error intelligently


def addOSKit(baseScreen, kitops, osdistro):
    kit = kitops.prepareOSKit(osdistro)

    baseScreen.kiprofile[baseScreen.profile]['initrd'] = kit['initrd']
    baseScreen.kiprofile[baseScreen.profile]['kernel'] = kit['kernel']
    baseScreen.kiprofile[baseScreen.profile]['longname'] = kit['longname']

    prog_dlg = baseScreen.selector.popupProgress('Copying Kit', 'Copying OS kit (%s)' % kit['name'])
    kitops.copyOSKitMedia(kit)
    prog_dlg.close()

    while baseScreen.selector.popupYesNo('Any More Disks?',
                         'Any more disks for this OS kit?'):
        # unmount and eject.
        kitops.unmountMedia()
        out, err = eject(cdrom)
        if err:
            baseScreen.selector.popupMsg('CD/DVD Drive Eject Error', err)
        baseScreen.selector.popupMsg('Insert Next Disk', 'Please insert the next disk.')
        prog_dlg = baseScreen.selector.popupProgress('Copying Kit', 'Copying OS kit (%s)' % kit['name'])
        kitops.copyOSKitMedia(kit)
        prog_dlg.close()
        subprocess.call('eject -t %s' % kitops.mountpoint, shell=True)

    return kitops.finalizeOSKit(kit)

def addKitFromURIForm(baseScreen):
    """Add kit from URI. This is the form."""
    pass
