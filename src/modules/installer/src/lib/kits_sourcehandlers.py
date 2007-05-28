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

NAV_NOTHING = -1
NAV_BACK = 1

def addKitFromCDForm(baseScreen):
    """Add kit from CD. This displays the form."""
    title = _('Insert CD or DVD')
    msg = _('Please insert a CD or DVD containing a kit, and press OK.')
    buttons = [_('OK'), _('Cancel')]
    result = baseScreen.selector.popupDialogBox(title, msg, buttons)
    if result == buttons[1].lower():
        return NAV_BACK
    addKitFromCDAction()


def addKitFromCDAction():
    """Add kit from CD. This is the action."""
    pass


def addKitFromURIForm(baseScreen):
    """Add kit from URI. This is the form."""
    pass
