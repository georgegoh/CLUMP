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

def addKitFromCDForm(baseScreen, kitops):
    """Add kit from CD. This displays the form."""
    title = _('Insert CD or DVD')
    msg = _('Please insert a CD or DVD containing a kit, and press OK.')
    buttons = [_('OK'), _('Cancel')]
    result = baseScreen.selector.popupDialogBox(title, msg, buttons)
    if result == buttons[1].lower():
        return NAV_BACK
    addKitFromCDAction(baseScreen, kitops)


def addKitFromCDAction(baseScreen, kitops):
    """Add kit from CD. This is the action."""
    # NEED TO CHANGE THIS TO DETECT AND MOUNT MORE INTELLIGENTLY
    # Detected CD
    # Mount cd
    kitops.mountMedia('/dev/sr0')

    kl.warning('HARDCODED CD PATH')

    # NEED TO CHANGE THIS TO DETECT AND MOUNT MORE INTELLIGENTLY

    if kitops.addKitPrepare() != 0:
        kl.debug('Failed kit prepare')
        raise CannotAddKitError, 'Failed Kit Prepare'

    media_distro = kitops.getOSDist()
    if media_distro.ostype:
        kit_add_failed = addOSKit(baseScreen, kitops, media_distro)
    else:
        kit_add_failed = kitops.addKit()

    if kit_add_failed: raise CannotAddKitError, 'Add kit Failed'
    # handle this error intelligently

    # Unmount cd
    kitops.unmountMedia()


def addOSKit(baseScreen, kitops, osdistro):
    rv, kit, osdistro = kitops.prepareOSKit(osdistro)

    if rv:  # we have a non-zero return code
        return rv

    res = ''
    while 1:    #loop to go through all the media disks...
        rv = kitops.copyOSKitMedia(kit, osdistro, res)
        if rv:
            return rv

        while baseScreen.selector.popupYesNo('Any More Disks?',
                             'Any more disks for this OS kit?'):
            # unmount and eject.
            kitops.unmountMedia()
            subprocess.call('eject %s' % kitops.mountpoint, shell=True)
            baseScreen.selector.popupMsg('Please insert the next disk')
            subprocess.call('eject -t %s' % kitops.mountpoint, shell=True)

    return kitops.finalizeOSKit(kit)

def addKitFromURIForm(baseScreen):
    """Add kit from URI. This is the form."""
    pass
