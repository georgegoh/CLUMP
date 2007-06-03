#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Delete Partition Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import socket
import snack
import partition
from gettext import gettext as _
from partition_new import *
from kusu.partitiontool import partitiontool
from kusu.ui.text import screenfactory, kusuwidgets
from kusu.ui.text.kusuwidgets import LEFT,CENTER,RIGHT
from kusu.ui.text.navigator import NAV_NOTHING

def deleteDevice(baseScreen):
    """Determine the type of device and bring up the appropriate screen."""
    screen = baseScreen.screen
    diskProfile = baseScreen.disk_profile
    listbox = baseScreen.listbox

    try:
        selected_device = listbox.current()
        diskProfile.delete(selected_device)
    except partitiontool.KusuError, e:
        msgbox = snack.GridForm(screen, 'Error', 1, 2)
        text = snack.TextboxReflowed(30, str(e))
        msgbox.add(text, 0, 0)
        msgbox.add(snack.Button('Ok'), 0, 1)
        msgbox.runPopup()
    except KeyError:
        msgbox = snack.GridForm(screen, 'Error', 1, 2)
        text = snack.TextboxReflowed(30, 'Nothing to delete.')
        msgbox.add(text, 0, 0)
        msgbox.add(snack.Button('Ok'), 0, 1)
        msgbox.runPopup()
    return NAV_NOTHING
