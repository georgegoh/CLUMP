#!/usr/bin/env python
# $Id$
#
# Kusu Text Installer Delete Partition Screen.
#
# Copyright 2007 Platform Computing Inc.
#
# Licensed under GPL version 2; See LICENSE file for details.
#

import socket
import snack
import partition
from gettext import gettext as _
from partition_new import *
from kusu.util.errors import *
import kusu.partitiontool
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
    except CannotDeleteExtendedPartitionError, e:
        baseScreen.selector.popupMsg('Delete Logical Partitions First',
                                     'Cannot delete the extended partition ' + \
                                     'because it still contains logical ' + \
                                     'partitions.')
    except KusuError, e:
        baseScreen.selector.popupMsg('Error', str(e))
    except KeyError:
        baseScreen.selector.popupMsg('Error', 'Nothing to delete.')
    return NAV_NOTHING
