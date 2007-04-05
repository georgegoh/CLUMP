#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Delete Partition Screen.
#
# Copyright 2007 Platform Computing Corporation.
#
# Licensed under GPL version 2; See LICENSE file for details.
#
__version__ = "$Revision$"

import socket
import logging
import snack
import partition
from gettext import gettext as _
from partition_new import *
from partitiontool import partitiontool
from ui.text import screenfactory, kusuwidgets
from ui.text.kusuwidgets import LEFT,CENTER,RIGHT

NAV_NOTHING = -1

def deleteDevice(baseScreen):
    """Determine the type of device and bring up the appropriate screen."""
    screen = baseScreen.screen
    diskProfile = baseScreen.disk_profile
    listbox = baseScreen.listbox
    selected_device = listbox.current()

    try:
        if selected_device in diskProfile.lv_groups.keys():
            raise partitiontool.KusuError, "Alpha can only work with primary partitions."
        elif selected_device in diskProfile.logi_vol.keys():
            raise partitiontool.KusuError, "Alpha can only work with primary partitions."
        elif selected_device in diskProfile.disk_dict.keys():
            print 'Disk'
        elif type(selected_device) is partitiontool.Partition:
            diskProfile.deletePartition(selected_device)
        else:
            raise partitiontool.KusuError, "Cannot identify selected device."

    except partitiontool.KusuError, e:
        msgbox = snack.GridForm(screen, 'Error', 1, 2)
        text = snack.TextboxReflowed(30, str(e))
        msgbox.add(text, 0, 0)
        msgbox.add(snack.Button('Ok'), 0, 1)
        msgbox.runPopup()

    return NAV_NOTHING
