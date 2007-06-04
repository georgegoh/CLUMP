#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer New Partition Setup Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
import snack
from gettext import gettext as _
from kusu.ui.text import kusuwidgets
from kusu.util.errors import *
import kits_sourcehandlers
from kusu.ui.text.navigator import NAV_NOTHING, NAV_BACK
from kusu.kitops.kitops import KitOps

kitsource_handler_dict = { 'CDROM': kits_sourcehandlers.addKitFromCDForm,
                           'URI': kits_sourcehandlers.addKitFromURIForm }

def kitAdd(baseScreen):
    """Let the user add kits."""
    kitops = KitOps(installer=True)
    try:
        source = askForKitSource(baseScreen)
        addKitFunc = kitsource_handler_dict[source]
        addKitFunc(baseScreen, kitops)
    except CannotAddKitError, e:
        baseScreen.selector.popupMsg('Error Adding Kit', str(e))
    return NAV_NOTHING


def askForKitSource(baseScreen):
    """Ask user where the kits are located."""
    sources = sorted(kitsource_handler_dict.keys())
    # return CDROM for now.
    return sources[0]


def promptForMore(baseScreen):
    """After adding a kit, prompt for more."""
    title = _('Any More Kits?')
    msg = _('Do you have any more kits to add?')
    buttons = [_('Yes'), _('No')]
    result = baseScreen.selector.popupDialogBox(title, msg, buttons)
    if result == buttons[0].lower(): return True
    else: return False
